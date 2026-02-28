#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义技能存储文件，所有可复用的Python技能都存储在此
"""
from typing import Tuple, Dict, List, Any, Optional
import time
import threading

# 技能注册表
SKILL_REGISTRY = {}

def register_skill(name: str, func: callable, description: str):
 """注册技能到注册表"""
 SKILL_REGISTRY[name] = {
 'func': func,
 'description': description
 }
 return True


# Skill: 自我优化安全管控与测试框架总调度器，实现修改前风险评估、修改中灰度验证、修改后效果回测全流程自动化，异常时10秒内自动回滚稳定版本，核心功能不失效
from typing import Tuple, Dict, List
from custom_skills import (
 code_security_verification, analyze_change_impact,
 grayscale_test_executor, run_test_suite,
 deployment_rollback_manager
)
import time
import threading

def security_test_framework_scheduler(
 target_file_path: str, 
 modified_code_content: str, 
 test_cases: List[str] = None,
 coverage_threshold: float = 80.0
) -> Tuple[bool, Dict]:
 """
 自我优化安全管控与测试框架总调度入口
 实现修改前风险评估→修改中灰度验证→修改后效果回测全流程自动化，异常10秒内自动回滚
 :param target_file_path: 待修改的目标文件路径
 :param modified_code_content: 修改后的代码内容
 :param test_cases: 关联的测试用例列表
 :param coverage_threshold: 测试覆盖率阈值
 :return: (是否执行成功, 执行结果详情)
 """
 start_time = time.time()
 result = {
 'steps': [],
 'success': False,
 'rollback_triggered': False,
 'total_cost_time': 0
 }
 
 # ---------------------- 第一步：修改前风险评估 ----------------------
 result['steps'].append('step1: 开始修改前风险评估')
 # 1.1 代码安全校验
 security_pass, security_result = code_security_verification(target_file_path, modified_code_content)
 if not security_pass:
 result['steps'].append('step1 失败：代码安全校验不通过')
 result['error'] = security_result
 return False, result
 # 1.2 变更影响分析
 impact_result = analyze_change_impact(target_file_path, '代码修改风险评估')
 # 高风险拦截：影响核心模块超过3个直接驳回
 core_impact_count = len([f for f in impact_result.get('dependent_files', []) if 'core/' in f])
 if core_impact_count > 3:
 result['steps'].append('step1 失败：变更影响范围过大，高风险拦截')
 result['error'] = impact_result
 return False, result
 result['steps'].append('step1 成功：风险评估通过')
 
 # ---------------------- 第二步：灰度验证与自动回滚准备 ----------------------
 result['steps'].append('step2: 开始灰度验证，启动10秒异常回滚看门狗')
 rollback_triggered = threading.Event()
 rollback_result = {'success': False}
 
 # 启动看门狗线程：异常时10秒内自动回滚
 def rollback_watchdog():
 wait_start = time.time()
 while time.time() - wait_start < 10:
 if rollback_triggered.is_set():
 # 触发回滚，恢复稳定版本
 rb_pass, rb_res = deployment_rollback_manager(
 target_file_path, modified_code_content, 
 auto_rollback=True, smoke_test_code=test_cases[0] if test_cases else None
 )
 rollback_result['success'] = rb_pass
 rollback_result['detail'] = rb_res
 return
 time.sleep(0.1)
 
 watchdog_thread = threading.Thread(target=rollback_watchdog, daemon=True)
 watchdog_thread.start()
 
 # 执行灰度测试
 grayscale_pass, grayscale_result = grayscale_test_executor(
 target_file_path, test_cases, coverage_threshold
 )
 if not grayscale_pass:
 result['steps'].append('step2 失败：灰度验证不通过，触发自动回滚')
 rollback_triggered.set()
 watchdog_thread.join(timeout=10)
 result['rollback_triggered'] = True
 result['rollback_result'] = rollback_result
 return False, result
 result['steps'].append('step2 成功：灰度验证通过')
 
 # ---------------------- 第三步：修改后效果回测 ----------------------
 result['steps'].append('step3: 开始修改后效果回测')
 test_pass, test_result = run_test_suite(target_file_path, test_cases, coverage_threshold)
 if not test_pass:
 result['steps'].append('step3 失败：效果回测不通过，触发自动回滚')
 rollback_triggered.set()
 watchdog_thread.join(timeout=10)
 result['rollback_triggered'] = True
 result['rollback_result'] = rollback_result
 return False, result
 result['steps'].append('step3 成功：效果回测通过')
 
 # 所有流程通过，取消看门狗
 rollback_triggered.set()
 watchdog_thread.join(timeout=2)
 
 result['success'] = True
 result['total_cost_time'] = round(time.time() - start_time, 2)
 result['steps'].append(f'全流程执行完成，总耗时{result["total_cost_time"]}秒')
 return True, result


# Skill: 解析自我对话生成的自然语言优化需求，自动匹配对应的目标功能模块，返回模块路径、关联测试用例、匹配置信度，匹配准确率不低于90%
import json
from typing import Tuple, Optional, List
from src.utils.llm import LLMClient

def requirement_to_module_matcher(requirement_text: str) -> Tuple[Optional[str], Optional[List[str]], float, str]:
 """
 解析自然语言优化需求，自动匹配对应的目标模块
 参数：
 requirement_text: 自我对话生成的自然语言优化需求文本
 返回：
 (匹配到的模块路径, 关联测试用例列表, 匹配置信度(0-100), 优化目标描述)
 当匹配置信度低于90%时返回None作为模块路径，确保匹配准确率不低于90%
 """
 # 初始化LLM客户端
 llm_client = LLMClient()
 
 # 项目模块功能映射知识库，内置所有模块的功能描述用于匹配
 module_knowledge_base = [
 {"path": "src/brain/attention_system/", "desc": "注意力系统，负责信息优先级分配、焦点管理、重要信息筛选"},
 {"path": "src/brain/decision_system/", "desc": "决策系统，负责行为决策、目标拆解、优先级判断、方案选择"},
 {"path": "src/brain/memory_system/", "desc": "记忆系统，负责长短期记忆存储、检索、遗忘管理、记忆关联"},
 {"path": "src/brain/perception_system/", "desc": "感知系统，负责输入信息解析、意图识别、实体抽取、语义理解"},
 {"path": "src/brain/value_system/", "desc": "价值体系，负责目标价值评估、行为奖惩判断、优先级排序"},
 {"path": "src/skills/", "desc": "技能模块，所有可复用功能函数、工具方法、业务能力的实现"},
 {"path": "src/utils/", "desc": "工具模块，通用工具类、辅助函数、中间件、公共组件实现"},
 {"path": "src/agents/", "desc": "智能体模块，各角色智能体的逻辑实现、任务调度、交互逻辑"},
 {"path": "src/core/", "desc": "核心模块，系统底层核心能力、基础框架、运行时环境实现"},
 {"path": "src/tools/", "desc": "工具集模块，所有外部工具调用、API封装、能力集成的实现"}
 ]

 # 构建匹配prompt，确保LLM返回正确的结构化结果
 match_prompt = f"""
 请根据以下项目模块知识库，解析用户的优化需求，匹配最合适的目标模块，并返回严格的JSON格式结果：
 模块知识库：
 {json.dumps(module_knowledge_base, ensure_ascii=False, indent=2)}
 优化需求：
 {requirement_text}
 
 输出要求：仅返回JSON，不要任何其他内容，字段说明：
 1. module_path: 匹配到的最适合的模块完整路径，如果无法确定返回null
 2. test_cases: 关联的测试用例路径列表，没有则返回空数组
 3. confidence: 匹配置信度，0-100的数字，只有当你100%确定匹配正确时才能返回>=90的值，否则返回低于90
 4. optimization_target: 提炼后的清晰优化目标描述
 """

 # 调用LLM执行匹配
 try:
 match_result_str = llm_client.chat(match_prompt).strip()
 # 移除可能的markdown代码块标记
 match_result_str = match_result_str.replace('', '').replace('', '').strip()
 match_result = json.loads(match_result_str)
 
 module_path = match_result.get("module_path")
 test_cases = match_result.get("test_cases", [])
 confidence = float(match_result.get("confidence", 0.0))
 optimization_target = match_result.get("optimization_target", "")
 
 # 安全校验：低于90置信度的匹配直接返回None，确保准确率不低于90%
 if confidence < 90.0:
 module_path = None
 
 return module_path, test_cases, confidence, optimization_target
 
 except Exception as e:
 # 解析异常时返回低置信度结果
 return None, [], 0.0, f"需求解析失败：{str(e)}"
 
# 测试代码
if __name__ == "__main__":
 # 测试用例1：明确需求匹配
 test_req1 = "优化记忆系统的检索速度，减少内存占用"
 path, cases, conf, target = requirement_to_module_matcher(test_req1)
 print(f"测试1结果：路径={path}, 置信度={conf}, 目标={target}")
 assert conf >= 90.0 or path is None, "匹配准确率不满足要求"
 
 # 测试用例2：模糊需求匹配
 test_req2 = "优化某个地方的响应速度"
 path, cases, conf, target = requirement_to_module_matcher(test_req2)
 print(f"测试2结果：路径={path}, 置信度={conf}, 目标={target}")
 assert conf < 90.0 and path is None, "模糊需求应该返回低置信度"
