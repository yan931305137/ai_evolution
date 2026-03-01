"""
Pytest 配置文件 - 整合测试管家模块

此文件集中管理所有测试 fixtures 和配置
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ==================== 导入测试管家模块 ====================

# 导入所有 fixtures
from tests.test_manager.fixtures import (
    # Brain fixtures
    brain_instance,
    planning_instance,
    memory_system,
    perception_system,
    value_system,
    emotion_system,
    orchestrator,
    sample_thought_data,
    sample_plan_data,
    sample_memory_data,
    # Tool fixtures
    file_tool,
    code_tool,
    git_tool,
    web_tool,
    directory_tool,
    shell_tool,
    json_tool,
    security_tool,
    text_tool,
    # Skill fixtures
    code_generation_skill,
    web_search_skill,
    analysis_skill,
    file_operation_skill,
    evolution_skill,
    business_skill,
    security_skill,
    skill_input_data,
    skill_output_schema,
    # Data fixtures
    test_data_dir,
    test_temp_dir,
    temp_file_factory,
    mock_llm_client,
    mock_config,
    sample_text_data,
    sample_code_data,
    error_scenarios,
)

# 导入辅助工具
from tests.test_manager.helpers import (
    MockLLMHelper,
    LLMResponseBuilder,
    MockLLMScenario,
    AssertHelper,
    CustomAssertions,
    CoverageHelper,
    CoverageMonitor,
)

# 导入数据工厂
from tests.test_manager.factories import (
    MemoryFactory,
    TaskFactory,
    TaskPriority,
    TaskStatus,
    CodeFactory,
)

# 导入测试注册中心
from tests.test_manager.registry import (
    TestRegistry,
    TestCategory,
    TestPriority,
    test_category,
    unit_test,
    integration_test,
    e2e_test,
    performance_test,
    registry,
)

# ==================== 依赖注入 Mock ====================

@pytest.fixture(autouse=True)
def mock_container_deps(monkeypatch):
    """
    自动 Mock 容器中的 Config 和 Logger
    避免测试时依赖真实的配置文件和日志输出
    """
    from src.core.container import container
    from src.utils.config import Config
    import logging

    # 1. Mock Config
    mock_cfg = type("MockConfig", (), {
        "get": lambda self, k, d=None: d,
        "llm_config": {},
        "db_config": {},
        "langsmith_config": {}
    })()
    
    # 2. Mock Logger
    mock_logger = logging.getLogger("MockLogger")
    mock_logger.setLevel(logging.DEBUG)
    
    # 临时替换容器中的实例
    original_instances = container._instances.copy()
    
    container.register(Config, lambda: mock_cfg)
    container.register(logging.Logger, lambda: mock_logger)
    
    yield
    
    # 恢复原始状态
    container._instances = original_instances

# ==================== Pytest 配置钩子 ====================

def pytest_configure(config):
    """
    Pytest 配置钩子
    
    在测试收集之前调用
    """
    # 自动发现测试
    registry.auto_discover()
    
    # 打印测试统计
    stats = registry.get_statistics()
    if stats['total'] > 0:
        print(f"\n测试管家: 已注册 {stats['total']} 个测试用例")
        print(f"  - 单元测试: {stats['by_category'].get('unit', 0)}")
        print(f"  - 集成测试: {stats['by_category'].get('integration', 0)}")
        print(f"  - 端到端测试: {stats['by_category'].get('e2e', 0)}")


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集项
    
    用于添加自定义标记、排序等
    """
    for item in items:
        # 根据测试名称自动添加标记
        if "brain" in item.nodeid.lower():
            item.add_marker(pytest.mark.brain)
        if "tool" in item.nodeid.lower():
            item.add_marker(pytest.mark.tool)
        if "skill" in item.nodeid.lower():
            item.add_marker(pytest.mark.skill)
        if "memory" in item.nodeid.lower():
            item.add_marker(pytest.mark.memory)
        if "planning" in item.nodeid.lower():
            item.add_marker(pytest.mark.planning)


def pytest_addoption(parser):
    """
    添加自定义命令行选项
    """
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="运行慢速测试"
    )
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="运行集成测试"
    )
    parser.addoption(
        "--run-e2e", action="store_true", default=False, help="运行端到端测试"
    )
    parser.addoption(
        "--test-category", action="store", default=None, help="按类别运行测试"
    )


def pytest_runtest_setup(item):
    """
    测试运行前设置
    """
    # 跳过慢速测试（除非指定 --run-slow）
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("需要 --run-slow 选项")
    
    # 跳过集成测试（除非指定 --run-integration）
    if "integration" in item.keywords and not item.config.getoption("--run-integration"):
        pytest.skip("需要 --run-integration 选项")
    
    # 跳过端到端测试（除非指定 --run-e2e）
    if "e2e" in item.keywords and not item.config.getoption("--run-e2e"):
        pytest.skip("需要 --run-e2e 选项")


# ==================== 自定义 Fixtures ====================

@pytest.fixture(scope="session")
def test_registry():
    """
    测试注册中心 fixture
    
    提供全局测试注册中心实例
    """
    return registry


@pytest.fixture
def assert_helper():
    """
    断言辅助工具 fixture
    
    使用示例:
        def test_something(assert_helper):
            assert assert_helper.is_valid_json('{"key": "value"}')
    """
    return AssertHelper


@pytest.fixture
def memory_factory():
    """
    记忆工厂 fixture
    
    使用示例:
        def test_memory(memory_factory):
            memory = memory_factory.create_conversation("你好", "你好！")
    """
    return MemoryFactory


@pytest.fixture
def task_factory():
    """
    任务工厂 fixture
    """
    return TaskFactory


@pytest.fixture
def code_factory():
    """
    代码工厂 fixture
    """
    return CodeFactory


@pytest.fixture
def llm_builder():
    """
    LLM 响应构建器 fixture
    
    使用示例:
        def test_with_llm(llm_builder):
            response = (llm_builder
                .add_text("首先")
                .add_tool_call("search", {"query": "测试"})
                .build())
    """
    return LLMResponseBuilder()


@pytest.fixture(scope="session")
def coverage_monitor():
    """
    覆盖率监控器 fixture
    """
    return CoverageMonitor()


# ==================== 标记定义 ====================

def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line("markers", "brain: 大脑模块测试")
    config.addinivalue_line("markers", "tool: 工具模块测试")
    config.addinivalue_line("markers", "skill: 技能模块测试")
    config.addinivalue_line("markers", "memory: 记忆模块测试")
    config.addinivalue_line("markers", "planning: 规划模块测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
