"""
安全扫描工具 - 检测敏感信息泄露
用于 CI/CD 流程、预提交钩子和人工审查
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Severity(Enum):
    """严重级别"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    """安全发现项"""
    file_path: str
    line_number: int
    line_content: str
    pattern_name: str
    category: str
    severity: Severity
    matched_text: str
    description: str
    
    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content[:100] + "..." if len(self.line_content) > 100 else self.line_content,
            "pattern_name": self.pattern_name,
            "category": self.category,
            "severity": self.severity.value,
            "matched_text": self.matched_text[:50] + "..." if len(self.matched_text) > 50 else self.matched_text,
            "description": self.description
        }


@dataclass
class ScanResult:
    """扫描结果"""
    total_files: int
    files_scanned: int
    findings: List[SecurityFinding]
    scan_duration_ms: float
    scan_time: str
    passed: bool
    
    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "files_scanned": self.files_scanned,
            "findings_count": len(self.findings),
            "scan_duration_ms": self.scan_duration_ms,
            "scan_time": self.scan_time,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings]
        }
    
    def get_summary(self) -> str:
        """获取摘要"""
        critical = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        high = sum(1 for f in self.findings if f.severity == Severity.HIGH)
        medium = sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
        
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return (
            f"{status} | Files: {self.files_scanned}/{self.total_files} | "
            f"Findings: {len(self.findings)} (CRITICAL: {critical}, HIGH: {high}, MEDIUM: {medium})"
        )


class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "security_rules.json"
        )
        self.rules = self._load_rules()
        self.compiled_patterns: Dict[str, List[Tuple[str, re.Pattern, str, Severity]]] = {}
        self.allowed_patterns: List[re.Pattern] = []
        self._compile_patterns()
        
    def _load_rules(self) -> dict:
        """加载安全规则"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Security rules file not found: {self.rules_path}")
            return {"patterns": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in security rules: {e}")
            return {"patterns": {}}
    
    def _compile_patterns(self):
        """编译正则表达式"""
        patterns_config = self.rules.get("patterns", {})
        
        for category, config in patterns_config.items():
            self.compiled_patterns[category] = []
            for pattern_def in config.get("patterns", []):
                try:
                    compiled = re.compile(pattern_def["regex"])
                    severity = Severity(config.get("severity", "MEDIUM"))
                    self.compiled_patterns[category].append((
                        pattern_def["name"],
                        compiled,
                        pattern_def.get("example", ""),
                        severity
                    ))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_def.get('name', 'unknown')}': {e}")
        
        # 编译允许的模式（例外）
        allowed_config = self.rules.get("allowed_patterns", {})
        for pattern_def in allowed_config.get("patterns", []):
            try:
                self.allowed_patterns.append(re.compile(pattern_def["regex"]))
            except re.error as e:
                logger.warning(f"Invalid allowed pattern: {e}")
    
    def _is_allowed(self, content: str) -> bool:
        """检查内容是否在允许的例外中"""
        for pattern in self.allowed_patterns:
            if pattern.search(content):
                return True
        return False
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """判断是否应该扫描该文件"""
        file_rules = self.rules.get("file_rules", {})
        
        # 检查跳过目录
        skip_dirs = file_rules.get("skip_directories", [])
        for part in file_path.parts:
            if part in skip_dirs:
                return False
        
        # 检查跳过文件
        skip_files = file_rules.get("skip_files", [])
        file_name = file_path.name
        for pattern in skip_files:
            if pattern.startswith("*"):
                if file_name.endswith(pattern[1:]):
                    return False
            elif file_name == pattern:
                return False
        
        # 检查扩展名
        scan_exts = file_rules.get("scan_extensions", [])
        if file_path.suffix.lower() in scan_exts:
            return True
        
        # 检查文件名（如 .env）
        if file_path.name in [".env", ".env.local", ".env.production"]:
            return True
        
        return False
    
    def _scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """扫描单个文件"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"Cannot read file {file_path}: {e}")
            return findings
        
        # 检测是否是 JSON 配置文件（包含 example 字段）
        is_config_file = file_path.name.endswith('.json') and 'security_rules' in str(file_path)
        
        for line_num, line in enumerate(lines, start=1):
            # 首先检查是否是允许的例外
            if self._is_allowed(line):
                continue
            
            # 在配置文件中跳过包含 example 的行
            if is_config_file and '"example"' in line:
                continue
            
            # 扫描所有类别
            for category, patterns in self.compiled_patterns.items():
                for pattern_name, compiled, example, severity in patterns:
                    matches = compiled.finditer(line)
                    for match in matches:
                        matched_text = match.group(0)
                        
                        # 再次检查匹配文本是否在例外中
                        if self._is_allowed(matched_text):
                            continue
                        
                        finding = SecurityFinding(
                            file_path=str(file_path),
                            line_number=line_num,
                            line_content=line.strip(),
                            pattern_name=pattern_name,
                            category=category,
                            severity=severity,
                            matched_text=matched_text,
                            description=f"Detected {pattern_name}: {example}"
                        )
                        findings.append(finding)
        
        return findings
    
    def scan(
        self,
        target_path: str,
        max_critical: int = 0,
        max_high: int = 0,
        specific_files: Optional[List[str]] = None
    ) -> ScanResult:
        """
        执行安全扫描
        
        Args:
            target_path: 扫描目标路径
            max_critical: 允许的 CRITICAL 级别发现数（超过则失败）
            max_high: 允许的 HIGH 级别发现数（超过则失败）
            specific_files: 指定扫描的文件列表（为None则扫描整个目录）
            
        Returns:
            ScanResult: 扫描结果
        """
        start_time = datetime.now()
        findings: List[SecurityFinding] = []
        
        if specific_files:
            # 扫描指定文件
            files_to_scan = [Path(f) for f in specific_files if os.path.exists(f)]
            total_files = len(files_to_scan)
        else:
            # 扫描整个目录
            target = Path(target_path)
            if target.is_file():
                files_to_scan = [target]
                total_files = 1
            else:
                all_files = list(target.rglob("*"))
                files_to_scan = [f for f in all_files if f.is_file()]
                total_files = len(files_to_scan)
        
        files_scanned = 0
        for file_path in files_to_scan:
            if self._should_scan_file(file_path):
                file_findings = self._scan_file(file_path)
                findings.extend(file_findings)
                files_scanned += 1
        
        # 计算扫描时间
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # 判断是否通过
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == Severity.HIGH)
        passed = critical_count <= max_critical and high_count <= max_high
        
        return ScanResult(
            total_files=total_files,
            files_scanned=files_scanned,
            findings=findings,
            scan_duration_ms=duration_ms,
            scan_time=start_time.isoformat(),
            passed=passed
        )
    
    def scan_text(self, text: str) -> List[SecurityFinding]:
        """扫描文本内容（用于检查提交消息、PR描述等）"""
        findings = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            if self._is_allowed(line):
                continue
            
            for category, patterns in self.compiled_patterns.items():
                for pattern_name, compiled, example, severity in patterns:
                    matches = compiled.finditer(line)
                    for match in matches:
                        matched_text = match.group(0)
                        
                        if self._is_allowed(matched_text):
                            continue
                        
                        finding = SecurityFinding(
                            file_path="<text_content>",
                            line_number=line_num,
                            line_content=line.strip()[:100],
                            pattern_name=pattern_name,
                            category=category,
                            severity=severity,
                            matched_text=matched_text[:50],
                            description=f"Detected {pattern_name}"
                        )
                        findings.append(finding)
        
        return findings
    
    def sanitize_for_logging(self, text: str) -> str:
        """
        清理日志中的敏感信息
        将检测到的敏感信息替换为 [REDACTED]
        """
        sanitized = text
        
        for category, patterns in self.compiled_patterns.items():
            for pattern_name, compiled, example, severity in patterns:
                if severity in [Severity.CRITICAL, Severity.HIGH]:
                    sanitized = compiled.sub(f"[REDACTED:{pattern_name}]", sanitized)
        
        return sanitized


# 便捷函数
def run_security_scan(
    target_path: str = ".",
    output_format: str = "text",
    max_critical: int = 0,
    max_high: int = 0,
    specific_files: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    运行安全扫描并返回结果
    
    Returns:
        Tuple[bool, str]: (是否通过, 输出内容)
    """
    scanner = SecurityScanner()
    result = scanner.scan(target_path, max_critical, max_high, specific_files)
    
    if output_format == "json":
        output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    elif output_format == "markdown":
        output = _format_markdown(result)
    else:
        output = _format_text(result)
    
    return result.passed, output


