"""
技能模块统一入口 - 将大型 skills.py 重构为模块化结构

此模块重新组织 legacy_skills.py 中的技能，按功能分类：
- test_skills: 测试技能
- file_skills: 文件处理技能
- evolution_skills: 自我进化技能  
- security_skills: 代码安全技能
"""

# 从遗留技能文件导入所有函数
from .legacy_skills import (
    # 测试技能
    test_adder,
    test_multiply,
    test_concat,
    # 文件处理
    read_large_file,
    # 自我进化
    generate_next_self_improvement_goal,
    collect_runtime_operation_data,
    identify_evolution_problems,
    generate_iteration_plan,
    autonomous_iteration_pipeline,
    self_reference_recognition,
    run_self_optimization_cycle,
    iteration_cycle_optimization_manager,
    # 代码安全
    code_security_verification,
    grayscale_test_executor,
    deployment_rollback_manager,
    generation_content_compliance_check,
    project_compliance_auto_check,
    # 其他
    run_test_suite,
)

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
