"""
工具模块 Fixtures

提供各种工具的测试实例
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def file_tool():
    """文件工具 fixture"""
    try:
        from src.tools.file_tools import FileTools
        return FileTools()
    except ImportError:
        mock = MagicMock()
        mock.read_file = MagicMock(return_value="文件内容")
        mock.write_file = MagicMock(return_value={"success": True})
        return mock


@pytest.fixture
def code_tool():
    """代码工具 fixture"""
    try:
        from src.tools.code_tools import CodeTools
        return CodeTools()
    except ImportError:
        mock = MagicMock()
        mock.generate_code = MagicMock(return_value="def test(): pass")
        mock.review_code = MagicMock(return_value={"issues": []})
        return mock


@pytest.fixture
def git_tool():
    """Git 工具 fixture"""
    try:
        from src.tools.git_tools import GitTools
        return GitTools()
    except ImportError:
        mock = MagicMock()
        mock.git_commit = MagicMock(return_value={"success": True, "commit_id": "abc123"})
        mock.git_status = MagicMock(return_value={"modified": [], "untracked": []})
        return mock


@pytest.fixture
def web_tool():
    """Web 工具 fixture"""
    try:
        from src.tools.web_tools import WebTools
        return WebTools()
    except ImportError:
        mock = MagicMock()
        mock.web_search = MagicMock(return_value=[{"title": "测试", "url": "http://test.com"}])
        mock.fetch_url = MagicMock(return_value="<html>测试页面</html>")
        return mock


@pytest.fixture
def directory_tool():
    """目录工具 fixture"""
    try:
        from src.tools.directory_tools import DirectoryTools
        return DirectoryTools()
    except ImportError:
        mock = MagicMock()
        mock.list_directory = MagicMock(return_value=["file1.txt", "file2.py"])
        mock.create_directory = MagicMock(return_value={"success": True})
        return mock


@pytest.fixture
def shell_tool():
    """Shell 工具 fixture"""
    try:
        from src.tools.system_tools import SystemTools
        return SystemTools()
    except ImportError:
        mock = MagicMock()
        mock.run_command = MagicMock(return_value={"stdout": "output", "stderr": "", "returncode": 0})
        return mock


@pytest.fixture
def json_tool():
    """JSON 工具 fixture"""
    try:
        from src.tools.json_yaml_tools import JSONYamlTools
        return JSONYamlTools()
    except ImportError:
        mock = MagicMock()
        mock.validate_json = MagicMock(return_value={"valid": True})
        mock.format_json = MagicMock(return_value='{\n  "key": "value"\n}')
        return mock


@pytest.fixture
def security_tool():
    """安全工具 fixture"""
    try:
        from src.tools.security_tools import SecurityTools
        return SecurityTools()
    except ImportError:
        mock = MagicMock()
        mock.scan_secrets = MagicMock(return_value={"secrets_found": []})
        mock.validate_input = MagicMock(return_value={"safe": True})
        return mock


@pytest.fixture
def text_tool():
    """文本处理工具 fixture"""
    try:
        from src.tools.text_processing_tools import TextProcessingTools
        return TextProcessingTools()
    except ImportError:
        mock = MagicMock()
        mock.summarize = MagicMock(return_value="摘要内容")
        mock.translate = MagicMock(return_value="Translated text")
        return mock
