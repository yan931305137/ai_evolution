
from typing import Dict, Any, Type, Callable, Optional
import threading

class Container:
    """
    一个简单的依赖注入容器 (IoC Container)
    用于管理单例和依赖关系，解耦全局状态
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Container, cls).__new__(cls)
                    cls._instance._registry = {}
                    cls._instance._instances = {}
        return cls._instance

    def register(self, key: Type, provider: Callable[[], Any], scope: str = "singleton"):
        """
        注册依赖提供者
        :param key: 依赖的标识（通常是类或接口）
        :param provider: 创建依赖实例的工厂函数
        :param scope: 生命周期 ("singleton" 或 "transient")
        """
        self._registry[key] = {"provider": provider, "scope": scope}

    def resolve(self, key: Type) -> Any:
        """
        解析并获取依赖实例
        :param key: 依赖的标识
        :return: 依赖实例
        """
        if key not in self._registry:
            raise KeyError(f"No provider registered for {key}")

        spec = self._registry[key]
        
        if spec["scope"] == "singleton":
            if key not in self._instances:
                with self._lock:
                    if key not in self._instances:
                        self._instances[key] = spec["provider"]()
            return self._instances[key]
        else:
            return spec["provider"]()

    def reset(self):
        """重置容器（主要用于测试）"""
        with self._lock:
            self._registry.clear()
            self._instances.clear()

# 全局容器实例
container = Container()
