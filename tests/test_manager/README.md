# OpenClaw 测试管家 (Test Manager)

测试管家模块提供统一的测试基础设施，包括基类、fixtures、数据工厂和辅助工具。

## 目录结构

```
tests/test_manager/
├── __init__.py              # 模块入口
├── base.py                  # 测试基类
├── fixtures/                # 测试 fixtures
│   ├── brain_fixtures.py    # Brain 相关 fixtures
│   ├── tool_fixtures.py     # 工具相关 fixtures
│   ├── skill_fixtures.py    # 技能相关 fixtures
│   └── data_fixtures.py     # 通用数据 fixtures
├── factories/               # 数据工厂
│   ├── memory_factory.py    # 记忆数据工厂
│   ├── task_factory.py      # 任务数据工厂
│   └── code_factory.py      # 代码数据工厂
├── helpers/                 # 辅助工具
│   ├── mock_llm.py          # Mock LLM 工具
│   ├── assert_utils.py      # 自定义断言
│   └── coverage_utils.py    # 覆盖率工具
└── registry.py              # 测试注册中心
```

## 快速开始

### 1. 使用测试基类

```python
from tests.test_manager.base import BaseTestCase

class TestMyFeature(BaseTestCase):
    def test_something(self):
        # 使用基类提供的方法
        temp_file = self.create_temp_file("测试内容")
        self.assertFileExists(temp_file)
        self.assertFileContains(temp_file, "测试")
        
        # Mock LLM
        response = self.mock_llm_response("测试响应")
        self.assertEqual(response.content, "测试响应")
```

### 2. 使用 Fixtures

```python
# 自动注入 fixtures
def test_with_brain(brain_instance):
    result = brain_instance.process("测试")
    assert result is not None

def test_with_memory(memory_system):
    memory_system.add_memory("id", "内容")
    results = memory_system.search_memory("内容")
    assert len(results) > 0
```

### 3. 使用数据工厂

```python
from tests.test_manager.factories import MemoryFactory, TaskFactory, CodeFactory

# 生成记忆数据
memory = MemoryFactory.create_conversation("问题", "答案")
memories = MemoryFactory.create_batch(10, "knowledge")

# 生成任务数据
task = TaskFactory.create_task(name="测试任务")
task_chain = TaskFactory.create_task_chain(5)

# 生成代码
code = CodeFactory.create_python_function("my_func")
test_code = CodeFactory.create_test_function("add")
```

### 4. 使用测试装饰器

```python
from tests.test_manager.registry import unit_test, integration_test, Priority

@unit_test(priority=Priority.P0, description="核心功能测试")
def test_critical_feature():
    assert True

@integration_test(priority=Priority.P1, tags=["api", "slow"])
def test_api_integration():
    assert True
```

### 5. 使用辅助工具

```python
from tests.test_manager.helpers import MockLLMHelper, AssertHelper

# Mock LLM
response = MockLLMHelper.create_response("回答", tool_calls=[...])

# 自定义断言
assert AssertHelper.is_valid_json('{"key": "value"}')
assert AssertHelper.contains_all("abc", ["a", "b"])
```

## 提供的 Fixtures

### Brain Fixtures
- `brain_instance` - Brain 实例
- `planning_instance` - 规划系统实例
- `memory_system` - 记忆系统（内存模式）
- `perception_system` - 感知系统
- `value_system` - 价值系统
- `emotion_system` - 情感系统
- `orchestrator` - 编排器

### Tool Fixtures
- `file_tool` - 文件工具
- `code_tool` - 代码工具
- `git_tool` - Git 工具
- `web_tool` - Web 工具
- `directory_tool` - 目录工具
- `shell_tool` - Shell 工具
- `json_tool` - JSON 工具
- `security_tool` - 安全工具
- `text_tool` - 文本工具

### Skill Fixtures
- `code_generation_skill` - 代码生成技能
- `web_search_skill` - Web 搜索技能
- `analysis_skill` - 分析技能
- `file_operation_skill` - 文件操作技能
- `evolution_skill` - 进化技能
- `business_skill` - 业务技能
- `security_skill` - 安全技能

### 工厂 Fixtures
- `memory_factory` - 记忆工厂
- `task_factory` - 任务工厂
- `code_factory` - 代码工厂

## 基类方法

### 文件/目录管理
- `create_temp_dir()` - 创建临时目录
- `create_temp_file(content, suffix)` - 创建临时文件
- `temp_directory(suffix)` - 临时目录上下文管理器

### Mock 管理
- `mock_patch(target, **kwargs)` - 创建 patch mock
- `mock_llm_response(content, tool_calls)` - Mock LLM 响应
- `mock_tool_call(name, args)` - Mock 工具调用

### 自定义断言
- `assertSuccess(result)` - 断言成功
- `assertFailure(result)` - 断言失败
- `assertContains(container, item)` - 断言包含
- `assertValidJson(data)` - 断言有效 JSON
- `assertFileExists(path)` - 断言文件存在
- `assertFileContains(path, content)` - 断言文件包含内容
- `assertDictHasKeys(d, keys)` - 断言字典包含键
- `assertInRange(value, min, max)` - 断言值在范围内

### 配置
- `create_test_config(overrides)` - 创建测试配置

## 覆盖率监控

```python
from tests.test_manager.helpers import CoverageHelper, CoverageMonitor

# 运行覆盖率测试
report = CoverageHelper.run_coverage("src")

# 检查阈值
passed, files = CoverageHelper.check_threshold(report, 80.0)

# 监控覆盖率变化
monitor = CoverageMonitor()
monitor.save_baseline(report)
passed, msg = monitor.check_regression(report)
```

## 测试注册中心

```python
from tests.test_manager.registry import registry, Category, Priority

# 自动发现测试
registry.auto_discover()

# 获取统计信息
stats = registry.get_statistics()
print(f"总测试数: {stats['total']}")

# 按类别获取测试
unit_tests = registry.get_by_category(Category.UNIT)
high_priority = registry.get_by_priority(Priority.P0)

# 生成测试计划
plan = registry.get_test_plan(
    categories=[Category.UNIT, Category.INTEGRATION],
    min_priority=Priority.P1
)

# 导出报告
registry.generate_report("test_report.json")
```

## 最佳实践

1. **使用基类**：所有测试类继承 `BaseTestCase` 或 `AsyncBaseTestCase`
2. **使用 Fixtures**：优先使用提供的 fixtures 而非手动创建实例
3. **使用工厂**：使用数据工厂生成测试数据，保持一致性
4. **标记测试**：使用装饰器标记测试类别和优先级
5. **自定义断言**：使用基类提供的断言方法，提高可读性

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定类别的测试
pytest tests/ -m unit
pytest tests/ -m integration

# 运行带覆盖率
pytest tests/ --cov=src --cov-report=html

# 运行慢速测试
pytest tests/ --run-slow

# 运行集成测试
pytest tests/ --run-integration
```
