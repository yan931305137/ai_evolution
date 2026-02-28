"""
热重载启动模块 - 启用并管理系统的热更新功能

功能：
1. 注册核心模块到热重载管理器
2. 启动后台线程监听文件变更
3. 自动重载变更的模块
4. 提供启动/停止控制接口
"""

import os
import sys
import time
import threading
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# 热重载管理器实例
_hot_reload_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def register_core_modules():
    """注册核心模块到热重载管理器"""
    from src.utils.hot_reload_manager import hot_reload_manager
    
    registered = []
    
    # 1. 注册 Agent 模块
    try:
        from src.agents.agent import AutoAgent
        from src.utils.llm import LLMClient
        agent = AutoAgent(LLMClient())
        if hot_reload_manager.register_module("src.agents.agent", agent):
            registered.append("src.agents.agent")
    except Exception as e:
        logger.warning(f"注册 agent 模块失败: {e}")
    
    # 2. 注册工具模块
    try:
        from src.tools import Tools
        if hot_reload_manager.register_module("src.tools", Tools):
            registered.append("src.tools")
    except Exception as e:
        logger.warning(f"注册 tools 模块失败: {e}")
    
    # 3. 注册技能模块
    try:
        from src import skills
        if hot_reload_manager.register_module("src.skills", skills):
            registered.append("src.skills")
    except Exception as e:
        logger.warning(f"注册 skills 模块失败: {e}")
    
    # 4. 注册存储模块
    try:
        from src.storage.memory import MemorySystem
        memory = MemorySystem()
        if hot_reload_manager.register_module("src.storage.memory", memory):
            registered.append("src.storage.memory")
    except Exception as e:
        logger.warning(f"注册 memory 模块失败: {e}")
    
    # 5. 注册业务模块
    try:
        from src.business.source_manager import SourceManager
        sm = SourceManager()
        if hot_reload_manager.register_module("src.business.source_manager", sm):
            registered.append("src.business.source_manager")
    except Exception as e:
        logger.warning(f"注册 source_manager 模块失败: {e}")
    
    logger.info(f"已注册 {len(registered)} 个模块到热重载管理器: {registered}")
    return registered


def _watch_loop(check_interval: float = 2.0):
    """
    文件监听循环（在后台线程中运行）
    
    Args:
        check_interval: 检查文件变更的间隔时间（秒）
    """
    from src.utils.hot_reload_manager import hot_reload_manager
    
    logger.info(f"热重载监听线程启动，检查间隔: {check_interval}秒")
    
    while not _stop_event.is_set():
        try:
            # 检查文件变更
            changed_modules = hot_reload_manager.check_module_changes()
            
            for module_name in changed_modules:
                logger.info(f"检测到模块变更: {module_name}")
                
                # 执行热重载
                success, msg = hot_reload_manager.reload_module(module_name)
                
                if success:
                    logger.info(f"✅ {msg}")
                else:
                    logger.error(f"❌ {msg}")
            
            # 等待下一次检查
            _stop_event.wait(check_interval)
            
        except Exception as e:
            logger.error(f"热重载监听循环出错: {e}", exc_info=True)
            time.sleep(check_interval)
    
    logger.info("热重载监听线程已停止")


def start_hot_reload(check_interval: float = 2.0) -> bool:
    """
    启动热重载功能
    
    Args:
        check_interval: 检查文件变更的间隔时间（秒）
    
    Returns:
        是否成功启动
    """
    global _hot_reload_thread
    
    if _hot_reload_thread and _hot_reload_thread.is_alive():
        logger.warning("热重载功能已经在运行")
        return False
    
    # 注册核心模块
    registered = register_core_modules()
    
    if not registered:
        logger.warning("没有模块被注册，热重载功能未启动")
        return False
    
    # 重置停止事件
    _stop_event.clear()
    
    # 启动监听线程
    _hot_reload_thread = threading.Thread(
        target=_watch_loop,
        args=(check_interval,),
        name="HotReloadWatcher",
        daemon=True  # 作为守护线程，主程序退出时自动结束
    )
    _hot_reload_thread.start()
    
    logger.info(f"✅ 热重载功能已启动，监听 {len(registered)} 个模块")
    return True


def stop_hot_reload():
    """停止热重载功能"""
    global _hot_reload_thread
    
    if not _hot_reload_thread or not _hot_reload_thread.is_alive():
        logger.warning("热重载功能未运行")
        return
    
    # 设置停止事件
    _stop_event.set()
    
    # 等待线程结束
    _hot_reload_thread.join(timeout=5.0)
    
    if _hot_reload_thread.is_alive():
        logger.warning("热重载线程未能在5秒内结束")
    else:
        logger.info("✅ 热重载功能已停止")
    
    _hot_reload_thread = None


def get_hot_reload_status() -> dict:
    """获取热重载状态信息"""
    from src.utils.hot_reload_manager import hot_reload_manager
    
    is_running = _hot_reload_thread is not None and _hot_reload_thread.is_alive()
    
    return {
        "running": is_running,
        "registered_modules": list(hot_reload_manager.module_registry.keys()),
        "module_count": len(hot_reload_manager.module_registry),
        "reload_success_count": hot_reload_manager.reload_success_count,
        "reload_fail_count": hot_reload_manager.reload_fail_count,
        "last_reload_time": hot_reload_manager.last_reload_time,
        "performance_gain": hot_reload_manager.get_reload_performance() if hasattr(hot_reload_manager, 'get_reload_performance') else None
    }


# 便捷的启动/停止函数
def enable():
    """启用热重载（简写）"""
    return start_hot_reload()


def disable():
    """禁用热重载（简写）"""
    return stop_hot_reload()


def status():
    """获取状态（简写）"""
    return get_hot_reload_status()
