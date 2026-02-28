#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码仓库管理工具
支持 GitHub 和 Gitee 的认证、项目拉取和克隆功能
"""

import os
import logging
import subprocess
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Repository:
    """仓库信息数据类"""
    name: str
    url: str
    description: str = ""
    language: str = ""
    stars: int = 0
    forks: int = 0
    updated_at: str = ""
    is_private: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class GitHubClient:
    """GitHub API 客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 GitHub 客户端
        
        Args:
            token: GitHub Personal Access Token
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {}
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        logger.info(f"GitHub 客户端初始化完成 ({'已认证' if self.token else '未认证'})")
    
    def get_user_repos(self, username: Optional[str] = None) -> List[Repository]:
        """
        获取用户的仓库列表
        
        Args:
            username: 用户名，如果为None则获取认证用户的仓库
            
        Returns:
            仓库列表
        """
        if not username and not self.token:
            raise ValueError("未认证时必须提供用户名")
        
        if username:
            url = f"{self.base_url}/users/{username}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            repos_data = response.json()
            repos = []
            
            for repo_data in repos_data:
                repo = Repository(
                    name=repo_data.get("name", ""),
                    url=repo_data.get("clone_url", ""),
                    description=repo_data.get("description", ""),
                    language=repo_data.get("language", ""),
                    stars=repo_data.get("stargazers_count", 0),
                    forks=repo_data.get("forks_count", 0),
                    updated_at=repo_data.get("updated_at", ""),
                    is_private=repo_data.get("private", False),
                    metadata={
                        "full_name": repo_data.get("full_name", ""),
                        "html_url": repo_data.get("html_url", ""),
                        "size": repo_data.get("size", 0),
                        "open_issues": repo_data.get("open_issues_count", 0),
                    }
                )
                repos.append(repo)
            
            logger.info(f"获取到 {len(repos)} 个 GitHub 仓库")
            return repos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取 GitHub 仓库失败: {str(e)}")
            raise
    
    def get_repo(self, owner: str, repo_name: str) -> Repository:
        """
        获取单个仓库信息
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            仓库信息
        """
        url = f"{self.base_url}/repos/{owner}/{repo_name}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            repo_data = response.json()
            
            repo = Repository(
                name=repo_data.get("name", ""),
                url=repo_data.get("clone_url", ""),
                description=repo_data.get("description", ""),
                language=repo_data.get("language", ""),
                stars=repo_data.get("stargazers_count", 0),
                forks=repo_data.get("forks_count", 0),
                updated_at=repo_data.get("updated_at", ""),
                is_private=repo_data.get("private", False),
                metadata={
                    "full_name": repo_data.get("full_name", ""),
                    "html_url": repo_data.get("html_url", ""),
                    "size": repo_data.get("size", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "default_branch": repo_data.get("default_branch", "main"),
                }
            )
            
            logger.info(f"获取仓库信息成功: {owner}/{repo_name}")
            return repo
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取仓库信息失败: {str(e)}")
            raise


class GiteeClient:
    """Gitee API 客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 Gitee 客户端
        
        Args:
            token: Gitee Personal Access Token
        """
        self.token = token or os.getenv("GITEE_TOKEN")
        self.base_url = "https://gitee.com/api/v5"
        self.headers = {}
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        logger.info(f"Gitee 客户端初始化完成 ({'已认证' if self.token else '未认证'})")
    
    def get_user_repos(self, username: Optional[str] = None) -> List[Repository]:
        """
        获取用户的仓库列表
        
        Args:
            username: 用户名，如果为None则获取认证用户的仓库
            
        Returns:
            仓库列表
        """
        if not username and not self.token:
            raise ValueError("未认证时必须提供用户名")
        
        if username:
            url = f"{self.base_url}/users/{username}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        
        params = {
            "page": 1,
            "per_page": 100,
            "sort": "updated"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            repos_data = response.json()
            repos = []
            
            for repo_data in repos_data:
                repo = Repository(
                    name=repo_data.get("name", ""),
                    url=repo_data.get("clone_url", ""),
                    description=repo_data.get("description", ""),
                    language=repo_data.get("language", ""),
                    stars=repo_data.get("stargazers_count", 0),
                    forks=repo_data.get("forks_count", 0),
                    updated_at=repo_data.get("updated_at", ""),
                    is_private=repo_data.get("private", False),
                    metadata={
                        "full_name": repo_data.get("full_name", ""),
                        "html_url": repo_data.get("html_url", ""),
                        "size": repo_data.get("size", 0),
                        "open_issues": repo_data.get("open_issues_count", 0),
                    }
                )
                repos.append(repo)
            
            logger.info(f"获取到 {len(repos)} 个 Gitee 仓库")
            return repos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取 Gitee 仓库失败: {str(e)}")
            raise
    
    def get_repo(self, owner: str, repo_name: str) -> Repository:
        """
        获取单个仓库信息
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            仓库信息
        """
        url = f"{self.base_url}/repos/{owner}/{repo_name}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            repo_data = response.json()
            
            repo = Repository(
                name=repo_data.get("name", ""),
                url=repo_data.get("clone_url", ""),
                description=repo_data.get("description", ""),
                language=repo_data.get("language", ""),
                stars=repo_data.get("stargazers_count", 0),
                forks=repo_data.get("forks_count", 0),
                updated_at=repo_data.get("updated_at", ""),
                is_private=repo_data.get("private", False),
                metadata={
                    "full_name": repo_data.get("full_name", ""),
                    "html_url": repo_data.get("html_url", ""),
                    "size": repo_data.get("size", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "default_branch": repo_data.get("default_branch", "master"),
                }
            )
            
            logger.info(f"获取仓库信息成功: {owner}/{repo_name}")
            return repo
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取仓库信息失败: {str(e)}")
            raise


class RepositoryManager:
    """代码仓库管理器"""
    
    def __init__(self):
        """初始化仓库管理器"""
        self.github_client = None
        self.gitee_client = None
        
        # 检查环境变量
        github_token = os.getenv("GITHUB_TOKEN")
        gitee_token = os.getenv("GITEE_TOKEN")
        
        if github_token:
            self.github_client = GitHubClient(token=github_token)
        
        if gitee_token:
            self.gitee_client = GiteeClient(token=gitee_token)
        
        logger.info("仓库管理器初始化完成")
    
    def get_github_repos(self, username: Optional[str] = None) -> List[Repository]:
        """
        获取 GitHub 仓库列表
        
        Args:
            username: 用户名
            
        Returns:
            仓库列表
        """
        if not self.github_client:
            raise ValueError("GitHub 客户端未初始化，请设置 GITHUB_TOKEN 环境变量")
        
        return self.github_client.get_user_repos(username)
    
    def get_gitee_repos(self, username: Optional[str] = None) -> List[Repository]:
        """
        获取 Gitee 仓库列表
        
        Args:
            username: 用户名
            
        Returns:
            仓库列表
        """
        if not self.gitee_client:
            raise ValueError("Gitee 客户端未初始化，请设置 GITEE_TOKEN 环境变量")
        
        return self.gitee_client.get_user_repos(username)
    
    def get_all_repos(self, username: Optional[str] = None) -> Dict[str, List[Repository]]:
        """
        获取所有平台的仓库列表
        
        Args:
            username: 用户名
            
        Returns:
            {平台: 仓库列表}
        """
        result = {}
        
        if self.github_client:
            try:
                result["github"] = self.github_client.get_user_repos(username)
            except Exception as e:
                logger.error(f"获取 GitHub 仓库失败: {str(e)}")
                result["github"] = []
        
        if self.gitee_client:
            try:
                result["gitee"] = self.gitee_client.get_user_repos(username)
            except Exception as e:
                logger.error(f"获取 Gitee 仓库失败: {str(e)}")
                result["gitee"] = []
        
        return result
    
    def clone_repo(self, repo_url: str, target_dir: str, branch: Optional[str] = None) -> bool:
        """
        克隆仓库到本地
        
        Args:
            repo_url: 仓库 URL
            target_dir: 目标目录
            branch: 分支名（可选）
            
        Returns:
            是否克隆成功
        """
        try:
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 构建 git clone 命令
            cmd = ["git", "clone", repo_url]
            if branch:
                cmd.extend(["--branch", branch])
            
            logger.info(f"开始克隆仓库: {repo_url}")
            
            result = subprocess.run(
                cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"仓库克隆成功: {repo_url}")
                return True
            else:
                logger.error(f"仓库克隆失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"仓库克隆超时: {repo_url}")
            return False
        except Exception as e:
            logger.error(f"仓库克隆异常: {str(e)}")
            return False


# 全局仓库管理器实例
repository_manager = RepositoryManager()
