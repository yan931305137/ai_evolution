"""
安全扫描工具函数 - 供 Agent 调用
用于检测敏感信息、清理日志、检查代码安全性
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def scan_code_for_secrets(
    file_paths: Optional[List[str]] = None,
    scan_all: bool = False,
    max_critical: int = 0,
    max_high: int = 0
) -> Dict[str, Any]:
    """
    扫描代码中的敏感信息
    
    Args:
        file_paths: 要扫描的文件路径列表（为None时根据 scan_all 决定）
        scan_all: 是否扫描整个项目
        max_critical: 允许的 CRITICAL 级别发现数
        max_high: 允许的 HIGH 级别发现数
        
    Returns:
        扫描结果字典
        
    Example:
        >>> scan_code_for_secrets(file_paths=["src/main.py"])
        {
            "passed": true,
            "files_scanned": 1,
            "findings": [],
            "summary": "✅ PASSED | Files: 1/1 | Findings: 0"
        }
    """
    try:
        from src.utils.security_scanner import run_security_scan
        
        target_path = "." if scan_all else "."
        passed, output = run_security_scan(
            target_path=target_path,
            output_format="json",
            max_critical=max_critical,
            max_high=max_high,
            specific_files=file_paths
        )
        
        import json
        result = json.loads(output)
        result["passed"] = passed
        
        return result
        
    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        return {
            "passed": False,
            "error": str(e),
            "files_scanned": 0,
            "findings": [],
            "summary": f"Scan failed: {e}"
        }


def check_text_security(text: str) -> Dict[str, Any]:
    """
    检查文本内容是否包含敏感信息
    
    Args:
        text: 要检查的文本内容
        
    Returns:
        检查结果字典
        
    Example:
        >>> check_text_security("API key: sk-abc123")
        {
            "is_safe": false,
            "issues": ["[CRITICAL] OpenAI API Key: sk-abc123"],
            "sanitized": "API key: [REDACTED:OpenAI API Key]"
        }
    """
    try:
        from src.utils.security_scanner import check_text_for_secrets, SecurityScanner
        
        is_safe, issues = check_text_for_secrets(text)
        
        scanner = SecurityScanner()
        sanitized = scanner.sanitize_for_logging(text)
        
        return {
            "is_safe": is_safe,
            "issues": issues,
            "sanitized": sanitized,
            "issues_count": len(issues)
        }
        
    except Exception as e:
        logger.error(f"Text security check failed: {e}")
        return {
            "is_safe": False,
            "issues": [f"Check failed: {e}"],
            "sanitized": text,
            "issues_count": 1
        }


def sanitize_sensitive_data(text: str) -> str:
    """
    清理文本中的敏感数据
    
    将检测到的敏感信息（API keys、密码等）替换为 [REDACTED]
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
        
    Example:
        >>> sanitize_sensitive_data("Key: sk-abc123, Password: secret123")
        "Key: [REDACTED:OpenAI API Key], Password: [REDACTED:Password in Code]"
    """
    try:
        from src.utils.security_scanner import SecurityScanner
        scanner = SecurityScanner()
        return scanner.sanitize_for_logging(text)
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        # 如果清理失败，返回提示信息
        return "[Content sanitized due to security policy]"


def validate_pr_content(
    title: str,
    body: str,
    branch: str = ""
) -> Dict[str, Any]:
    """
    验证 PR 内容安全性
    
    在创建 PR 前调用此函数检查标题和内容是否包含敏感信息
    
    Args:
        title: PR 标题
        body: PR 内容
        branch: 分支名（可选）
        
    Returns:
        验证结果字典
        
    Example:
        >>> validate_pr_content(
        ...     title="Fix: update API key",
        ...     body="Changed key to sk-newkey123"
        ... )
        {
            "is_valid": false,
            "errors": ["[Title] Pass", "[Body] [CRITICAL] OpenAI API Key detected"],
            "recommendation": "Remove sensitive data before creating PR"
        }
    """
    errors = []
    
    # 检查标题
    title_check = check_text_security(title)
    if not title_check["is_safe"]:
        errors.extend([f"[Title] {issue}" for issue in title_check["issues"]])
    
    # 检查内容
    body_check = check_text_security(body)
    if not body_check["is_safe"]:
        errors.extend([f"[Body] {issue}" for issue in body_check["issues"]])
    
    # 检查分支名
    if branch:
        branch_check = check_text_security(branch)
        if not branch_check["is_safe"]:
            errors.extend([f"[Branch] {issue}" for issue in branch_check["issues"]])
    
    is_valid = len(errors) == 0
    
    result = {
        "is_valid": is_valid,
        "errors": errors,
        "title_safe": title_check["is_safe"],
        "body_safe": body_check["is_safe"],
        "recommendation": None
    }
    
    if not is_valid:
        result["recommendation"] = (
            "Sensitive information detected. Please:\n"
            "1. Use environment variables instead of hardcoded secrets\n"
            "2. Move configuration to .env files (not committed)\n"
            "3. Use placeholder values like 'YOUR_API_KEY_HERE'\n"
            "4. Review and sanitize the content before creating PR"
        )
        result["sanitized_body"] = body_check["sanitized"]
    
    return result


def check_commit_message_safety(message: str) -> Dict[str, Any]:
    """
    检查提交信息安全性
    
    Args:
        message: 提交信息
        
    Returns:
        检查结果
        
    Example:
        >>> check_commit_message_safety("Add API key: sk-12345")
        {
            "is_safe": false,
            "issues": ["[CRITICAL] OpenAI API Key in commit message"],
            "sanitized_message": "Add API key: [REDACTED:OpenAI API Key]"
        }
    """
    result = check_text_security(message)
    
    return {
        "is_safe": result["is_safe"],
        "issues": result["issues"],
        "sanitized_message": result["sanitized"],
        "can_commit": result["is_safe"]  # 是否允许提交
    }


def run_pre_commit_check() -> Dict[str, Any]:
    """
    运行完整的预提交安全检查
    
    扫描暂存文件和提交信息，模拟 pre-commit 钩子
    
    Returns:
        检查结果
        
    Example:
        >>> run_pre_commit_check()
        {
            "passed": true,
            "staged_files_scanned": 3,
            "findings": [],
            "can_commit": true
        }
    """
    import subprocess
    import os
    
    results = {
        "passed": True,
        "staged_files_scanned": 0,
        "findings": [],
        "can_commit": True,
        "errors": []
    }
    
    try:
        # 获取暂存文件列表
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        staged_files = [f for f in result.stdout.strip().split('\n') if f]
        
        if not staged_files:
            return {
                "passed": True,
                "staged_files_scanned": 0,
                "findings": [],
                "can_commit": True,
                "message": "No staged files to check"
            }
        
        # 扫描暂存文件
        scan_result = scan_code_for_secrets(
            file_paths=staged_files,
            max_critical=0,
            max_high=0
        )
        
        results["staged_files_scanned"] = scan_result.get("files_scanned", 0)
        results["findings"] = scan_result.get("findings", [])
        results["passed"] = scan_result.get("passed", False)
        results["can_commit"] = results["passed"]
        
        if not results["passed"]:
            results["errors"].append("Security issues found in staged files")
        
    except Exception as e:
        logger.error(f"Pre-commit check failed: {e}")
        results["errors"].append(str(e))
        results["passed"] = False
        results["can_commit"] = False
    
    return results


def get_security_rules_info() -> Dict[str, Any]:
    """
    获取安全规则信息
    
    返回当前配置的安全检测规则说明
    
    Returns:
        规则信息字典
    """
    return {
        "description": "OpenClaw Security Scanner Rules",
        "categories": {
            "api_keys": {
                "description": "API Keys and Tokens",
                "severity": "CRITICAL",
                "examples": [
                    "GitHub Token (ghp_xxx)",
                    "AWS Access Key (AKIA...)",
                    "OpenAI API Key (sk-...)",
                    "Private Keys"
                ]
            },
            "passwords": {
                "description": "Passwords and Credentials",
                "severity": "CRITICAL",
                "examples": [
                    "Hardcoded passwords",
                    "Secret values"
                ]
            },
            "personal_info": {
                "description": "Personal Information",
                "severity": "HIGH",
                "examples": [
                    "Email addresses",
                    "Phone numbers",
                    "ID cards"
                ]
            },
            "urls": {
                "description": "Sensitive URLs",
                "severity": "MEDIUM",
                "examples": [
                    "Internal IPs",
                    "Localhost URLs"
                ]
            }
        },
        "allowed_patterns": [
            "Environment variables (${VAR}, getenv)",
            "Config placeholders (YOUR_KEY_HERE, PLACEHOLDER)",
            "Example domains (example.com)",
            "Empty/null values"
        ],
        "best_practices": [
            "Use environment variables for secrets",
            "Add sensitive files to .gitignore",
            "Use placeholder values in examples",
            "Regularly rotate exposed credentials",
            "Enable branch protection rules"
        ]
    }


# 便捷导出
__all__ = [
    "scan_code_for_secrets",
    "check_text_security",
    "sanitize_sensitive_data",
    "validate_pr_content",
    "check_commit_message_safety",
    "run_pre_commit_check",
    "get_security_rules_info"
]
