"""
断言工具

提供自定义断言方法
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class AssertHelper:
    """断言辅助类"""
    
    @staticmethod
    def is_valid_json(data: Union[str, bytes]) -> bool:
        """检查是否为有效 JSON"""
        try:
            json.loads(data)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def contains_all(container: str, items: List[str]) -> bool:
        """检查字符串是否包含所有指定子串"""
        return all(item in container for item in items)
    
    @staticmethod
    def contains_any(container: str, items: List[str]) -> bool:
        """检查字符串是否包含任意指定子串"""
        return any(item in container for item in items)
    
    @staticmethod
    def matches_pattern(text: str, pattern: str) -> bool:
        """检查文本是否匹配正则表达式"""
        return bool(re.search(pattern, text))
    
    @staticmethod
    def has_keys(d: Dict, keys: List[str]) -> bool:
        """检查字典是否包含所有指定键"""
        return all(key in d for key in keys)
    
    @staticmethod
    def has_nested_key(d: Dict, key_path: str, separator: str = ".") -> bool:
        """
        检查字典是否包含嵌套键
        
        Args:
            d: 字典
            key_path: 键路径，如 "user.name"
            separator: 分隔符
        """
        keys = key_path.split(separator)
        current = d
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True
    
    @staticmethod
    def is_subset(subset: Dict, superset: Dict) -> bool:
        """检查 subset 是否是 superset 的子集"""
        for key, value in subset.items():
            if key not in superset:
                return False
            if isinstance(value, dict) and isinstance(superset[key], dict):
                if not AssertHelper.is_subset(value, superset[key]):
                    return False
            elif superset[key] != value:
                return False
        return True


class CustomAssertions:
    """
    自定义断言（用于 pytest）
    
    使用示例:
        from tests.test_manager.helpers.assert_utils import CustomAssertions
        
        def test_something():
            CustomAssertions.assertValidJson('{"key": "value"}')
            CustomAssertions.assertContainsAll("hello world", ["hello", "world"])
    """
    
    @staticmethod
    def assertValidJson(data: Union[str, bytes], msg: Optional[str] = None):
        """断言有效 JSON"""
        assert AssertHelper.is_valid_json(data), msg or "无效的 JSON 格式"
    
    @staticmethod
    def assertContainsAll(container: str, items: List[str], msg: Optional[str] = None):
        """断言包含所有子串"""
        missing = [item for item in items if item not in container]
        assert not missing, msg or f"缺少: {missing}"
    
    @staticmethod
    def assertContainsAny(container: str, items: List[str], msg: Optional[str] = None):
        """断言包含任意子串"""
        assert AssertHelper.contains_any(container, items), msg or f"不包含任何: {items}"
    
    @staticmethod
    def assertMatchesPattern(text: str, pattern: str, msg: Optional[str] = None):
        """断言匹配正则"""
        assert AssertHelper.matches_pattern(text, pattern), msg or f"不匹配模式: {pattern}"
    
    @staticmethod
    def assertHasKeys(d: Dict, keys: List[str], msg: Optional[str] = None):
        """断言字典包含键"""
        missing = [key for key in keys if key not in d]
        assert not missing, msg or f"缺少键: {missing}"
    
    @staticmethod
    def assertHasNestedKey(d: Dict, key_path: str, separator: str = ".", msg: Optional[str] = None):
        """断言包含嵌套键"""
        assert AssertHelper.has_nested_key(d, key_path, separator), msg or f"缺少嵌套键: {key_path}"
    
    @staticmethod
    def assertIsSubset(subset: Dict, superset: Dict, msg: Optional[str] = None):
        """断言子集关系"""
        assert AssertHelper.is_subset(subset, superset), msg or "不是子集关系"
    
    @staticmethod
    def assertFileExists(path: Union[str, Path], msg: Optional[str] = None):
        """断言文件存在"""
        path = Path(path)
        assert path.exists(), msg or f"文件不存在: {path}"
    
    @staticmethod
    def assertFileContains(path: Union[str, Path], content: str, msg: Optional[str] = None):
        """断言文件包含内容"""
        path = Path(path)
        AssertHelper.assertFileExists(path)
        file_content = path.read_text(encoding='utf-8')
        assert content in file_content, msg or f"文件不包含: {content}"
    
    @staticmethod
    def assertSuccess(result: Union[Dict, Any], msg: Optional[str] = None):
        """断言操作成功"""
        if isinstance(result, dict):
            assert result.get('success', False), msg or f"操作失败: {result}"
        elif hasattr(result, 'success'):
            assert result.success, msg or "操作失败"
        else:
            assert bool(result), msg or "结果为假值"
    
    @staticmethod
    def assertFailure(result: Union[Dict, Any], msg: Optional[str] = None):
        """断言操作失败"""
        if isinstance(result, dict):
            assert not result.get('success', True), msg or "操作应该失败"
        elif hasattr(result, 'success'):
            assert not result.success, msg or "操作应该失败"
        else:
            assert not bool(result), msg or "结果应该为假值"
    
    @staticmethod
    def assertInRange(value: Union[int, float], min_val: Union[int, float], 
                      max_val: Union[int, float], msg: Optional[str] = None):
        """断言值在范围内"""
        assert min_val <= value <= max_val, msg or f"{value} 不在 [{min_val}, {max_val}] 范围内"
    
    @staticmethod
    def assertIsPositiveInteger(value: Any, msg: Optional[str] = None):
        """断言是正整数"""
        assert isinstance(value, int) and value > 0, msg or f"{value} 不是正整数"
    
    @staticmethod
    def assertValidEmail(email: str, msg: Optional[str] = None):
        """断言有效邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(pattern, email), msg or f"无效邮箱: {email}"
    
    @staticmethod
    def assertValidURL(url: str, msg: Optional[str] = None):
        """断言有效 URL"""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        assert re.match(pattern, url), msg or f"无效 URL: {url}"
