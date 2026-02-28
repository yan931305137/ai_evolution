"""
测试管家演示测试

演示如何使用测试管家模块的各种功能
"""

import pytest
from tests.test_manager.base import BaseTestCase
from tests.test_manager.registry import unit_test, integration_test, TestCategory, TestPriority


class TestManagerDemo(BaseTestCase):
    """测试管家功能演示"""
    
    def test_base_class_features(self):
        """测试基类功能"""
        # 临时文件
        temp_file = self.create_temp_file("测试内容", ".txt")
        self.assertFileExists(temp_file)
        self.assertFileContains(temp_file, "测试")
        
        # 临时目录
        temp_dir = self.create_temp_dir()
        self.assertTrue(temp_dir.exists())
        
        # 测试配置
        config = self.create_test_config({"model": {"temperature": 0.5}})
        self.assertEqual(config["model"]["temperature"], 0.5)
        
        # Mock LLM
        response = self.mock_llm_response("测试响应", [self.mock_tool_call("test", {"arg": 1})])
        self.assertEqual(response.content, "测试响应")
    
    def test_assertions(self):
        """测试自定义断言"""
        result = {"success": True, "data": "test"}
        self.assertSuccess(result)
        
        self.assertContains("hello world", "world")
        self.assertValidJson('{"key": "value"}')
        self.assertDictHasKeys({"a": 1, "b": 2}, ["a", "b"])
        self.assertInRange(50, 0, 100)  # 使用 unittest 原生的 assert 方式
    
    def test_factories(self):
        """测试数据工厂"""
        from tests.test_manager.factories import MemoryFactory, TaskFactory, CodeFactory
        
        # 记忆工厂
        memory = MemoryFactory.create_conversation("问题", "答案")
        self.assertEqual(memory["type"], "conversation")
        
        memories = MemoryFactory.create_batch(5, "knowledge")
        self.assertEqual(len(memories), 5)
        
        # 任务工厂
        task = TaskFactory.create_task(name="测试任务")
        self.assertEqual(task["name"], "测试任务")
        
        task_chain = TaskFactory.create_task_chain(3)
        self.assertEqual(len(task_chain), 3)
        self.assertEqual(task_chain[1]["dependencies"], ["chain_task_0"])
        
        # 代码工厂
        code = CodeFactory.create_python_function("test_func")
        self.assertIn("def test_func", code)
        
        buggy_code = CodeFactory.create_buggy_code("runtime_error")
        self.assertIn("Bug:", buggy_code)
    
    def test_helpers(self):
        """测试辅助工具"""
        from tests.test_manager.helpers import MockLLMHelper, AssertHelper
        
        # Mock LLM
        response = MockLLMHelper.create_response("测试")
        self.assertEqual(response.content, "测试")
        
        tool_call = MockLLMHelper.create_tool_call("search", {"q": "test"})
        self.assertEqual(tool_call["name"], "search")
        
        # 断言辅助
        self.assertTrue(AssertHelper.is_valid_json('{"key": "value"}'))
        self.assertTrue(AssertHelper.contains_all("abc", ["a", "b"]))
        self.assertTrue(AssertHelper.has_keys({"a": 1, "b": 2}, ["a"]))


@unit_test(priority=TestPriority.P0, description="高优先级单元测试示例")
def test_with_decorator():
    """使用装饰器的测试示例"""
    assert True


class TestWithFixtures:
    """演示 fixtures 的使用"""
    
    def test_brain_fixture(self, brain_instance):
        """使用 brain fixture"""
        assert brain_instance is not None
    
    def test_memory_fixture(self, memory_system):
        """使用 memory fixture"""
        # 添加测试记忆
        memory_system.add_memory("test", "测试内容")
        results = memory_system.search_memory("测试")
        assert len(results) > 0
    
    def test_memory_factory_fixture(self, memory_factory):
        """使用记忆工厂 fixture"""
        memory = memory_factory.create_knowledge("Python")
        assert "Python" in memory["content"]
    
    def test_task_factory_fixture(self, task_factory):
        """使用任务工厂 fixture"""
        tasks = task_factory.create_batch(3)
        assert len(tasks) == 3
    
    def test_code_factory_fixture(self, code_factory):
        """使用代码工厂 fixture"""
        code = code_factory.create_test_function("add")
        assert "class Test" in code  # 检查生成了测试类
        assert "def test_" in code   # 检查生成了测试方法
    
    def test_assert_helper_fixture(self, assert_helper):
        """使用断言辅助 fixture"""
        assert assert_helper.is_valid_json('{}')
        assert assert_helper.matches_pattern("test123", r"\d+")
