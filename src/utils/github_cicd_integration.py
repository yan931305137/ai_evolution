"""
GitHub CI/CD 集成模块

实现与 GitHub Actions 的集成，支持：
- 触发 CI/CD Pipeline
- 监听构建状态
- 获取构建日志
- 自动合并 PR
- 敏感信息安全检查
"""
import os
import time
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.config import cfg

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ConclusionStatus(Enum):
    """结论状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    passed: bool
    issues: List[str]
    sanitized_content: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues_count": len(self.issues),
            "issues": self.issues[:10] if self.issues else [],  # 最多显示10个
            "has_more_issues": len(self.issues) > 10
        }


@dataclass
class WorkflowRun:
    """工作流运行记录"""
    run_id: int
    name: str
    status: WorkflowStatus
    conclusion: ConclusionStatus
    branch: str
    commit_sha: str
    commit_message: str
    created_at: datetime
    updated_at: datetime
    html_url: str
    logs_url: Optional[str] = None
    artifacts_url: Optional[str] = None


@dataclass
class CICDResult:
    """CI/CD 执行结果"""
    success: bool
    workflow_run: Optional[WorkflowRun]
    duration_seconds: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    security_check: Optional[SecurityCheckResult] = None


class GitHubCICDIntegration:
    """
    GitHub CI/CD 集成
    
    提供与 GitHub Actions 的完整集成支持
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None
    ):
        """
        初始化 GitHub CI/CD 集成
        
        Args:
            token: GitHub Personal Access Token
            owner: 仓库所有者
            repo: 仓库名称
        """
        self.token = token or os.getenv("GITHUB_TOKEN") or cfg.get("github.token")
        self.owner = owner or cfg.get("github.owner")
        self.repo = repo or cfg.get("github.repo")
        
        if not self.token:
            logger.warning("GitHub token not configured. CI/CD integration disabled.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
        
        # 回调函数
        self.on_status_change: Optional[Callable[[WorkflowRun], None]] = None
        self.on_complete: Optional[Callable[[CICDResult], None]] = None
        
        logger.info(f"GitHub CI/CD Integration initialized for {self.owner}/{self.repo}")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.token and self.owner and self.repo)
    
    def _load_security_scanner(self):
        """延迟加载安全扫描器"""
        try:
            from src.utils.security_scanner import SecurityScanner
            return SecurityScanner()
        except ImportError:
            logger.warning("Security scanner not available")
            return None
    
    def check_content_security(
        self,
        content: str,
        content_type: str = "text"
    ) -> SecurityCheckResult:
        """
        检查内容安全性（防止敏感信息泄露）
        
        Args:
            content: 要检查的内容
            content_type: 内容类型 (text, commit_message, pr_body, etc.)
            
        Returns:
            SecurityCheckResult: 检查结果
        """
        scanner = self._load_security_scanner()
        if not scanner:
            # 安全扫描器不可用，默认通过但警告
            return SecurityCheckResult(
                passed=True,
                issues=["Security scanner not available - manual review recommended"]
            )
        
        try:
            # 检查文本中的敏感信息
            findings = scanner.scan_text(content)
            
            if not findings:
                return SecurityCheckResult(
                    passed=True,
                    issues=[]
                )
            
            # 处理发现的问题
            issues = []
            has_critical = False
            
            for finding in findings:
                issue = f"[{finding.severity.value}] {finding.pattern_name}: {finding.matched_text}"
                issues.append(issue)
                if finding.severity.value == "CRITICAL":
                    has_critical = True
            
            # 清理敏感内容
            sanitized = scanner.sanitize_for_logging(content)
            
            return SecurityCheckResult(
                passed=not has_critical,  # 有 CRITICAL 则失败
                issues=issues,
                sanitized_content=sanitized
            )
            
        except Exception as e:
            logger.error(f"Security check failed: {e}")
            return SecurityCheckResult(
                passed=False,
                issues=[f"Security check error: {str(e)}"]
            )
    
    def check_pr_security(
        self,
        title: str,
        body: str,
        branch: str
    ) -> SecurityCheckResult:
        """
        检查 PR 的安全性
        
        Args:
            title: PR 标题
            body: PR 内容
            branch: 分支名
            
        Returns:
            SecurityCheckResult: 检查结果
        """
        all_issues = []
        
        # 检查标题
        title_check = self.check_content_security(title, "pr_title")
        if title_check.issues:
            all_issues.extend([f"[Title] {issue}" for issue in title_check.issues])
        
        # 检查内容
        body_check = self.check_content_security(body, "pr_body")
        if body_check.issues:
            all_issues.extend([f"[Body] {issue}" for issue in body_check.issues])
        
        # 检查分支名（可能包含敏感信息）
        branch_check = self.check_content_security(branch, "branch_name")
        if branch_check.issues:
            all_issues.extend([f"[Branch] {issue}" for issue in branch_check.issues])
        
        has_critical = any("[CRITICAL]" in issue for issue in all_issues)
        
        return SecurityCheckResult(
            passed=not has_critical and len(all_issues) < 5,  # 少量非关键问题允许
            issues=all_issues
        )
    
    def sanitize_for_logs(self, text: str) -> str:
        """清理日志中的敏感信息"""
        scanner = self._load_security_scanner()
        if scanner:
            return scanner.sanitize_for_logging(text)
        return text
    
    def trigger_workflow(
        self,
        workflow_name: str = "ci.yml",
        branch: str = "main",
        inputs: Optional[Dict[str, str]] = None
    ) -> Optional[int]:
        """
        触发工作流
        
        Args:
            workflow_name: 工作流文件名
            branch: 目标分支
            inputs: 工作流输入参数
            
        Returns:
            run_id: 工作流运行 ID，失败返回 None
        """
        if not self.is_configured():
            logger.error("GitHub CI/CD not configured")
            return None
        
        try:
            # 获取 workflow ID
            workflow_id = self._get_workflow_id(workflow_name)
            if not workflow_id:
                logger.error(f"Workflow {workflow_name} not found")
                return None
            
            # 触发工作流
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/dispatches"
            data = {"ref": branch}
            if inputs:
                data["inputs"] = inputs
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 204:
                logger.info(f"Workflow {workflow_name} triggered on {branch}")
                
                # 等待工作流启动并获取 run_id
                time.sleep(2)
                run_id = self._get_latest_run_id(workflow_id, branch)
                return run_id
            else:
                logger.error(f"Failed to trigger workflow: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            return None
    
    def _get_workflow_id(self, workflow_name: str) -> Optional[int]:
        """获取工作流 ID"""
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/workflows"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                workflows = response.json().get("workflows", [])
                for wf in workflows:
                    if wf["path"].endswith(workflow_name):
                        return wf["id"]
            return None
        except Exception as e:
            logger.error(f"Error getting workflow ID: {e}")
            return None
    
    def _get_latest_run_id(self, workflow_id: int, branch: str) -> Optional[int]:
        """获取最新的工作流运行 ID"""
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/runs"
            params = {"branch": branch, "per_page": 1}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                runs = response.json().get("workflow_runs", [])
                if runs:
                    return runs[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error getting latest run ID: {e}")
            return None
    
    def get_workflow_run(self, run_id: int) -> Optional[WorkflowRun]:
        """
        获取工作流运行详情
        
        Args:
            run_id: 工作流运行 ID
            
        Returns:
            WorkflowRun 对象
        """
        if not self.is_configured():
            return None
        
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return WorkflowRun(
                    run_id=data["id"],
                    name=data["name"],
                    status=WorkflowStatus(data.get("status", "unknown")),
                    conclusion=ConclusionStatus(data.get("conclusion", "unknown")),
                    branch=data["head_branch"],
                    commit_sha=data["head_sha"][:8],
                    commit_message=data.get("head_commit", {}).get("message", "")[:50],
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                    html_url=data["html_url"],
                    logs_url=data.get("logs_url"),
                    artifacts_url=data.get("artifacts_url")
                )
            else:
                logger.error(f"Failed to get workflow run: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting workflow run: {e}")
            return None
    
    def wait_for_completion(
        self,
        run_id: int,
        timeout: int = 600,
        poll_interval: int = 10
    ) -> CICDResult:
        """
        等待工作流完成
        
        Args:
            run_id: 工作流运行 ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            CICDResult 对象
        """
        start_time = time.time()
        last_status = None
        
        logger.info(f"Waiting for workflow run {run_id} to complete...")
        
        while time.time() - start_time < timeout:
            run = self.get_workflow_run(run_id)
            
            if not run:
                return CICDResult(
                    success=False,
                    workflow_run=None,
                    duration_seconds=time.time() - start_time,
                    summary="Failed to get workflow status"
                )
            
            # 状态变化回调
            if last_status != run.status and self.on_status_change:
                self.on_status_change(run)
            last_status = run.status
            
            # 检查是否完成
            if run.status == WorkflowStatus.COMPLETED:
                duration = time.time() - start_time
                success = run.conclusion == ConclusionStatus.SUCCESS
                
                result = CICDResult(
                    success=success,
                    workflow_run=run,
                    duration_seconds=duration,
                    summary=f"Workflow {run.name} {run.conclusion.value}",
                    details={
                        "commit": run.commit_sha,
                        "message": run.commit_message,
                        "url": run.html_url
                    }
                )
                
                if self.on_complete:
                    self.on_complete(result)
                
                return result
            
            logger.debug(f"Workflow status: {run.status.value}, waiting...")
            time.sleep(poll_interval)
        
        # 超时
        return CICDResult(
            success=False,
            workflow_run=self.get_workflow_run(run_id),
            duration_seconds=time.time() - start_time,
            summary="Timeout waiting for workflow completion"
        )
    
    def get_run_logs(self, run_id: int) -> str:
        """
        获取工作流运行日志
        
        Args:
            run_id: 工作流运行 ID
            
        Returns:
            日志内容
        """
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/logs"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.text
            else:
                return f"Failed to get logs: {response.status_code}"
                
        except Exception as e:
            return f"Error getting logs: {e}"
    
    def create_pr(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        skip_security_check: bool = False
    ) -> Tuple[Optional[int], Optional[SecurityCheckResult]]:
        """
        创建 Pull Request（带安全检查）
        
        Args:
            title: PR 标题
            body: PR 内容
            head_branch: 源分支
            base_branch: 目标分支
            skip_security_check: 是否跳过安全检查（危险！）
            
        Returns:
            Tuple[Optional[int], Optional[SecurityCheckResult]]: (PR编号, 安全检查结果)
        """
        if not self.is_configured():
            return None, None
        
        # 安全检查
        security_result = None
        if not skip_security_check:
            security_result = self.check_pr_security(title, body, head_branch)
            
            if not security_result.passed:
                logger.error(f"❌ Security check failed for PR creation!")
                for issue in security_result.issues:
                    logger.error(f"   - {issue}")
                
                # 可以选择抛出异常或返回失败
                if cfg.get("github.security.block_on_failure", True):
                    return None, security_result
                else:
                    logger.warning("Security check failed but block_on_failure is disabled")
                    # 在 PR body 中添加安全警告
                    body = self._add_security_warning(body, security_result)
        
        # 清理日志中的敏感信息
        safe_title = self.sanitize_for_logs(title)
        logger.info(f"Creating PR: {safe_title}")
        
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/pulls"
            data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                pr_number = response.json()["number"]
                logger.info(f"✅ PR #{pr_number} created: {safe_title}")
                return pr_number, security_result
            else:
                # 清理错误信息中的敏感内容
                safe_error = self.sanitize_for_logs(response.text)
                logger.error(f"Failed to create PR: {response.status_code} - {safe_error}")
                return None, security_result
                
        except Exception as e:
            safe_error = self.sanitize_for_logs(str(e))
            logger.error(f"Error creating PR: {safe_error}")
            return None, security_result
    
    def _add_security_warning(
        self,
        body: str,
        security_result: SecurityCheckResult
    ) -> str:
        """在 PR body 中添加安全警告"""
        warning = """

## ⚠️ Security Warning

This PR has potential security concerns that were detected during automated scanning:

"""
        for issue in security_result.issues[:5]:  # 最多显示5个
            warning += f"- {issue}\n"
        
        if len(security_result.issues) > 5:
            warning += f"- ... and {len(security_result.issues) - 5} more issues\n"
        
        warning += "\nPlease review carefully before merging."
        
        return body + warning
    
    def merge_pr(
        self,
        pr_number: int,
        commit_message: Optional[str] = None,
        check_security_approval: bool = True
    ) -> bool:
        """
        合并 Pull Request（带安全检查）
        
        Args:
            pr_number: PR 编号
            commit_message: 提交信息
            check_security_approval: 是否检查安全审批
            
        Returns:
            是否成功
        """
        if not self.is_configured():
            return False
        
        # 检查提交信息安全性
        if commit_message:
            security_check = self.check_content_security(commit_message, "commit_message")
            if not security_check.passed:
                logger.error(f"❌ Commit message failed security check!")
                for issue in security_check.issues:
                    logger.error(f"   - {issue}")
                
                if cfg.get("github.security.block_on_failure", True):
                    return False
        
        try:
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/merge"
            data = {}
            if commit_message:
                # 清理提交信息
                data["commit_message"] = self.sanitize_for_logs(commit_message)
            
            response = requests.put(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"✅ PR #{pr_number} merged successfully")
                return True
            else:
                safe_error = self.sanitize_for_logs(response.text)
                logger.error(f"Failed to merge PR: {response.status_code} - {safe_error}")
                return False
                
        except Exception as e:
            safe_error = self.sanitize_for_logs(str(e))
            logger.error(f"Error merging PR: {safe_error}")
            return False
    
    def run_full_pipeline(
        self,
        workflow_name: str = "ci.yml",
        branch: str = "main",
        create_pr_on_success: bool = False,
        pr_title: Optional[str] = None,
        pr_body: Optional[str] = None
    ) -> CICDResult:
        """
        运行完整 CI/CD Pipeline
        
        Args:
            workflow_name: 工作流文件名
            branch: 目标分支
            create_pr_on_success: 成功后是否创建 PR
            pr_title: PR 标题
            pr_body: PR 内容
            
        Returns:
            CICDResult 对象
        """
        logger.info(f"Starting full CI/CD pipeline for {branch}")
        
        # 1. 触发工作流
        run_id = self.trigger_workflow(workflow_name, branch)
        if not run_id:
            return CICDResult(
                success=False,
                workflow_run=None,
                duration_seconds=0,
                summary="Failed to trigger workflow"
            )
        
        # 2. 等待完成
        result = self.wait_for_completion(run_id)
        
        # 3. 成功后创建 PR
        if result.success and create_pr_on_success:
            title = pr_title or f"Auto: Evolution changes from {datetime.now().strftime('%Y-%m-%d')}"
            body = pr_body or "This PR contains automated evolution changes.\n\nCI Status: ✅ Passed"
            
            pr_number, security_result = self.create_pr(title, body, branch)
            
            if pr_number:
                result.details["pr_number"] = pr_number
                result.details["pr_url"] = f"https://github.com/{self.owner}/{self.repo}/pull/{pr_number}"
            
            if security_result:
                result.security_check = security_result
                if not security_result.passed:
                    result.summary += " (Security issues detected)"
        
        return result


# 便捷函数
def trigger_github_ci(
    branch: str = "main",
    workflow: str = "ci.yml",
    wait: bool = True
) -> CICDResult:
    """
    触发 GitHub CI/CD 的便捷函数
    
    Args:
        branch: 目标分支
        workflow: 工作流文件名
        wait: 是否等待完成
        
    Returns:
        CICDResult
    """
    ci = GitHubCICDIntegration()
    
    if not ci.is_configured():
        return CICDResult(
            success=False,
            workflow_run=None,
            duration_seconds=0,
            summary="GitHub CI/CD not configured"
        )
    
    run_id = ci.trigger_workflow(workflow, branch)
    if not run_id:
        return CICDResult(
            success=False,
            workflow_run=None,
            duration_seconds=0,
            summary="Failed to trigger workflow"
        )
    
    if wait:
        return ci.wait_for_completion(run_id)
    else:
        run = ci.get_workflow_run(run_id)
        return CICDResult(
            success=True,
            workflow_run=run,
            duration_seconds=0,
            summary="Workflow triggered (not waiting)"
        )
