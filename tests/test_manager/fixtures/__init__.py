"""
Fixtures 模块

统一导出所有 fixtures，方便在 conftest.py 中导入
"""

# Brain fixtures
from .brain_fixtures import (
    brain_instance,
    planning_instance,
    memory_system,
    perception_system,
    value_system,
    emotion_system,
    orchestrator,
    sample_thought_data,
    sample_plan_data,
    sample_memory_data,
)

# Tool fixtures
from .tool_fixtures import (
    file_tool,
    code_tool,
    git_tool,
    web_tool,
    directory_tool,
    shell_tool,
    json_tool,
    security_tool,
    text_tool,
)

# Skill fixtures
from .skill_fixtures import (
    code_generation_skill,
    web_search_skill,
    analysis_skill,
    file_operation_skill,
    evolution_skill,
    business_skill,
    security_skill,
    skill_input_data,
    skill_output_schema,
)

# Data fixtures
from .data_fixtures import (
    test_data_dir,
    test_temp_dir,
    temp_file_factory,
    mock_llm_client,
    mock_config,
    sample_text_data,
    sample_code_data,
    error_scenarios,
)

__all__ = [
    # Brain
    'brain_instance',
    'planning_instance',
    'memory_system',
    'perception_system',
    'value_system',
    'emotion_system',
    'orchestrator',
    'sample_thought_data',
    'sample_plan_data',
    'sample_memory_data',
    # Tools
    'file_tool',
    'code_tool',
    'git_tool',
    'web_tool',
    'directory_tool',
    'shell_tool',
    'json_tool',
    'security_tool',
    'text_tool',
    # Skills
    'code_generation_skill',
    'web_search_skill',
    'analysis_skill',
    'file_operation_skill',
    'evolution_skill',
    'business_skill',
    'security_skill',
    'skill_input_data',
    'skill_output_schema',
    # Data
    'test_data_dir',
    'test_temp_dir',
    'temp_file_factory',
    'mock_llm_client',
    'mock_config',
    'sample_text_data',
    'sample_code_data',
    'error_scenarios',
]
