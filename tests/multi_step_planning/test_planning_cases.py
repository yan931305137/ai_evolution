import pytest
from src.brain.planning_system import PlanningSystem

# 初始化规划系统实例
@pytest.fixture(scope="module")
def planning_instance():
 """测试前置：初始化多步骤规划系统实例"""
 return PlanningSystem()


def test_simple_task_decomposition(planning_instance):
 """测试用例1：简单任务拆解，验证基础目标拆解能力"""
 goal = "明天在家做番茄炒蛋"
 plan = planning_instance.generate_plan(goal)
 # 验证拆解的步骤数量和关键步骤
 assert len(plan.steps) >= 3
 step_contents = [step.content for step in plan.steps]
 assert any("准备食材" in step or "番茄" in step or "鸡蛋" in step for step in step_contents)
 assert any("炒制" in step or "烹饪" in step for step in step_contents)
 assert any("盛盘" in step or "出锅" in step for step in step_contents)


def test_multi_tool_call_planning(planning_instance):
 """测试用例2：多工具调用规划，验证工具链规划能力"""
 goal = "统计当前项目Python代码总行数，然后把结果写入到report.md文件中"
 plan = planning_instance.generate_plan(goal)
 # 验证步骤包含对应的工具调用
 step_contents = [step.content for step in plan.steps]
 assert any("统计代码行数" in step or "count_lines" in step for step in step_contents)
 assert any("写入文件" in step or "write_file" in step for step in step_contents)
 # 验证步骤顺序正确：先统计再写入
 count_idx = next(i for i, s in enumerate(step_contents) if "统计" in s or "count_lines" in s)
 write_idx = next(i for i, s in enumerate(step_contents) if "写入" in s or "write_file" in s)
 assert count_idx < write_idx


def test_error_path_correction_planning(planning_instance):
 """测试用例3：错误路径修正，验证规划调整能力"""
 goal = "安装pandas库，但是如果pip安装失败就用conda安装"
 plan = planning_instance.generate_plan(goal)
 # 验证包含分支判断逻辑
 assert plan.has_branch_logic == True
 step_contents = [step.content for step in plan.steps]
 assert any("pip install pandas" in step or "pip安装pandas" in step for step in step_contents)
 assert any("如果安装失败" in step or "conda install pandas" in step for step in step_contents)


def test_resource_dependency_planning(planning_instance):
 """测试用例4：资源依赖规划，验证依赖顺序处理能力"""
 goal = "部署一个Web服务，需要先安装依赖，再配置环境变量，最后启动服务"
 plan = planning_instance.generate_plan(goal)
 # 验证步骤顺序符合依赖关系
 step_contents = [step.content for step in plan.steps]
 install_idx = next(i for i, s in enumerate(step_contents) if "安装依赖" in s or "install" in s)
 config_idx = next(i for i, s in enumerate(step_contents) if "配置环境变量" in s or "config" in s)
 start_idx = next(i for i, s in enumerate(step_contents) if "启动服务" in s or "start" in s)
 assert install_idx < config_idx < start_idx


def test_long_flow_task_planning(planning_instance):
 """测试用例5：长流程任务规划，验证长序列任务处理能力"""
 goal = "开发一个简单的TodoList应用，包括需求分析、数据库设计、后端接口开发、前端页面开发、测试、部署上线"
 plan = planning_instance.generate_plan(goal)
 # 验证步骤覆盖所有要求的环节
 assert len(plan.steps) >= 5
 step_contents = [step.content for step in plan.steps]
 required_stages = ["需求分析", "数据库设计", "后端开发", "前端开发", "测试", "部署"]
 matched_count = sum(1 for stage in required_stages if any(stage in s for s in step_contents))
 assert matched_count >= 5


def test_task_conflict_resolution_planning(planning_instance):
 """测试用例6：任务冲突处理，验证冲突场景规划能力"""
 goal = "明天下午2点既要参加会议，又要完成代码提交，会议预计1小时，代码提交需要30分钟"
 plan = planning_instance.generate_plan(goal)
 # 验证包含时间调整或优先级处理逻辑
 assert any("优先级" in step or "时间调整" in step or "错开时间" in step for step in [s.content for s in plan.steps])


def test_priority_task_planning(planning_instance):
 """测试用例7：优先级任务规划，验证优先级排序能力"""
 goal = "处理三个任务：P0线上bug修复（需要30分钟）、P1需求文档编写（需要2小时）、P2周报提交（需要1小时），按优先级排序执行"
 plan = planning_instance.generate_plan(goal)
 # 验证执行顺序符合优先级：P0 > P1 > P2
 step_contents = [step.content for step in plan.steps]
 bug_idx = next(i for i, s in enumerate(step_contents) if "bug修复" in s or "P0" in s)
 doc_idx = next(i for i, s in enumerate(step_contents) if "需求文档" in s or "P1" in s)
 report_idx = next(i for i, s in enumerate(step_contents) if "周报" in s or "P2" in s)
 assert bug_idx < doc_idx < report_idx


def test_cross_platform_task_planning(planning_instance):
 """测试用例8：跨平台任务规划，验证多环境适配能力"""
 goal = "把当前项目打包，分别发布到GitHub和Gitee两个平台的仓库"
 plan = planning_instance.generate_plan(goal)
 # 验证覆盖两个平台的发布步骤
 step_contents = [step.content for step in plan.steps]
 assert any("GitHub" in step for step in step_contents)
 assert any("Gitee" in step for step in step_contents)


def test_time_constraint_planning(planning_instance):
 """测试用例9：带时间约束的规划，验证时间估算和约束处理能力"""
 goal = "需要在2小时内完成：代码审查（30分钟）、单元测试编写（1小时）、上线部署（20分钟），确保不超时"
 plan = planning_instance.generate_plan(goal)
 # 验证时间总和不超过约束，且包含时间估算
 total_time = sum(step.estimated_time for step in plan.steps if step.estimated_time > 0)
 assert total_time <= 120 # 总时间不超过120分钟


def test_dynamic_adjustment_planning(planning_instance):
 """测试用例10：动态调整规划，验证执行中调整能力"""
 goal = "如果明天不下雨就去公园跑步，如果下雨就在家做瑜伽，之后还要洗澡吃早餐"
 plan = planning_instance.generate_plan(goal)
 # 验证包含动态分支和后续公共步骤
 assert plan.has_branch_logic == True
 step_contents = [step.content for step in plan.steps]
 assert any("下雨" in step or "天气判断" in step for step in step_contents)
 assert any("跑步" in step or "瑜伽" in step for step in step_contents)
 assert any("洗澡" in step or "早餐" in step for step in step_contents)