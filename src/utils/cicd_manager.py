"""
CI/CD 平台管理器
支持 GitHub 和 Gitee 双平台切换
"""
import os
import logging
from enum import Enum
from typing import Dict, Optional, Any, Literal
from dataclasses import dataclass

import yaml


class CICDPlatform(Enum):
    """CI/CD 平台类型"""
    GITHUB = "github"
    GITEE = "gitee"


@dataclass
class CICDConfig:
    """CI/CD 配置数据类"""
    platform: CICDPlatform
    token: str
    owner: str
    repo: str
    enabled: bool = True
    auto_trigger: bool = True
    branch: str = "evolution"
    create_pr: bool = True
    auto_merge: bool = False
    security_block_on_failure: bool = True
    security_enable_scan: bool = True
    
    # 平台特定配置
    docker_registry: str = ""
    docker_image_name: str = ""
    test_server_host: str = ""
    test_server_user: str = ""


class CICDManager:
    """
    CI/CD 平台管理器
    支持通过环境变量切换 GitHub 和 Gitee
    
    使用方法:
        # 通过环境变量设置平台
        export CICD_PLATFORM=gitee  # 或 github
        
        # 初始化管理器
        manager = CICDManager()
        
        # 获取当前配置
        config = manager.get_config()
        
        # 触发 CI/CD
        manager.trigger_cicd(branch="feature-branch")
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 CI/CD 管理器
        
        Args:
            config_path: 配置文件路径，默认从环境变量检测
        """
        self.logger = logging.getLogger(__name__)
        
        # 检测当前平台
        self.platform = self._detect_platform()
        self.logger.info(f"CI/CD 平台: {self.platform.value}")
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化平台特定的客户端
        self._client = None
        self._init_client()
    
    def _detect_platform(self) -> CICDPlatform:
        """
        检测 CI/CD 平台
        优先级: 环境变量 > 配置文件 > 默认值(GitHub)
        """
        platform_str = os.getenv("CICD_PLATFORM", "").lower()
        
        if platform_str == "gitee":
            return CICDPlatform.GITEE
        elif platform_str == "github":
            return CICDPlatform.GITHUB
        else:
            # 检测配置文件存在性
            if os.path.exists("config/gitee_cicd.yaml") and os.path.exists(".gitee-ci.yml"):
                # 检查是否有 Gitee 环境变量
                if os.getenv("GITEE_TOKEN"):
                    return CICDPlatform.GITEE
            
            # 默认使用 GitHub
            return CICDPlatform.GITHUB
    
    def _load_config(self, config_path: Optional[str] = None) -> CICDConfig:
        """加载 CI/CD 配置"""
        # 确定配置文件路径
        if config_path is None:
            if self.platform == CICDPlatform.GITEE:
                config_path = "config/gitee_cicd.yaml"
            else:
                config_path = "config/github_cicd.yaml"
        
        # 加载 YAML 配置
        file_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
        
        # 获取平台特定的配置节
        platform_key = self.platform.value
        platform_config = file_config.get(platform_key, {})
        evolution_config = file_config.get('self_evolution', {})
        cicd_config = evolution_config.get('cicd', {})
        security_config = cicd_config.get('security', {})
        
        # 构建配置对象（环境变量优先级高于配置文件）
        config = CICDConfig(
            platform=self.platform,
            token=self._get_config_value(
                f"{platform_key.upper()}_TOKEN",
                platform_config.get('token')
            ),
            owner=self._get_config_value(
                f"{platform_key.upper()}_OWNER",
                platform_config.get('owner')
            ),
            repo=self._get_config_value(
                f"{platform_key.upper()}_REPO",
                platform_config.get('repo')
            ),
            enabled=self._get_config_bool(
                "EVOLUTION_CICD_ENABLED",
                cicd_config.get('enabled', True)
            ),
            auto_trigger=self._get_config_bool(
                "EVOLUTION_CICD_AUTO_TRIGGER",
                cicd_config.get('auto_trigger', True)
            ),
            branch=self._get_config_value(
                "EVOLUTION_CICD_BRANCH",
                cicd_config.get('branch', 'evolution')
            ),
            create_pr=self._get_config_bool(
                "EVOLUTION_CICD_CREATE_PR",
                cicd_config.get('create_pr', True)
            ),
            auto_merge=self._get_config_bool(
                "EVOLUTION_CICD_AUTO_MERGE",
                cicd_config.get('auto_merge', False)
            ),
            security_block_on_failure=self._get_config_bool(
                "GITHUB_SECURITY_BLOCK_ON_FAILURE",
                security_config.get('block_on_failure', True)
            ),
            security_enable_scan=self._get_config_bool(
                "EVOLUTION_CICD_SECURITY_ENABLE_SCAN",
                security_config.get('enable_security_scan', True)
            ),
            docker_registry=os.getenv("DOCKER_REGISTRY", ""),
            docker_image_name=os.getenv("DOCKER_IMAGE_NAME", ""),
            test_server_host=os.getenv("TEST_SERVER_HOST", ""),
            test_server_user=os.getenv("TEST_SERVER_USER", "")
        )
        
        return config
    
    def _get_config_value(self, env_var: str, file_value: Any) -> str:
        """获取配置值，环境变量优先级高于配置文件"""
        env_value = os.getenv(env_var)
        if env_value:
            return env_value
        if file_value and file_value != "null":
            return str(file_value)
        return ""
    
    def _get_config_bool(self, env_var: str, file_value: Any) -> bool:
        """获取布尔配置值"""
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        if file_value is not None:
            return bool(file_value)
        return True
    
    def _init_client(self):
        """初始化平台特定的客户端"""
        if not self.config.token:
            self.logger.warning(f"未配置 {self.platform.value} Token，CI/CD 功能受限")
            return
        
        try:
            if self.platform == CICDPlatform.GITHUB:
                self._client = self._init_github_client()
            elif self.platform == CICDPlatform.GITEE:
                self._client = self._init_gitee_client()
        except Exception as e:
            self.logger.error(f"初始化 {self.platform.value} 客户端失败: {e}")
    
    def _init_github_client(self):
        """初始化 GitHub 客户端"""
        try:
            from github import Github
            return Github(self.config.token)
        except ImportError:
            self.logger.warning("未安装 PyGithub，使用 API 方式")
            return None
    
    def _init_gitee_client(self):
        """初始化 Gitee 客户端"""
        # Gitee 使用 REST API，不需要专门的库
        return None
    
    def get_config(self) -> CICDConfig:
        """获取当前 CI/CD 配置"""
        return self.config
    
    def get_platform(self) -> CICDPlatform:
        """获取当前平台类型"""
        return self.platform
    
    def is_enabled(self) -> bool:
        """检查 CI/CD 是否启用"""
        return self.config.enabled and bool(self.config.token)
    
    def trigger_cicd(self, branch: str = None, workflow: str = None) -> bool:
        """
        触发 CI/CD 流水线
        
        Args:
            branch: 触发的分支，默认使用配置中的分支
            workflow: 工作流/流水线名称
            
        Returns:
            是否成功触发
        """
        if not self.is_enabled():
            self.logger.warning("CI/CD 未启用或未配置 Token")
            return False
        
        branch = branch or self.config.branch
        
        try:
            if self.platform == CICDPlatform.GITHUB:
                return self._trigger_github_cicd(branch, workflow)
            elif self.platform == CICDPlatform.GITEE:
                return self._trigger_gitee_cicd(branch, workflow)
        except Exception as e:
            self.logger.error(f"触发 CI/CD 失败: {e}")
            return False
    
    def _trigger_github_cicd(self, branch: str, workflow: str = None) -> bool:
        """触发 GitHub Actions"""
        import requests
        
        workflow = workflow or "ci-cd-pipeline.yml"
        url = f"https://api.github.com/repos/{self.config.owner}/{self.config.repo}/actions/workflows/{workflow}/dispatches"
        
        headers = {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {"ref": branch}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            self.logger.info(f"✅ GitHub Actions 触发成功: {branch}")
            return True
        else:
            self.logger.error(f"GitHub Actions 触发失败: {response.status_code} - {response.text}")
            return False
    
    def _trigger_gitee_cicd(self, branch: str, pipeline: str = None) -> bool:
        """触发 Gitee CI/CD"""
        import requests
        
        pipeline = pipeline or "default"
        url = f"https://gitee.com/api/v5/repos/{self.config.owner}/{self.config.repo}/pipelines/{pipeline}/builds"
        
        headers = {
            "Authorization": f"token {self.config.token}",
            "Content-Type": "application/json"
        }
        
        data = {"branch": branch}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in (200, 201):
            self.logger.info(f"✅ Gitee CI/CD 触发成功: {branch}")
            return True
        else:
            self.logger.error(f"Gitee CI/CD 触发失败: {response.status_code} - {response.text}")
            return False
    
    def get_cicd_status(self, run_id: str = None) -> Dict[str, Any]:
        """
        获取 CI/CD 状态
        
        Args:
            run_id: 运行 ID，不提供则获取最新状态
            
        Returns:
            状态信息字典
        """
        if not self.is_enabled():
            return {"error": "CI/CD 未启用"}
        
        try:
            if self.platform == CICDPlatform.GITHUB:
                return self._get_github_status(run_id)
            elif self.platform == CICDPlatform.GITEE:
                return self._get_gitee_status(run_id)
        except Exception as e:
            self.logger.error(f"获取 CI/CD 状态失败: {e}")
            return {"error": str(e)}
    
    def _get_github_status(self, run_id: str = None) -> Dict[str, Any]:
        """获取 GitHub Actions 状态"""
        import requests
        
        if run_id:
            url = f"https://api.github.com/repos/{self.config.owner}/{self.config.repo}/actions/runs/{run_id}"
        else:
            url = f"https://api.github.com/repos/{self.config.owner}/{self.config.repo}/actions/runs?per_page=1"
        
        headers = {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if run_id:
                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "conclusion": data.get("conclusion"),
                    "branch": data.get("head_branch"),
                    "created_at": data.get("created_at"),
                    "url": data.get("html_url")
                }
            else:
                runs = data.get("workflow_runs", [])
                if runs:
                    run = runs[0]
                    return {
                        "id": run.get("id"),
                        "status": run.get("status"),
                        "conclusion": run.get("conclusion"),
                        "branch": run.get("head_branch"),
                        "created_at": run.get("created_at"),
                        "url": run.get("html_url")
                    }
                return {"error": "未找到运行记录"}
        else:
            return {"error": f"API 错误: {response.status_code}"}
    
    def _get_gitee_status(self, build_id: str = None) -> Dict[str, Any]:
        """获取 Gitee CI/CD 状态"""
        import requests
        
        if build_id:
            url = f"https://gitee.com/api/v5/repos/{self.config.owner}/{self.config.repo}/pipelines/default/builds/{build_id}"
        else:
            url = f"https://gitee.com/api/v5/repos/{self.config.owner}/{self.config.repo}/pipelines/default/builds?per_page=1"
        
        headers = {
            "Authorization": f"token {self.config.token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if build_id:
                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "branch": data.get("branch"),
                    "created_at": data.get("created_at"),
                    "duration": data.get("duration"),
                    "url": data.get("web_url")
                }
            else:
                builds = data if isinstance(data, list) else [data]
                if builds:
                    build = builds[0]
                    return {
                        "id": build.get("id"),
                        "status": build.get("status"),
                        "branch": build.get("branch"),
                        "created_at": build.get("created_at"),
                        "duration": build.get("duration"),
                        "url": build.get("web_url")
                    }
                return {"error": "未找到构建记录"}
        else:
            return {"error": f"API 错误: {response.status_code}"}


# 便捷函数
def get_cicd_manager(config_path: Optional[str] = None) -> CICDManager:
    """
    获取 CI/CD 管理器实例
    
    使用方法:
        manager = get_cicd_manager()
        if manager.is_enabled():
            manager.trigger_cicd(branch="dev")
    """
    return CICDManager(config_path)


def switch_cicd_platform(platform: Literal["github", "gitee"]):
    """
    切换 CI/CD 平台
    
    注意: 这只会修改当前进程的环境变量，
    要永久切换需要修改 .env 文件
    
    Args:
        platform: 目标平台 ("github" 或 "gitee")
    """
    os.environ["CICD_PLATFORM"] = platform
    logging.info(f"CI/CD 平台已切换为: {platform}")
    return get_cicd_manager()


# 命令行接口
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("用法: python -m src.utils.cicd_manager <命令> [参数]")
        print("\n命令:")
        print("  status              查看当前 CI/CD 配置状态")
        print("  trigger [branch]    触发 CI/CD 流水线")
        print("  switch <platform>   切换平台 (github/gitee)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        manager = get_cicd_manager()
        config = manager.get_config()
        print(f"\n当前平台: {config.platform.value}")
        print(f"启用状态: {'✅ 已启用' if manager.is_enabled() else '❌ 未启用'}")
        print(f"仓库: {config.owner}/{config.repo}")
        print(f"进化分支: {config.branch}")
        print(f"自动触发: {'是' if config.auto_trigger else '否'}")
        print(f"自动合并 PR: {'是' if config.auto_merge else '否'}")
        
    elif command == "trigger":
        branch = sys.argv[2] if len(sys.argv) > 2 else None
        manager = get_cicd_manager()
        success = manager.trigger_cicd(branch=branch)
        sys.exit(0 if success else 1)
        
    elif command == "switch":
        if len(sys.argv) < 3:
            print("错误: 请指定目标平台 (github/gitee)")
            sys.exit(1)
        platform = sys.argv[2]
        manager = switch_cicd_platform(platform)
        print(f"已切换到 {platform}")
        
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
