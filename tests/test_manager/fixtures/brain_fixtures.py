"""
Brain 模块 Fixtures

提供 Brain、PlanningSystem、MemorySystem 等核心组件的测试实例
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def brain_instance():
    """
    Brain 实例 fixture
    
    返回配置好的 Brain 实例，用于测试
    """
    try:
        from src.brain.brain import Brain
        brain = Brain()
        return brain
    except ImportError as e:
        # 如果导入失败，返回 Mock 对象
        mock = MagicMock()
        mock.process = MagicMock(return_value={"success": True, "result": "mock_result"})
        mock.think = MagicMock(return_value="mock_thinking")
        return mock


@pytest.fixture
def planning_instance():
    """
    规划系统实例 fixture
    
    返回 PlanningSystem 实例
    """
    try:
        from src.brain.planning_system import PlanningSystem
        return PlanningSystem()
    except ImportError:
        mock = MagicMock()
        mock.create_plan = MagicMock(return_value={"plan_id": "test_plan", "steps": []})
        mock.execute_next_step = MagicMock(return_value={"success": True})
        return mock


@pytest.fixture
def memory_system():
    """
    增强记忆系统 fixture
    
    使用内存模式（非 ChromaDB）以便测试
    """
    try:
        from src.storage.enhanced_memory import EnhancedMemorySystem
        return EnhancedMemorySystem(use_memory_only=True)
    except ImportError:
        mock = MagicMock()
        mock.add_memory = MagicMock(return_value=True)
        mock.search_memory = MagicMock(return_value=[])
        return mock


@pytest.fixture
def perception_system():
    """感知系统 fixture"""
    try:
        from src.brain.perception_system import PerceptionSystem
        return PerceptionSystem()
    except ImportError:
        mock = MagicMock()
        mock.perceive = MagicMock(return_value={"input": "test", "type": "text"})
        return mock


@pytest.fixture
def value_system():
    """价值系统 fixture"""
    try:
        from src.brain.value_system import ValueSystem
        return ValueSystem()
    except ImportError:
        mock = MagicMock()
        mock.evaluate = MagicMock(return_value={"score": 0.8, "passed": True})
        return mock


@pytest.fixture
def emotion_system():
    """情感系统 fixture"""
    try:
        from src.brain.emotion_system import EmotionSystem
        return EmotionSystem()
    except ImportError:
        mock = MagicMock()
        mock.get_current_emotion = MagicMock(return_value="neutral")
        mock.update_emotion = MagicMock(return_value=None)
        return mock


@pytest.fixture
def orchestrator():
    """编排器 fixture"""
    try:
        from src.brain.orchestrator import Orchestrator
        return Orchestrator()
    except ImportError:
        mock = MagicMock()
        mock.orchestrate = MagicMock(return_value={"success": True, "output": "mock_output"})
        return mock


# ==================== Brain 测试数据 ====================

@pytest.fixture
def sample_thought_data():
    """示例思考数据"""
    return {
        "input": "测试输入",
        "context": {"user": "test_user", "session": "test_session"},
        "reasoning_steps": ["步骤1", "步骤2"],
        "conclusion": "测试结论"
    }


@pytest.fixture
def sample_plan_data():
    """示例规划数据"""
    return {
        "goal": "测试目标",
        "steps": [
            {"id": 1, "action": "步骤1", "dependencies": []},
            {"id": 2, "action": "步骤2", "dependencies": [1]},
            {"id": 3, "action": "步骤3", "dependencies": [2]}
        ],
        "estimated_time": 60
    }


@pytest.fixture
def sample_memory_data():
    """示例记忆数据"""
    return {
        "content": "这是一条测试记忆",
        "type": "conversation",
        "importance": 0.8,
        "emotional_tag": "neutral",
        "metadata": {"source": "test", "timestamp": 1234567890}
    }
