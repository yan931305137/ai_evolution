"""
覆盖率工具

提供测试覆盖率相关的辅助功能
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CoverageReport:
    """覆盖率报告数据类"""
    total_statements: int
    missing_statements: int
    coverage_percent: float
    files: Dict[str, Dict]
    
    @property
    def covered_statements(self) -> int:
        """已覆盖的语句数"""
        return self.total_statements - self.missing_statements
    
    def get_uncovered_files(self, threshold: float = 80.0) -> List[str]:
        """获取覆盖率低于阈值的文件"""
        return [
            f for f, data in self.files.items()
            if data.get('percent', 0) < threshold
        ]
    
    def get_file_coverage(self, filepath: str) -> Optional[float]:
        """获取指定文件的覆盖率"""
        if filepath in self.files:
            return self.files[filepath].get('percent')
        return None


class CoverageHelper:
    """覆盖率辅助类"""
    
    @staticmethod
    def run_coverage(module: str = "src", output_dir: str = "htmlcov") -> CoverageReport:
        """
        运行覆盖率测试并返回报告
        
        Args:
            module: 要测试的模块
            output_dir: HTML 报告输出目录
        
        Returns:
            覆盖率报告
        """
        # 运行 pytest 并生成覆盖率报告
        cmd = [
            "python", "-m", "pytest",
            "--cov", module,
            "--cov-report", "json",
            "--cov-report", f"html:{output_dir}",
            "-q"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 读取 JSON 报告
        try:
            with open("coverage.json") as f:
                data = json.load(f)
            
            totals = data.get('totals', {})
            files = {}
            
            for filepath, filedata in data.get('files', {}).items():
                files[filepath] = {
                    'statements': filedata.get('statements', 0),
                    'missing': filedata.get('missing', 0),
                    'percent': filedata.get('percent_covered', 0.0)
                }
            
            return CoverageReport(
                total_statements=totals.get('covered_lines', 0) + totals.get('missing_lines', 0),
                missing_statements=totals.get('missing_lines', 0),
                coverage_percent=totals.get('percent_covered', 0.0),
                files=files
            )
        except (FileNotFoundError, json.JSONDecodeError):
            return CoverageReport(0, 0, 0.0, {})
    
    @staticmethod
    def check_threshold(report: CoverageReport, threshold: float = 80.0) -> Tuple[bool, List[str]]:
        """
        检查覆盖率是否达到阈值
        
        Args:
            report: 覆盖率报告
            threshold: 阈值百分比
        
        Returns:
            (是否通过, 未达标的文件列表)
        """
        passed = report.coverage_percent >= threshold
        uncovered = report.get_uncovered_files(threshold)
        return passed, uncovered
    
    @staticmethod
    def generate_badge(report: CoverageReport, output_path: str = "coverage-badge.svg"):
        """
        生成覆盖率徽章
        
        Args:
            report: 覆盖率报告
            output_path: 输出路径
        """
        percent = report.coverage_percent
        
        # 确定颜色
        if percent >= 80:
            color = "brightgreen"
        elif percent >= 60:
            color = "green"
        elif percent >= 40:
            color = "yellow"
        else:
            color = "red"
        
        # 简单的 SVG 徽章
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="104" height="20">
            <linearGradient id="b" x2="0" y2="100%">
                <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
                <stop offset="1" stop-opacity=".1"/>
            </linearGradient>
            <clipPath id="a">
                <rect width="104" height="20" rx="3" fill="#fff"/>
            </clipPath>
            <g clip-path="url(#a)">
                <path fill="#555" d="M0 0h63v20H0z"/>
                <path fill="{color}" d="M63 0h41v20H63z"/>
                <path fill="url(#b)" d="M0 0h104v20H0z"/>
            </g>
            <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
                <text x="31.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
                <text x="31.5" y="14">coverage</text>
                <text x="83.5" y="15" fill="#010101" fill-opacity=".3">{percent:.0f}%</text>
                <text x="83.5" y="14">{percent:.0f}%</text>
            </g>
        </svg>"""
        
        Path(output_path).write_text(svg)
    
    @staticmethod
    def print_summary(report: CoverageReport):
        """打印覆盖率摘要"""
        print("\n" + "=" * 60)
        print("覆盖率报告摘要")
        print("=" * 60)
        print(f"总语句数: {report.total_statements}")
        print(f"已覆盖: {report.covered_statements}")
        print(f"未覆盖: {report.missing_statements}")
        print(f"覆盖率: {report.coverage_percent:.2f}%")
        print("=" * 60)
        
        # 显示覆盖率最低的文件
        if report.files:
            sorted_files = sorted(
                report.files.items(),
                key=lambda x: x[1].get('percent', 100)
            )[:10]  # 前10个
            
            print("\n覆盖率最低的文件:")
            for filepath, data in sorted_files:
                if data['percent'] < 100:
                    print(f"  {filepath}: {data['percent']:.1f}%")


class CoverageMonitor:
    """
    覆盖率监控器
    
    用于持续监控测试覆盖率变化
    """
    
    def __init__(self, baseline_file: str = ".coverage_baseline.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline = self._load_baseline()
    
    def _load_baseline(self) -> Dict:
        """加载基线数据"""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                return json.load(f)
        return {}
    
    def save_baseline(self, report: CoverageReport):
        """保存当前覆盖率为基线"""
        data = {
            "coverage_percent": report.coverage_percent,
            "total_statements": report.total_statements,
            "missing_statements": report.missing_statements
        }
        with open(self.baseline_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def compare_with_baseline(self, report: CoverageReport) -> Dict:
        """
        与基线比较
        
        Returns:
            变化信息字典
        """
        if not self.baseline:
            return {"status": "no_baseline", "change": 0}
        
        baseline_percent = self.baseline.get("coverage_percent", 0)
        current_percent = report.coverage_percent
        change = current_percent - baseline_percent
        
        return {
            "status": "improved" if change > 0 else "degraded" if change < 0 else "unchanged",
            "change": change,
            "baseline": baseline_percent,
            "current": current_percent
        }
    
    def check_regression(self, report: CoverageReport, 
                        max_degradation: float = 5.0) -> Tuple[bool, str]:
        """
        检查覆盖率是否下降过多
        
        Args:
            report: 当前报告
            max_degradation: 最大允许的下降百分比
        
        Returns:
            (是否通过, 消息)
        """
        comparison = self.compare_with_baseline(report)
        
        if comparison["status"] == "no_baseline":
            return True, "无基线数据"
        
        change = comparison["change"]
        if change < -max_degradation:
            return False, f"覆盖率下降 {abs(change):.2f}% (超过 {max_degradation}% 限制)"
        
        return True, f"覆盖率变化: {change:+.2f}%"
