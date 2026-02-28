"""
技能模块 Fixtures

提供各种技能的测试实例
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def code_generation_skill():
    """代码生成技能 fixture"""
    try:
        from src.skills.evolution_skills import CodeGenerationSkill
        return CodeGenerationSkill()
    except ImportError:
        mock = MagicMock()
        mock.generate = MagicMock(return_value="def generated(): pass")
        return mock


@pytest.fixture
def web_search_skill():
    """Web 搜索技能 fixture"""
    try:
        from src.skills.web_search_skill import WebSearchSkill
        return WebSearchSkill()
    except ImportError:
        mock = MagicMock()
        mock.search = MagicMock(return_value=[{"title": "结果", "snippet": "内容"}])
        return mock


@pytest.fixture
def analysis_skill():
    """分析技能 fixture"""
    try:
        from src.skills.analysis_skill import AnalysisSkill
        return AnalysisSkill()
    except ImportError:
        mock = MagicMock()
        mock.analyze = MagicMock(return_value={"sentiment": "positive", "keywords": ["test"]})
        return mock


@pytest.fixture
def file_operation_skill():
    """文件操作技能 fixture"""
    try:
        from src.skills.file_skills import FileOperationSkill
        return FileOperationSkill()
    except ImportError:
        mock = MagicMock()
        mock.read = MagicMock(return_value="文件内容")
        mock.write = MagicMock(return_value={"success": True})
        return mock


@pytest.fixture
def evolution_skill():
    """进化技能 fixture"""
    try:
        from src.skills.evolution_skills import EvolutionSkill
        return EvolutionSkill()
    except ImportError:
        mock = MagicMock()
        mock.evaluate_idea = MagicMock(return_value={"score": 0.85, "should_apply": True})
        mock.generate_idea = MagicMock(return_value={"idea": "新想法", "confidence": 0.9})
        return mock


@pytest.fixture
def business_skill():
    """业务技能 fixture"""
    try:
        from src.skills.business_skills import BusinessSkill
        return BusinessSkill()
    except ImportError:
        mock = MagicMock()
        mock.analyze_requirement = MagicMock(return_value={"complexity": "medium", "estimate": 5})
        return mock


@pytest.fixture
def security_skill():
    """安全技能 fixture"""
    try:
        from src.skills.security_skills import SecuritySkill
        return SecuritySkill()
    except ImportError:
        mock = MagicMock()
        mock.scan_code = MagicMock(return_value={"vulnerabilities": []})
        mock.check_compliance = MagicMock(return_value={"passed": True})
        return mock


# ==================== 技能测试数据 ====================

@pytest.fixture
def skill_input_data():
    """技能输入数据"""
    return {
        "prompt": "测试提示",
        "context": {"user": "test", "session": "123"},
        "parameters": {"temperature": 0.7}
    }


@pytest.fixture
def skill_output_schema():
    """技能输出模式"""
    return {
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "confidence": {"type": "number"},
            "metadata": {"type": "object"}
        },
        "required": ["result"]
    }
