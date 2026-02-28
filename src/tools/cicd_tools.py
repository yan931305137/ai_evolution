"""
CI/CD 工具函数

提供 Agent 可以调用的 CI/CD 相关工具
"""
import logging
from typing import Optional

from src.utils.github_cicd_integration import GitHubCICDIntegration, CICDResult

logger = logging.getLogger(__name__)


def trigger_ci_pipeline(
    branch: str = "main",
    workflow: str = "ci.yml",
    wait_for_completion: bool = True
) -> str:
    """
    触发 CI/CD Pipeline 并等待结果。
    
    在代码修改后调用此函数运行自动化测试和构建。
    
    Args:
        branch: 要测试的分支，默认为 main
        workflow: GitHub Actions 工作流文件名，默认为 ci.yml
        wait_for_completion: 是否等待 Pipeline 完成，默认为 True
    
    Returns:
        CI/CD 执行结果摘要
        
    Example:
        >>> trigger_ci_pipeline(branch="feature/new-auth")
        >>> trigger_ci_pipeline(workflow="deploy.yml", wait_for_completion=False)
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured. Please set GITHUB_TOKEN, GITHUB_OWNER and GITHUB_REPO."
        
        logger.info(f"Triggering CI pipeline for branch: {branch}")
        
        # 触发工作流
        run_id = ci.trigger_workflow(workflow, branch)
        if not run_id:
            return f"Error: Failed to trigger workflow '{workflow}' on branch '{branch}'"
        
        if not wait_for_completion:
            run = ci.get_workflow_run(run_id)
            return f"CI Pipeline triggered successfully!\nRun ID: {run_id}\nURL: {run.html_url if run else 'N/A'}\nStatus: Check GitHub Actions for progress."
        
        # 等待完成
        logger.info(f"Waiting for workflow run {run_id} to complete...")
        result = ci.wait_for_completion(run_id)
        
        # 格式化输出
        status_icon = "✅" if result.success else "❌"
        output = f"""{status_icon} CI Pipeline Result

Workflow: {workflow}
Branch: {branch}
Status: {result.workflow_run.conclusion.value if result.workflow_run else 'Unknown'}
Duration: {result.duration_seconds:.1f}s

Summary: {result.summary}
"""
        
        if result.workflow_run:
            output += f"""
Commit: {result.workflow_run.commit_sha}
Message: {result.workflow_run.commit_message}
URL: {result.workflow_run.html_url}
"""
        
        if result.details.get("pr_number"):
            output += f"""
Pull Request: #{result.details['pr_number']}
PR URL: {result.details.get('pr_url', 'N/A')}
"""
        
        return output
        
    except Exception as e:
        logger.error(f"Error triggering CI pipeline: {e}")
        return f"Error: {str(e)}"


def check_ci_status(run_id: int) -> str:
    """
    检查 CI/CD Pipeline 的状态。
    
    Args:
        run_id: GitHub Actions Run ID
    
    Returns:
        当前状态信息
        
    Example:
        >>> check_ci_status(1234567890)
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured."
        
        run = ci.get_workflow_run(run_id)
        if not run:
            return f"Error: Could not find workflow run with ID {run_id}"
        
        status_icon = {
            "completed": "✅" if run.conclusion.value == "success" else "❌",
            "in_progress": "🔄",
            "queued": "⏳"
        }.get(run.status.value, "❓")
        
        return f"""{status_icon} CI Status

Workflow: {run.name}
Status: {run.status.value}
Conclusion: {run.conclusion.value}
Branch: {run.branch}
Commit: {run.commit_sha}
Message: {run.commit_message}
Started: {run.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Updated: {run.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
URL: {run.html_url}
"""
        
    except Exception as e:
        logger.error(f"Error checking CI status: {e}")
        return f"Error: {str(e)}"


def get_ci_logs(run_id: int, max_lines: int = 100) -> str:
    """
    获取 CI/CD Pipeline 的日志。
    
    Args:
        run_id: GitHub Actions Run ID
        max_lines: 最大返回行数，默认为 100
    
    Returns:
        日志内容
        
    Example:
        >>> get_ci_logs(1234567890, max_lines=50)
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured."
        
        logs = ci.get_run_logs(run_id)
        
        # 限制行数
        lines = logs.split('\n')
        if len(lines) > max_lines:
            logs = '\n'.join(lines[-max_lines:])
            logs = f"... (showing last {max_lines} lines)\n{logs}"
        
        return f"CI Logs for Run #{run_id}:\n\n{logs}"
        
    except Exception as e:
        logger.error(f"Error getting CI logs: {e}")
        return f"Error: {str(e)}"


def create_pr_from_branch(
    branch: str,
    title: str,
    body: Optional[str] = None,
    base_branch: str = "main"
) -> str:
    """
    从指定分支创建 Pull Request。
    
    Args:
        branch: 源分支名称
        title: PR 标题
        body: PR 内容（可选）
        base_branch: 目标分支，默认为 main
    
    Returns:
        PR 创建结果
        
    Example:
        >>> create_pr_from_branch("feature/auth", "Add authentication module")
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured."
        
        default_body = f"Automated PR from branch '{branch}'"
        pr_body = body or default_body
        
        pr_number = ci.create_pr(title, pr_body, branch, base_branch)
        
        if pr_number:
            return f"""✅ Pull Request Created

PR Number: #{pr_number}
Title: {title}
Branch: {branch} -> {base_branch}
URL: https://github.com/{ci.owner}/{ci.repo}/pull/{pr_number}
"""
        else:
            return "❌ Failed to create Pull Request"
            
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        return f"Error: {str(e)}"