def _format_text(result: ScanResult) -> str:
    """文本格式输出"""
    lines = [
        "=" * 60,
        "SECURITY SCAN REPORT",
        "=" * 60,
        f"Scan Time: {result.scan_time}",
        f"Duration: {result.scan_duration_ms:.2f}ms",
        f"Files Scanned: {result.files_scanned}/{result.total_files}",
        "",
        result.get_summary(),
        "",
    ]
    
    if result.findings:
        lines.append("FINDINGS:")
        lines.append("-" * 60)
        
        # 按严重级别排序
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        sorted_findings = sorted(result.findings, key=lambda f: severity_order.get(f.severity, 4))
        
        for finding in sorted_findings:
            icon = "🔴" if finding.severity == Severity.CRITICAL else "🟠" if finding.severity == Severity.HIGH else "🟡"
            lines.append(f"\n{icon} [{finding.severity.value}] {finding.pattern_name}")
            lines.append(f"   File: {finding.file_path}:{finding.line_number}")
            lines.append(f"   Match: {finding.matched_text}")
            lines.append(f"   Line: {finding.line_content[:80]}...")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def _format_markdown(result: ScanResult) -> str:
    """Markdown格式输出"""
    lines = [
        "# Security Scan Report",
        "",
        f"**Scan Time:** {result.scan_time}",
        f"**Duration:** {result.scan_duration_ms:.2f}ms",
        f"**Files Scanned:** {result.files_scanned}/{result.total_files}",
        f"**Status:** {'✅ PASSED' if result.passed else '❌ FAILED'}",
        "",
        "## Summary",
        "",
        f"- **Total Findings:** {len(result.findings)}",
        f"- **CRITICAL:** {sum(1 for f in result.findings if f.severity == Severity.CRITICAL)}",
        f"- **HIGH:** {sum(1 for f in result.findings if f.severity == Severity.HIGH)}",
        f"- **MEDIUM:** {sum(1 for f in result.findings if f.severity == Severity.MEDIUM)}",
        "",
    ]
    
    if result.findings:
        lines.append("## Findings")
        lines.append("")
        
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        sorted_findings = sorted(result.findings, key=lambda f: severity_order.get(f.severity, 4))
        
        for finding in sorted_findings:
            lines.append(f"### {finding.pattern_name}")
            lines.append("")
            lines.append(f"- **Severity:** {finding.severity.value}")
            lines.append(f"- **Category:** {finding.category}")
            lines.append(f"- **File:** `{finding.file_path}:{finding.line_number}`")
            lines.append(f"- **Match:** `{finding.matched_text}`")
            lines.append(f"- **Line:** `{finding.line_content[:100]}`")
            lines.append("")
    
    return "\n".join(lines)


