#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 工具包装器 - 仓库管理
为 Agent 提供仓库管理能力
"""

import logging
from typing import Optional, List, Dict, Any
from langchain.tools import tool, ToolRuntime

try:
    from coze_coding_utils.runtime_ctx.context import new_context
except ImportError:
    def new_context(**kwargs):
        return None

from src.tools.repo_tools import repository_manager, Repository

logger = logging.getLogger(__name__)


# 工具函数（不带装饰器，可直接调用）
def _list_github_repos_impl(username: Optional[str] = None) -> str:
    """获取 GitHub 仓库列表的实现函数"""
    try:
        repos = repository_manager.get_github_repos(username)
        
        if not repos:
            return "未找到任何 GitHub 仓库"
        
        result = f"找到 {len(repos)} 个 GitHub 仓库:\n\n"
        
        for repo in repos:
            result += f"📦 {repo.name}\n"
            result += f"   描述: {repo.description or '无描述'}\n"
            result += f"   语言: {repo.language or '未知'}\n"
            result += f"   ⭐ {repo.stars} stars | 🍴 {repo.forks} forks\n"
            result += f"   URL: {repo.metadata.get('html_url', repo.url)}\n"
            result += f"   更新时间: {repo.updated_at}\n\n"
        
        logger.info(f"获取 GitHub 仓库列表成功: {len(repos)} 个仓库")
        return result
        
    except Exception as e:
        error_msg = f"获取 GitHub 仓库列表失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


# LangChain 工具（带装饰器，用于 Agent）
@tool
def list_github_repos(username: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """
    获取 GitHub 仓库列表
    
    Args:
        username: GitHub 用户名，如果不提供则获取认证用户的仓库
        
    Returns:
        仓库列表的格式化字符串
    """
    ctx = runtime.context if runtime else new_context(method="list_github_repos")
    return _list_github_repos_impl(username)

# 工具函数（不带装饰器）
def _list_gitee_repos_impl(username: Optional[str] = None) -> str:
    """获取 Gitee 仓库列表的实现函数"""
    try:
        repos = repository_manager.get_gitee_repos(username)
        
        if not repos:
            return "未找到任何 Gitee 仓库"
        
        result = f"找到 {len(repos)} 个 Gitee 仓库:\n\n"
        
        for repo in repos:
            result += f"📦 {repo.name}\n"
            result += f"   描述: {repo.description or '无描述'}\n"
            result += f"   语言: {repo.language or '未知'}\n"
            result += f"   ⭐ {repo.stars} stars | 🍴 {repo.forks} forks\n"
            result += f"   URL: {repo.metadata.get('html_url', repo.url)}\n"
            result += f"   更新时间: {repo.updated_at}\n\n"
        
        logger.info(f"获取 Gitee 仓库列表成功: {len(repos)} 个仓库")
        return result
        
    except Exception as e:
        error_msg = f"获取 Gitee 仓库列表失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


# LangChain 工具
@tool
def list_gitee_repos(username: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """
    获取 Gitee 仓库列表
    
    Args:
        username: Gitee 用户名，如果不提供则获取认证用户的仓库
        
    Returns:
        仓库列表的格式化字符串
    """
    ctx = runtime.context if runtime else new_context(method="list_gitee_repos")
    return _list_gitee_repos_impl(username)


# 工具函数（不带装饰器）
def _list_all_repos_impl(username: Optional[str] = None) -> str:
    """获取所有平台仓库列表的实现函数"""
    try:
        all_repos = repository_manager.get_all_repos(username)
        
        result = ""
        
        if "github" in all_repos and all_repos["github"]:
            result += f"## GitHub 仓库 ({len(all_repos['github'])} 个)\n\n"
            for repo in all_repos["github"]:
                result += f"📦 {repo.name} - ⭐{repo.stars} | {repo.metadata.get('html_url', repo.url)}\n"
            result += "\n"
        
        if "gitee" in all_repos and all_repos["gitee"]:
            result += f"## Gitee 仓库 ({len(all_repos['gitee'])} 个)\n\n"
            for repo in all_repos["gitee"]:
                result += f"📦 {repo.name} - ⭐{repo.stars} | {repo.metadata.get('html_url', repo.url)}\n"
            result += "\n"
        
        if not result:
            return "未找到任何仓库，请检查 GITHUB_TOKEN 或 GITEE_TOKEN 环境变量是否已配置"
        
        logger.info("获取所有平台仓库列表成功")
        return result
        
    except Exception as e:
        error_msg = f"获取所有平台仓库列表失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


# LangChain 工具
@tool
def list_all_repos(username: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """
    获取所有平台（GitHub + Gitee）的仓库列表
    
    Args:
        username: 用户名，如果不提供则获取认证用户的仓库
        
    Returns:
        所有平台仓库列表的格式化字符串
    """
    ctx = runtime.context if runtime else new_context(method="list_all_repos")
    return _list_all_repos_impl(username)


# 工具函数（不带装饰器）
def _clone_repo_impl(repo_url: str, target_dir: str, branch: Optional[str] = None) -> str:
    """克隆代码仓库到本地"""
    try:
        success = repository_manager.clone_repo(repo_url, target_dir, branch)
        
        if success:
            result = f"✅ 仓库克隆成功!\n"
            result += f"   源地址: {repo_url}\n"
            result += f"   目标目录: {target_dir}"
            if branch:
                result += f"\n   分支: {branch}"
            
            logger.info(f"仓库克隆成功: {repo_url} -> {target_dir}")
            return result
        else:
            result = f"❌ 仓库克隆失败!\n"
            result += f"   源地址: {repo_url}\n"
            result += f"   请检查:\n"
            result += f"   1. 仓库 URL 是否正确\n"
            result += f"   2. 网络连接是否正常\n"
            result += f"   3. 是否有访问权限（私有仓库需要 Token）"
            
            logger.error(f"仓库克隆失败: {repo_url}")
            return result
            
    except Exception as e:
        error_msg = f"仓库克隆异常: {str(e)}"
        logger.error(error_msg)
        return error_msg


# LangChain 工具
@tool
def clone_repo(repo_url: str, target_dir: str, branch: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """
    克隆代码仓库到本地
    
    Args:
        repo_url: 仓库的克隆 URL（可以是 HTTPS 或 SSH）
        target_dir: 本地目标目录（绝对路径或相对路径）
        branch: 要克隆的分支名（可选）
        
    Returns:
        克隆结果的格式化字符串
    """
    ctx = runtime.context if runtime else new_context(method="clone_repo")
    return _clone_repo_impl(repo_url, target_dir, branch)


# 工具函数（不带装饰器）
def _get_repo_info_impl(platform: str, owner: str, repo_name: str) -> str:
    """获取单个仓库的详细信息"""
    try:
        if platform.lower() == "github":
            if not repository_manager.github_client:
                return "GitHub 客户端未初始化，请设置 GITHUB_TOKEN 环境变量"
            
            repo = repository_manager.github_client.get_repo(owner, repo_name)
        elif platform.lower() == "gitee":
            if not repository_manager.gitee_client:
                return "Gitee 客户端未初始化，请设置 GITEE_TOKEN 环境变量"
            
            repo = repository_manager.gitee_client.get_repo(owner, repo_name)
        else:
            return f"不支持的平台: {platform}，请使用 'github' 或 'gitee'"
        
        result = f"## 仓库信息: {repo.name}\n\n"
        result += f"📝 描述: {repo.description or '无描述'}\n\n"
        result += f"💻 主要语言: {repo.language or '未知'}\n"
        result += f"⭐ Stars: {repo.stars}\n"
        result += f"🍴 Forks: {repo.forks}\n"
        result += f"🔒 是否私有: {'是' if repo.is_private else '否'}\n\n"
        result += f"🔗 仓库地址: {repo.metadata.get('html_url', repo.url)}\n"
        result += f"📦 克隆地址: {repo.url}\n"
        result += f"📅 最后更新: {repo.updated_at}\n"
        
        logger.info(f"获取仓库信息成功: {platform}/{owner}/{repo_name}")
        return result
        
    except Exception as e:
        error_msg = f"获取仓库信息失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


# LangChain 工具
@tool
def get_repo_info(platform: str, owner: str, repo_name: str, runtime: ToolRuntime = None) -> str:
    """
    获取单个仓库的详细信息
    
    Args:
        platform: 平台名称（'github' 或 'gitee'）
        owner: 仓库所有者用户名
        repo_name: 仓库名称
        
    Returns:
        仓库详细信息的格式化字符串
    """
    ctx = runtime.context if runtime else new_context(method="get_repo_info")
    return _get_repo_info_impl(platform, owner, repo_name)


# 导出所有工具
__all__ = [
    "list_github_repos",
    "list_gitee_repos",
    "list_all_repos",
    "clone_repo",
    "get_repo_info"
]
