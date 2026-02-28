"""
技能模块统一入口 - 按功能分类管理所有技能

结构:
├── __init__.py          # 统一入口 (当前文件)
├── test_skills.py       # 测试技能 (3个)
├── file_skills.py       # 文件处理 (1个)
├── evolution_skills.py  # 自我进化 (8个)
└── security_skills.py   # 代码安全 (5个)

总计: 17个技能
"""

# 从各模块导入技能
from .test_skills import test_adder, test_multiply, test_concat
from .file_skills import read_large_file
from .evolution_skills import (
    generate_next_self_improvement_goal,
    collect_runtime_operation_data,
    identify_evolution_problems,
    generate_iteration_plan,
    autonomous_iteration_pipeline,
    self_reference_recognition,
    run_self_optimization_cycle,
    iteration_cycle_optimization_manager,
)
from .security_skills import (
    code_security_verification,
    grayscale_test_executor,
    deployment_rollback_manager,
    generation_content_compliance_check,
    project_compliance_auto_check,
)

# 兼容 legacy_skills.py 中的其他技能
from .legacy_skills import run_test_suite

__all__ = [
    # 测试技能 (3个)
    'test_adder', 'test_multiply', 'test_concat',
    # 文件处理 (1个)
    'read_large_file',
    # 自我进化 (8个)
    'generate_next_self_improvement_goal',
    'collect_runtime_operation_data',
    'identify_evolution_problems',
    'generate_iteration_plan',
    'autonomous_iteration_pipeline',
    'self_reference_recognition',
    'run_self_optimization_cycle',
    'iteration_cycle_optimization_manager',
    # 代码安全 (5个)
    'code_security_verification',
    'grayscale_test_executor',
    'deployment_rollback_manager',
    'generation_content_compliance_check',
    'project_compliance_auto_check',
    # 其他 (1个)
    'run_test_suite',
]

# 定义导出的技能列表
__all__ = [
    # 测试技能
    'test_adder',
    'test_multiply', 
    'test_concat',
    # 文件处理
    'read_large_file',
    # 自我进化
    'generate_next_self_improvement_goal',
    'collect_runtime_operation_data',
    'identify_evolution_problems',
    'generate_iteration_plan',
    'autonomous_iteration_pipeline',
    'self_reference_recognition',
    'run_self_optimization_cycle',
    'iteration_cycle_optimization_manager',
    # 代码安全
    'code_security_verification',
    'grayscale_test_executor',
    'deployment_rollback_manager',
    'generation_content_compliance_check',
    'project_compliance_auto_check',
    # 其他
    'run_test_suite',
]