def check_text_for_secrets(text: str) -> Tuple[bool, List[str]]:
    """
    检查文本是否包含敏感信息
    
    Returns:
        Tuple[bool, List[str]]: (是否安全, 发现的问题列表)
    """
    scanner = SecurityScanner()
    findings = scanner.scan_text(text)
    
    if not findings:
        return True, []
    
    issues = [
        f"[{f.severity.value}] {f.pattern_name} at line {f.line_number}: {f.matched_text}"
        for f in findings
    ]
    
    has_critical = any(f.severity == Severity.CRITICAL for f in findings)
    return not has_critical, issues


def sanitize_log_message(message: str) -> str:
    """清理日志消息中的敏感信息"""
    scanner = SecurityScanner()
    return scanner.sanitize_for_logging(message)


if __name__ == "__main__":
    # CLI 入口
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Scanner for OpenClaw")
    parser.add_argument("path", nargs="?", default=".", help="Path to scan")
    parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("--max-critical", type=int, default=0, help="Max allowed CRITICAL findings")
    parser.add_argument("--max-high", type=int, default=0, help="Max allowed HIGH findings")
    parser.add_argument("--files", nargs="+", help="Specific files to scan")
    
    args = parser.parse_args()
    
    passed, output = run_security_scan(
        args.path,
        args.format,
        args.max_critical,
        args.max_high,
        args.files
    )
    
    print(output)
    sys.exit(0 if passed else 1)
