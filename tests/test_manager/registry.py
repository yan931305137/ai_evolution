"""
测试注册中心

管理所有测试用例的分类、统计和发现
"""

import inspect
from typing import Dict, List, Set, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import functools


class Category(Enum):
    """测试类别枚举"""
    UNIT = "unit"                    # 单元测试
    INTEGRATION = "integration"      # 集成测试
    E2E = "e2e"                      # 端到端测试
    PERFORMANCE = "performance"      # 性能测试
    SECURITY = "security"            # 安全测试
    REGRESSION = "regression"        # 回归测试


class Priority(Enum):
    """测试优先级"""
    P0 = "p0"    # 阻塞级，必须100%通过
    P1 = "p1"    # 重要，必须95%通过
    P2 = "p2"    # 一般，必须90%通过
    P3 = "p3"    # 可选，建议80%通过


# 向后兼容的别名
TestCategory = Category
TestPriority = Priority


@dataclass
class TestInfo:
    """测试信息数据类"""
    name: str
    category: Category
    priority: Priority
    module: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    estimated_duration: float = 1.0  # 估计执行时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "category": self.category.value,
            "priority": self.priority.value,
            "module": self.module,
            "description": self.description,
            "dependencies": self.dependencies,
            "tags": list(self.tags),
            "estimated_duration": self.estimated_duration
        }


# 装饰器，用于标记测试类别和优先级
def test_category(
    category: Category,
    priority: Priority = Priority.P2,
    description: str = "",
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    estimated_duration: float = 1.0
):
    """
    测试类别装饰器
    
    用于标记测试函数的类别、优先级等信息
    
    使用示例:
        @test_category(Category.UNIT, Priority.P0, "核心功能测试")
        def test_core_feature():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # 存储测试元数据
        func._test_info = TestInfo(
            name=func.__name__,
            category=category,
            priority=priority,
            module=func.__module__,
            description=description or func.__doc__ or "",
            dependencies=dependencies or [],
            tags=set(tags or []),
            estimated_duration=estimated_duration
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 复制元数据
        wrapper._test_info = func._test_info
        return wrapper
    
    return decorator


# 快捷装饰器
def unit_test(priority: Priority = Priority.P2, **kwargs):
    """单元测试装饰器"""
    return test_category(Category.UNIT, priority, **kwargs)

def integration_test(priority: Priority = Priority.P1, **kwargs):
    """集成测试装饰器"""
    return test_category(Category.INTEGRATION, priority, **kwargs)

def e2e_test(priority: Priority = Priority.P1, **kwargs):
    """端到端测试装饰器"""
    return test_category(Category.E2E, priority, **kwargs)

def performance_test(priority: Priority = Priority.P2, **kwargs):
    """性能测试装饰器"""
    return test_category(Category.PERFORMANCE, priority, **kwargs)


class TestRegistry:
    """
    测试注册中心
    
    管理所有已注册的测试用例
    
    使用示例:
        # 在 conftest.py 中自动发现
        registry = TestRegistry()
        registry.auto_discover()
        
        # 获取统计信息
        stats = registry.get_statistics()
        print(f"总测试数: {stats['total']}")
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tests: Dict[str, TestInfo] = {}
        return cls._instance
    
    def register(self, test_info: TestInfo):
        """注册测试"""
        self._tests[test_info.name] = test_info
    
    def get_test(self, name: str) -> Optional[TestInfo]:
        """获取测试信息"""
        return self._tests.get(name)
    
    def get_all_tests(self) -> List[TestInfo]:
        """获取所有测试"""
        return list(self._tests.values())
    
    def get_by_category(self, category: Category) -> List[TestInfo]:
        """按类别获取测试"""
        return [t for t in self._tests.values() if t.category == category]
    
    def get_by_priority(self, priority: Priority) -> List[TestInfo]:
        """按优先级获取测试"""
        return [t for t in self._tests.values() if t.priority == priority]
    
    def get_by_tag(self, tag: str) -> List[TestInfo]:
        """按标签获取测试"""
        return [t for t in self._tests.values() if tag in t.tags]
    
    def get_by_module(self, module: str) -> List[TestInfo]:
        """按模块获取测试"""
        return [t for t in self._tests.values() if t.module == module]
    
    def auto_discover(self, test_modules: Optional[List[str]] = None):
        """
        自动发现测试
        
        Args:
            test_modules: 要扫描的测试模块列表，如果为 None 则扫描所有测试文件
        """
        import sys
        import importlib
        
        if test_modules is None:
            # 默认扫描 tests 目录下的所有测试文件
            test_modules = [
                "tests.code_generation.test_code_generation_cases",
                "tests.information_retrieval.test_retrieval_cases",
                "tests.multi_step_planning.test_planning_cases",
                "tests.planning.test_multi_step_planning",
            ]
        
        for module_name in test_modules:
            try:
                module = importlib.import_module(module_name)
                self._scan_module(module)
            except ImportError:
                pass
    
    def _scan_module(self, module):
        """扫描模块中的测试函数"""
        for name, obj in inspect.getmembers(module):
            # 检查是否是测试函数
            if name.startswith("test_") and callable(obj):
                # 检查是否已有测试信息
                if hasattr(obj, '_test_info'):
                    self.register(obj._test_info)
                else:
                    # 创建默认测试信息
                    info = TestInfo(
                        name=name,
                        category=Category.UNIT,
                        priority=Priority.P2,
                        module=module.__name__,
                        description=obj.__doc__ or ""
                    )
                    self.register(info)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        tests = self.get_all_tests()
        
        return {
            "total": len(tests),
            "by_category": {
                cat.value: len(self.get_by_category(cat))
                for cat in Category
            },
            "by_priority": {
                pri.value: len(self.get_by_priority(pri))
                for pri in Priority
            },
            "estimated_total_duration": sum(t.estimated_duration for t in tests),
            "modules": len(set(t.module for t in tests)),
            "all_tags": list(set(
                tag for t in tests for tag in t.tags
            ))
        }
    
    def generate_report(self, output_path: str = "test_report.json"):
        """
        生成测试报告
        
        Args:
            output_path: 输出路径
        """
        import json
        
        report = {
            "statistics": self.get_statistics(),
            "tests": [t.to_dict() for t in self.get_all_tests()]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def get_test_plan(self, 
                     categories: Optional[List[Category]] = None,
                     min_priority: Priority = Priority.P3) -> List[TestInfo]:
        """
        获取测试计划
        
        根据类别和优先级筛选测试
        
        Args:
            categories: 指定类别，None 表示全部
            min_priority: 最低优先级
        
        Returns:
            测试列表
        """
        tests = self.get_all_tests()
        
        if categories:
            tests = [t for t in tests if t.category in categories]
        
        # 按优先级过滤
        priority_order = {p: i for i, p in enumerate(Priority)}
        min_priority_order = priority_order[min_priority]
        tests = [t for t in tests if priority_order[t.priority] <= min_priority_order]
        
        # 按优先级和类别排序
        tests.sort(key=lambda t: (priority_order[t.priority], t.category.value))
        
        return tests


# 全局注册中心实例
registry = TestRegistry()
