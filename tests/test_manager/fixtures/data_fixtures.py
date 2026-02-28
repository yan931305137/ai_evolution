"""
通用数据 Fixtures

提供测试数据目录、mock 工厂等通用 fixtures
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def test_data_dir():
    """
    测试数据目录
    
    返回测试数据根目录，如果不存在则创建
    """
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def test_temp_dir():
    """
    会话级临时目录
    
    在整个测试会话期间保持的临时目录
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="openclaw_test_"))
    yield temp_dir
    # 清理
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_file_factory():
    """
    临时文件工厂
    
    使用示例:
        def test_something(temp_file_factory):
            file_path = temp_file_factory.create("内容", ".py")
            # 使用 file_path 进行测试
    """
    class TempFileFactory:
        def __init__(self):
            self._files = []
        
        def create(self, content: str = "", suffix: str = ".txt") -> Path:
            """创建临时文件"""
            fd, path = tempfile.mkstemp(suffix=suffix)
            Path(path).write_text(content, encoding='utf-8')
            self._files.append(Path(path))
            return Path(path)
        
        def create_json(self, data: dict) -> Path:
            """创建 JSON 临时文件"""
            return self.create(json.dumps(data, ensure_ascii=False), ".json")
        
        def cleanup(self):
            """清理所有临时文件"""
            for f in self._files:
                if f.exists():
                    f.unlink()
    
    factory = TempFileFactory()
    yield factory
    factory.cleanup()


@pytest.fixture
def mock_llm_client():
    """
    Mock LLM 客户端
    
    返回配置好的 Mock LLM 客户端
    """
    mock = MagicMock()
    mock.complete = MagicMock(return_value="Mock LLM 响应")
    mock.chat = MagicMock(return_value={"role": "assistant", "content": "Mock 回复"})
    mock.embed = MagicMock(return_value=[0.1] * 384)
    return mock


@pytest.fixture
def mock_config():
    """
    Mock 配置
    
    返回标准测试配置
    """
    return {
        "model": {
            "provider": "mock",
            "model_name": "test-model",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "memory": {
            "provider": "memory_only",
            "embedding_model": "simple"
        },
        "max_steps": 5,
        "timeout": 30,
        "debug": True
    }


@pytest.fixture
def sample_text_data():
    """示例文本数据"""
    return {
        "short": "简短文本",
        "medium": "这是一段中等长度的文本，用于测试文本处理功能。",
        "long": "这是一段很长的文本。" * 50,
        "chinese": "中文测试文本，包含一些中文特性。",
        "english": "This is an English test text with some special characters: @#$%",
        "mixed": "中英文混合 text with 一些中文 and English."
    }


@pytest.fixture
def sample_code_data():
    """示例代码数据"""
    return {
        "python_simple": "def hello():\n    print('Hello')",
        "python_class": """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
""",
        "javascript": "function greet(name) {\n    return `Hello, ${name}!`;\n}",
        "html": "<!DOCTYPE html><html><body><h1>Test</h1></body></html>",
        "json": '{"name": "test", "value": 123}'
    }


@pytest.fixture
def error_scenarios():
    """常见错误场景"""
    return {
        "file_not_found": {"error": "FileNotFoundError", "message": "文件不存在"},
        "permission_denied": {"error": "PermissionError", "message": "权限不足"},
        "timeout": {"error": "TimeoutError", "message": "操作超时"},
        "invalid_input": {"error": "ValueError", "message": "无效输入"},
        "network_error": {"error": "ConnectionError", "message": "网络连接失败"}
    }
