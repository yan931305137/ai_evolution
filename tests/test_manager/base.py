"""
测试基类

提供统一的测试基础设施，包括：
- 自动化的 setup/teardown
- 通用的断言方法
- 测试数据管理
- Mock 对象管理
"""

import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager


class BaseTestCase(unittest.TestCase):
    """
    同步测试基类
    
    使用示例:
        class TestMyFeature(BaseTestCase):
            def test_something(self):
                data = self.create_test_data()
                result = self.run_with_mock_llm("测试响应")
                self.assertSuccess(result)
    """
    
    # 测试类别标识，用于分类统计
    test_category: str = "unit"
    
    @classmethod
    def setUpClass(cls):
        """类级设置 - 创建临时目录等"""
        super().setUpClass()
        cls._temp_dirs: List[Path] = []
        cls._mocks: List = []
    
    @classmethod
    def tearDownClass(cls):
        """类级清理 - 删除临时目录等"""
        # 清理临时目录
        for temp_dir in getattr(cls, '_temp_dirs', []):
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        # 停止所有 mock
        for mock in getattr(cls, '_mocks', []):
            mock.stop()
        
        super().tearDownClass()
    
    def setUp(self):
        """测试方法级设置"""
        super().setUp()
        self._test_temp_dir: Optional[Path] = None
        self._method_mocks: List = []
    
    def tearDown(self):
        """测试方法级清理"""
        # 清理方法级临时目录
        if self._test_temp_dir and self._test_temp_dir.exists():
            shutil.rmtree(self._test_temp_dir)
        
        # 停止方法级 mock
        for mock in self._method_mocks:
            mock.stop()
        
        super().tearDown()
    
    # ==================== 临时文件/目录管理 ====================
    
    def create_temp_dir(self, suffix: str = "") -> Path:
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp(suffix=suffix))
        self._temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> Path:
        """创建临时文件"""
        temp_dir = self.create_temp_dir()
        temp_file = temp_dir / f"test_file{suffix}"
        temp_file.write_text(content, encoding='utf-8')
        return temp_file
    
    @contextmanager
    def temp_directory(self, suffix: str = ""):
        """临时目录上下文管理器"""
        temp_dir = self.create_temp_dir(suffix)
        try:
            yield temp_dir
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            if temp_dir in self._temp_dirs:
                self._temp_dirs.remove(temp_dir)
    
    # ==================== Mock 管理 ====================
    
    def mock_patch(self, target: str, **kwargs) -> Mock:
        """
        创建 patch mock，自动管理生命周期
        
        Args:
            target: 要 mock 的对象路径，如 'src.brain.brain.LLMClient'
            **kwargs: 传递给 mock 的参数
        
        Returns:
            Mock 对象
        """
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        self._method_mocks.append(patcher)
        return mock
    
    def mock_llm_response(self, content: str = "测试响应", 
                         tool_calls: Optional[List[Dict]] = None) -> MagicMock:
        """
        创建 LLM 响应 mock
        
        Args:
            content: 响应内容
            tool_calls: 工具调用列表
        
        Returns:
            Mock 响应对象
        """
        response = MagicMock()
        response.content = content
        response.tool_calls = tool_calls or []
        response.model_dump.return_value = {
            "content": content,
            "tool_calls": tool_calls or []
        }
        return response
    
    def mock_tool_call(self, name: str, args: Dict[str, Any]) -> Dict:
        """
        创建工具调用 mock
        
        Args:
            name: 工具名称
            args: 工具参数
        
        Returns:
            工具调用字典
        """
        return {
            "name": name,
            "args": args
        }
    
    # ==================== 通用断言方法 ====================
    
    def assertSuccess(self, result: Any, msg: Optional[str] = None):
        """断言操作成功"""
        if isinstance(result, dict):
            self.assertTrue(result.get('success', False), msg or f"操作失败: {result}")
        elif hasattr(result, 'success'):
            self.assertTrue(result.success, msg)
        else:
            self.assertTrue(bool(result), msg)
    
    def assertFailure(self, result: Any, msg: Optional[str] = None):
        """断言操作失败"""
        if isinstance(result, dict):
            self.assertFalse(result.get('success', True), msg)
        elif hasattr(result, 'success'):
            self.assertFalse(result.success, msg)
        else:
            self.assertFalse(bool(result), msg)
    
    def assertContains(self, container: Any, item: Any, msg: Optional[str] = None):
        """断言包含关系"""
        if isinstance(container, str):
            self.assertIn(item, container, msg)
        elif isinstance(container, (list, tuple)):
            self.assertIn(item, container, msg)
        elif isinstance(container, dict):
            self.assertIn(item, container, msg)
        else:
            raise TypeError(f"不支持的容器类型: {type(container)}")
    
    def assertValidJson(self, data: str, msg: Optional[str] = None):
        """断言有效的 JSON"""
        import json
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            self.fail(msg or f"无效的 JSON: {e}")
    
    def assertFileExists(self, path: Path, msg: Optional[str] = None):
        """断言文件存在"""
        self.assertTrue(path.exists(), msg or f"文件不存在: {path}")
    
    def assertFileContains(self, path: Path, content: str, msg: Optional[str] = None):
        """断言文件包含内容"""
        self.assertFileExists(path)
        file_content = path.read_text(encoding='utf-8')
        self.assertIn(content, file_content, msg)
    
    def assertDictHasKeys(self, d: Dict, keys: List[str], msg: Optional[str] = None):
        """断言字典包含所有指定键"""
        for key in keys:
            self.assertIn(key, d, msg or f"字典缺少键: {key}")
    
    def assertInRange(self, value: Any, min_val: Any, max_val: Any, msg: Optional[str] = None):
        """断言值在指定范围内"""
        self.assertGreaterEqual(value, min_val, msg or f"{value} 小于最小值 {min_val}")
        self.assertLessEqual(value, max_val, msg or f"{value} 大于最大值 {max_val}")

    # ==================== 测试数据生成 ====================
    
    def create_test_config(self, overrides: Optional[Dict] = None) -> Dict:
        """
        创建测试配置
        
        Args:
            overrides: 覆盖默认配置的参数
        
        Returns:
            配置字典
        """
        config = {
            "model": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "memory": {
                "provider": "memory_only",  # 测试时使用内存模式
                "embedding_model": "simple"
            },
            "max_steps": 5,
            "timeout": 30
        }
        if overrides:
            self._deep_update(config, overrides)
        return config
    
    def _deep_update(self, d: Dict, u: Dict):
        """深度更新字典"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v


class AsyncBaseTestCase(BaseTestCase):
    """
    异步测试基类
    
    使用示例:
        class TestAsyncFeature(AsyncBaseTestCase):
            async def test_async_operation(self):
                result = await self.run_async(self.async_method())
                self.assertSuccess(result)
    """
    
    def run_async(self, coro):
        """运行异步协程"""
        return asyncio.run(coro)
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