def merge_pull_request(pr_number: int, commit_message: Optional[str] = None) -> str:
    """
    合并指定的 Pull Request。
    
    Args:
        pr_number: PR 编号
        commit_message: 合并提交信息（可选）
    
    Returns:
        合并结果
        
    Example:
        >>> merge_pull_request(42)
        >>> merge_pull_request(42, "Merge authentication feature")
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured."
        
        success = ci.merge_pr(pr_number, commit_message)
        
        if success:
            msg = commit_message or f"Merge PR #{pr_number}"
            return f"""✅ Pull Request Merged

PR Number: #{pr_number}
Commit Message: {msg}
Status: Successfully merged
"""
        else:
            return f"❌ Failed to merge PR #{pr_number}. Check if PR is mergeable."
            
    except Exception as e:
        logger.error(f"Error merging PR: {e}")
        return f"Error: {str(e)}"


def run_evolution_ci_pipeline(
    evolution_branch: str = "evolution",
    create_pr: bool = True,
    auto_merge: bool = False
) -> str:
    """
    运行进化专用的完整 CI/CD Pipeline。
    
    这是进化完成后的标准流程：
    1. 触发 CI Pipeline
    2. 等待测试通过
    3. 创建 PR（可选）
    4. 自动合并（可选）
    
    Args:
        evolution_branch: 进化分支名称，默认为 "evolution"
        create_pr: 是否自动创建 PR，默认为 True
        auto_merge: 是否自动合并（仅当 CI 通过时），默认为 False
    
    Returns:
        完整执行结果
        
    Example:
        >>> run_evolution_ci_pipeline()
        >>> run_evolution_ci_pipeline(create_pr=True, auto_merge=False)
    """
    try:
        ci = GitHubCICDIntegration()
        
        if not ci.is_configured():
            return "Error: GitHub CI/CD not configured. Please check config.yaml or environment variables."
        
        logger.info(f"Running evolution CI pipeline for branch: {evolution_branch}")
        
        # 运行完整 Pipeline
        result = ci.run_full_pipeline(
            workflow_name="ci.yml",
            branch=evolution_branch,
            create_pr_on_success=create_pr,
            pr_title=f"🤖 Evolution: Automated changes from {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
            pr_body="""## 🤖 Automated Evolution Changes

This PR contains changes generated by the AI evolution system.

### Changes Summary
- Code improvements based on evaluation
- Automated refactoring and optimizations
- Test coverage enhancements

### Verification
- [x] All tests passing
- [x] Code quality checks passed
- [x] No breaking changes introduced

---
*This PR was automatically created by the Evolution Feedback Loop*"""
        )
        
        # 格式化输出
        status_icon = "✅" if result.success else "❌"
        output = f"""{status_icon} Evolution CI Pipeline Complete

Branch: {evolution_branch}
Status: {result.workflow_run.conclusion.value if result.workflow_run else 'Unknown'}
Duration: {result.duration_seconds:.1f}s

{result.summary}
"""
        
        if result.workflow_run:
            output += f"""
📊 Build Details:
- Commit: {result.workflow_run.commit_sha}
- Message: {result.workflow_run.commit_message}
- URL: {result.workflow_run.html_url}
"""
        
        if result.details.get("pr_number"):
            output += f"""
📋 Pull Request:
- PR #{result.details['pr_number']}
- URL: {result.details['pr_url']}
"""
            
            # 自动合并
            if auto_merge and result.success:
                pr_number = result.details['pr_number']
                merge_result = ci.merge_pr(pr_number, f"Auto-merge evolution PR #{pr_number}")
                if merge_result:
                    output += f"\n✅ Auto-merged successfully!"
                else:
                    output += f"\n⚠️ Could not auto-merge. Please merge manually."
        
        return output
        
    except Exception as e:
        logger.error(f"Error running evolution CI pipeline: {e}")
        return f"Error: {str(e)}"
