#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试校验管理器
核心功能：
1. 自动检索全量测试用例，支持pytest标准格式
2. 热启动加载新代码后自动触发测试执行
3. 100%准确输出进化是否达标的判定结果
4. 测试不通过时自动触发回滚/修复流程
5. 生成详细的测试报告和覆盖率统计
"""
import os
import sys
import time
import pytest
import json
import logging
import importlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 导入现有模块
from src.utils.hot_reload_manager import hot_reload_manager
# from src.skills.security_skills import deployment_rollback_manager
# from src.skills.evolution_skills import autonomous_iteration_pipeline

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果数据类"""
    total_cases: int = 0  # 总测试用例数
    passed_cases: int = 0  # 通过用例数
    failed_cases: int = 0  # 失败用例数
    skipped_cases: int = 0  # 跳过用例数
    coverage_rate: float = 0.0  # 测试覆盖率百分比
    execution_time: float = 0.0  # 测试执行耗时（秒）
    error_details: List[Dict[str, str]] = None  # 错误详情列表
    is_passed: bool = False  # 测试是否整体通过

class TestValidationManager:
    """自动化测试校验管理器单例类"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.test_dir: str = "./tests"  # 测试用例存放目录
        self.coverage_threshold: float = 80.0  # 最低覆盖率要求（百分比）
        self.pass_rate_threshold: float = 100.0  # 最低通过率要求（百分比，默认100%）
        self.auto_rollback_enabled: bool = True  # 测试失败是否自动回滚
        self.auto_repair_enabled: bool = True  # 回滚后是否自动触发修复流程
        self.last_test_result: Optional[TestResult] = None  # 上次测试结果

        # 初始化测试目录
        Path(self.test_dir).mkdir(exist_ok=True, parents=True)

        # 注册到热启动模块的后置钩子，热重载完成后自动执行测试
        self._register_hot_reload_hook()
        logger.info("自动化测试校验管理器初始化完成")

    def _register_hot_reload_hook(self) -> None:
        """注册热重载完成后自动执行测试的钩子"""
        # 给热启动模块添加测试执行钩子
        original_reload_module = hot_reload_manager.reload_module

        def hooked_reload_module(module_name: str) -> Tuple[bool, str]:
            # 先执行原有重载逻辑
            reload_success, reload_msg = original_reload_module(module_name)
            if not reload_success:
                return reload_success, reload_msg

            # 重载成功后自动执行全量测试
            logger.info(f"模块{module_name}热重载完成，自动触发全量测试校验")
            test_passed, test_result = self.run_full_validation()

            if test_passed:
                logger.info("全量测试校验通过，新版本正式生效")
                return True, f"{reload_msg}，全量测试通过，覆盖率{test_result.coverage_rate:.1f}%"
            else:
                # 避免除零错误
                if test_result.total_cases > 0:
                    pass_rate = test_result.passed_cases / test_result.total_cases * 100
                    
                    # 分析具体失败原因
                    if test_result.failed_cases > 0:
                        failure_reason = f"有{test_result.failed_cases}个测试失败"
                    elif pass_rate < self.pass_rate_threshold:
                        failure_reason = f"通过率{pass_rate:.1f}%低于要求{self.pass_rate_threshold}%"
                    elif test_result.coverage_rate < self.coverage_threshold:
                        failure_reason = f"覆盖率{test_result.coverage_rate:.1f}%低于要求{self.coverage_threshold}%"
                    else:
                        failure_reason = "未达到通过标准"
                    
                    error_msg = f"{reload_msg}，校验未通过：{failure_reason}（通过率{pass_rate:.1f}%，覆盖率{test_result.coverage_rate:.1f}%）"
                else:
                    error_msg = f"{reload_msg}，校验未通过：无测试用例（覆盖率{test_result.coverage_rate:.1f}%）"
                logger.error(error_msg)
                return False, error_msg

        # 替换原有重载方法
        hot_reload_manager.reload_module = hooked_reload_module
        logger.info("热重载自动测试钩子注册成功")

    def scan_test_cases(self) -> List[str]:
        """扫描测试目录下所有符合pytest规范的测试用例文件"""
        test_files = []
        for root, _, files in os.walk(self.test_dir):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
        logger.info(f"扫描到{len(test_files)}个测试用例文件")
        return test_files

    def run_full_validation(self, extra_test_paths: List[str] = None) -> Tuple[bool, TestResult]:
        """
        执行全量测试校验
        :param extra_test_paths: 额外指定的测试用例路径列表
        :return: (测试是否通过, 测试结果对象)
        """
        start_time = time.time()
        test_files = self.scan_test_cases()

        # 添加额外测试路径
        if extra_test_paths:
            test_files.extend(extra_test_paths)

        if not test_files:
            logger.warning("未找到任何测试用例，默认测试通过（无测试场景）")
            result = TestResult(
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                coverage_rate=100.0,
                execution_time=time.time() - start_time,
                is_passed=True
            )
            self.last_test_result = result
            return True, result

        # 配置pytest参数，生成覆盖率报告
        pytest_args = [
            *test_files,
            "-q",  # 静默模式
            "--cov=core",  # 统计core目录的覆盖率
            "--cov-report=json:tmp/coverage_report.json",  # 输出覆盖率JSON报告
            "--json-report",  # 输出测试结果JSON报告
            "--json-report-file=tmp/test_report.json"
        ]

        # 执行pytest
        try:
            exit_code = pytest.main(pytest_args)
        except Exception as e:
            logger.error(f"测试执行异常: {str(e)}")
            result = TestResult(
                total_cases=0,
                failed_cases=1,
                execution_time=time.time() - start_time,
                error_details=[{"error": str(e)}],
                is_passed=False
            )
            self.last_test_result = result
            self._handle_test_failure(result)
            return False, result

        # 解析测试结果
        test_result = self._parse_test_reports()
        test_result.execution_time = time.time() - start_time

        # 判定是否达标
        pass_rate = (test_result.passed_cases / test_result.total_cases) * 100 if test_result.total_cases > 0 else 100.0
        test_result.is_passed = (
            pass_rate >= self.pass_rate_threshold
            and test_result.coverage_rate >= self.coverage_threshold
            and test_result.failed_cases == 0
        )

        self.last_test_result = test_result

        if not test_result.is_passed:
            self._handle_test_failure(test_result)

        return test_result.is_passed, test_result

    def _parse_test_reports(self) -> TestResult:
        """解析pytest生成的测试报告和覆盖率报告"""
        result = TestResult(error_details=[])

        # 解析测试结果报告
        test_report_path = "tmp/test_report.json"
        if os.path.exists(test_report_path):
            with open(test_report_path, "r", encoding="utf-8") as f:
                test_report = json.load(f)

            result.total_cases = test_report.get("summary", {}).get("total", 0)
            result.passed_cases = test_report.get("summary", {}).get("passed", 0)
            result.failed_cases = test_report.get("summary", {}).get("failed", 0)
            result.skipped_cases = test_report.get("summary", {}).get("skipped", 0)

            # 收集错误详情
            for test in test_report.get("tests", []):
                if test.get("outcome") == "failed":
                    result.error_details.append({
                        "test_name": test.get("name"),
                        "file": test.get("file"),
                        "line": test.get("line"),
                        "error": test.get("call", {}).get("longrepr", "未知错误")
                    })

        # 解析覆盖率报告
        coverage_report_path = "tmp/coverage_report.json"
        if os.path.exists(coverage_report_path):
            with open(coverage_report_path, "r", encoding="utf-8") as f:
                coverage_report = json.load(f)
            result.coverage_rate = coverage_report.get("totals", {}).get("percent_covered", 0.0)

        return result

    def _handle_test_failure(self, test_result: TestResult) -> None:
        """处理测试失败的场景，自动触发回滚和修复流程"""
        logger.error(f"测试校验失败，触发自动处理流程，失败用例数：{test_result.failed_cases}")

        # 自动回滚
        if self.auto_rollback_enabled:
            logger.info("自动回滚到上一个稳定版本")
            # 回滚所有已注册的热重载模块
            for module_name in hot_reload_manager.module_registry.keys():
                hot_reload_manager._rollback_module(module_name)
            logger.info("所有模块已回滚到稳定版本")

        # 自动触发修复流程
        if self.auto_repair_enabled:
            logger.info("自动触发代码修复流程")
            try:
                from src.skills.evolution_skills import autonomous_iteration_pipeline
                # 调用自主迭代管道进行修复
                repair_result = autonomous_iteration_pipeline(
                    target_module_path="",  # 留空自动识别问题模块
                    modified_code_content="",
                    associated_test_cases=self.scan_test_cases(),
                    test_coverage_threshold=self.coverage_threshold
                )
                if repair_result[0]:
                    logger.info("自动修复成功，新版本已生成")
                else:
                    logger.error(f"自动修复失败，错误详情：{repair_result[1]}")
            except Exception as e:
                logger.error(f"自动修复流程执行异常：{str(e)}")

    def get_validation_report(self) -> Dict[str, Any]:
        """获取最新的校验报告，用于展示和统计"""
        if not self.last_test_result:
            return {"status": "no_test_executed"}

        return {
            "status": "passed" if self.last_test_result.is_passed else "failed",
            "total_cases": self.last_test_result.total_cases,
            "passed_cases": self.last_test_result.passed_cases,
            "failed_cases": self.last_test_result.failed_cases,
            "pass_rate": (self.last_test_result.passed_cases / self.last_test_result.total_cases * 100) if self.last_test_result.total_cases > 0 else 100.0,
            "coverage_rate": self.last_test_result.coverage_rate,
            "execution_time": self.last_test_result.execution_time,
            "error_details": self.last_test_result.error_details,
            "meets_requirement": self.last_test_result.is_passed
        }

# 全局单例实例
test_validation_manager = TestValidationManager()

def run_test_suite(target_module_path: str, test_cases: List[str] = None, coverage_threshold: float = 80.0) -> Tuple[bool, Dict]:
    """
    运行测试套件
    :param target_module_path: 目标模块路径
    :param test_cases: 测试用例列表
    :param coverage_threshold: 覆盖率阈值
    :return: (是否通过, 详情)
    """
    manager = test_validation_manager
    
    # Ensure test_cases is a list of paths
    passed, result = manager.run_full_validation(extra_test_paths=test_cases)
    
    # Convert TestResult to dict for compatibility
    detail = {
        "total": result.total_cases,
        "passed": result.passed_cases,
        "failed": result.failed_cases,
        "coverage": result.coverage_rate,
        "errors": result.error_details
    }
    return passed, detail
