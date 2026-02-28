import pytest
from src.brain.planning_system import PlanningSystem, StepStatus


@pytest.fixture(scope="module")
def planner_instance():
    """测试前置：初始化 PlanningSystem 实例，所有测试用例共享"""
    return PlanningSystem()


def test_planner_initialization(planner_instance):
    """测试用例1：规划器初始化功能验证"""
    assert planner_instance is not None
    assert planner_instance.current_plan is None
    assert len(planner_instance.plan_history) == 0


def test_simple_task_decomposition(planner_instance):
    """测试用例2：简单任务分解功能验证"""
    goal = "读取当前目录下的README.md文件内容"
    plan = planner_instance.generate_plan(goal)
    assert plan is not None
    assert len(plan.steps) >= 2
    assert plan.goal == goal


def test_plan_progress_calculation(planner_instance):
    """测试用例3：计划进度计算功能验证"""
    goal = "测试进度计算功能"
    plan = planner_instance.generate_plan(goal)
    # 初始进度
    assert plan.get_progress() >= 0.0
    # 执行第一个步骤
    if plan.steps:
        planner_instance.execute_step(plan.steps[0].id)
        expected_progress = 100.0 / len(plan.steps)
        assert plan.get_progress() == expected_progress


def test_next_executable_task(planner_instance):
    """测试用例4：获取下一个可执行子任务功能验证"""
    goal = "测试依赖调度功能"
    plan = planner_instance.generate_plan(goal)
    # 第一个任务没有依赖，应该是第一个可执行任务
    next_step = plan.get_next_pending_step()
    assert next_step is not None
    assert next_step.status == StepStatus.PENDING


def test_task_template_matching(planner_instance):
    """测试用例5：任务模板匹配功能验证"""
    # 测试文件操作类任务匹配
    file_goal = "修改src目录下的main.py文件内容"
    plan = planner_instance.generate_plan(file_goal)
    assert len(plan.steps) >= 2
    # 测试代码分析类任务匹配
    code_goal = "分析项目代码中的bug"
    code_plan = planner_instance.generate_plan(code_goal)
    assert len(code_plan.steps) >= 2
