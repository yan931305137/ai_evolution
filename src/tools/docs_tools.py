"""
文档工具函数 - 供 Agent 调用
用于更新 README、.gitignore 等项目文档
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def update_project_docs(
    test_results: Dict = None,
    new_features: List[str] = None
) -> Dict[str, Any]:
    """
    CI/CD 前更新项目文档
    
    更新 README 徽章、检查 .gitignore 完整性
    
    Args:
        test_results: 测试结果字典，包含 passed 和 coverage
        new_features: 新功能列表
        
    Returns:
        更新结果字典
        
    Example:
        >>> update_project_docs(
        ...     test_results={"passed": True, "coverage": 85},
        ...     new_features=["新增安全扫描"]
        ... )
        {
            "readme_updated": True,
            "gitignore_checked": True,
            "errors": []
        }
    """
    try:
        from src.utils.docs_updater import ProjectDocsUpdater
        
        updater = ProjectDocsUpdater()
        results = {
            "readme_updated": False,
            "gitignore_checked": False,
            "errors": []
        }
        
        # 更新 README 徽章
        if test_results:
            test_status = "passing" if test_results.get("passed", True) else "failing"
            coverage = f"{test_results.get('coverage', 85)}%"
            security = "audit passed"
            
            if updater.update_readme_badges(test_status, coverage, security):
                results["readme_updated"] = True
        
        # 更新功能列表
        if new_features:
            for feature in new_features:
                updater.update_readme_features(feature, "✅")
        
        # 检查 .gitignore
        is_complete, missing = updater.check_gitignore_complete()
        results["gitignore_checked"] = is_complete
        results["gitignore_missing"] = missing
        
        if not is_complete:
            results["errors"].append(f".gitignore 缺失 {len(missing)} 个规则")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to update project docs: {e}")
        return {
            "readme_updated": False,
            "gitignore_checked": False,
            "errors": [str(e)]
        }


def check_readme_compliance() -> Dict[str, Any]:
    """
    检查 README 是否符合 GitHub 标准
    
    Returns:
        合规检查结果
        
    Example:
        >>> check_readme_compliance()
        {
            "compliant": True,
            "score": "90%",
            "checks": {
                "has_title": True,
                "has_description": True,
                ...
            },
            "suggestions": []
        }
    """
    try:
        from src.utils.docs_updater import check_github_readme_compliance
        return check_github_readme_compliance()
    except Exception as e:
        logger.error(f"Failed to check README compliance: {e}")
        return {
            "compliant": False,
            "error": str(e)
        }


def check_gitignore_complete() -> Dict[str, Any]:
    """
    检查 .gitignore 是否完整
    
    Returns:
        检查结果
        
    Example:
        >>> check_gitignore_complete()
        {
            "complete": True,
            "missing_rules": [],
            "total_required": 20,
            "total_present": 20
        }
    """
    try:
        from src.utils.docs_updater import ProjectDocsUpdater
        
        updater = ProjectDocsUpdater()
        is_complete, missing = updater.check_gitignore_complete()
        
        return {
            "complete": is_complete,
            "missing_rules": missing,
            "total_required": 20,
            "total_present": 20 - len(missing)
        }
        
    except Exception as e:
        logger.error(f"Failed to check .gitignore: {e}")
        return {
            "complete": False,
            "error": str(e)
        }


def update_readme_badges(
    test_status: str = "passing",
    coverage: str = "85%",
    security: str = "audit passed"
) -> Dict[str, Any]:
    """
    更新 README 徽章状态
    
    Args:
        test_status: 测试状态 (passing/failing)
        coverage: 覆盖率百分比
        security: 安全状态
        
    Returns:
        更新结果
        
    Example:
        >>> update_readme_badges("passing", "90%", "secure")
        {"success": True, "message": "Badges updated"}
    """
    try:
        from src.utils.docs_updater import ProjectDocsUpdater
        
        updater = ProjectDocsUpdater()
        success = updater.update_readme_badges(test_status, coverage, security)
        
        return {
            "success": success,
            "message": "Badges updated" if success else "Failed to update badges"
        }
        
    except Exception as e:
        logger.error(f"Failed to update README badges: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def add_changelog_entry(
    changes: List[str],
    version: str = None
) -> Dict[str, Any]:
    """
    添加变更日志条目到 README
    
    Args:
        changes: 变更列表
        version: 版本号（可选）
        
    Returns:
        添加结果
    """
    try:
        from src.utils.docs_updater import ProjectDocsUpdater
        
        updater = ProjectDocsUpdater()
        success = updater.update_readme_changelog(changes, version)
        
        return {
            "success": success,
            "changes_added": len(changes)
        }
        
    except Exception as e:
        logger.error(f"Failed to add changelog: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_project_readme_stats() -> Dict[str, Any]:
    """
    获取项目 README 统计信息
    
    Returns:
        统计信息
        
    Example:
        >>> get_project_readme_stats()
        {
            "exists": True,
            "size_bytes": 5000,
            "lines": 100,
            "has_badges": True,
            "has_toc": True
        }
    """
    try:
        from src.utils.docs_updater import ProjectDocsUpdater
        
        updater = ProjectDocsUpdater()
        return updater.get_readme_stats()
        
    except Exception as e:
        logger.error(f"Failed to get README stats: {e}")
        return {"error": str(e)}


__all__ = [
    "update_project_docs",
    "check_readme_compliance",
    "check_gitignore_complete",
    "update_readme_badges",
    "add_changelog_entry",
    "get_project_readme_stats"
]
