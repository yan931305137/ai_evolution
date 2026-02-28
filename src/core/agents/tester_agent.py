#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试专项Agent
功能：测试用例生成、自动化测试执行、测试覆盖率分析、缺陷定位与分析、测试报告生成等测试专属能力
继承自基础AutoAgent，扩展测试专属功能与适配场景
"""
import json
import re
from typing import Dict, List, Any, Optional
from src.agents.agent import AutoAgent
from src.utils.llm import LLMClient
from src.tools import Tools
from rich.console import Console

console = Console()

class TesterAgent(AutoAgent):
    """测试专项Agent类"""
    
    def __init__(self, llm: LLMClient):
        # 调用父类初始化方法
        super().__init__(llm)
        
        # 测试专属工具集，过滤无关工具
        self.tester_tools = [
            "list_files", "read_file", "write_file", "run_command", "scan_project",
            "run_test_suite", "code_security_verification", "project_compliance_auto_check",
            "read_large_file", "grayscale_test_executor"
        ]
        # 重新生成专属工具描述
        self.tools_desc = self._get_tester_tool_descriptions()
        
        # 测试专属配置
        self.test_coverage_threshold = 80  # 默认测试覆盖率阈值
        self.defect_severity_levels = ["blocker", "critical", "major", "minor", "trivial"]
        
    def _get_tester_tool_descriptions(self) -> str:
        """获取测试专属工具描述，过滤非测试相关工具"""
        all_tools = json.loads(Tools.get_tool_descriptions())
        tester_tool_list = {k: v for k, v in all_tools.items() if k in self.tester_tools}
        return json.dumps(tester_tool_list, ensure_ascii=False, indent=2)
    
    def _generate_tester_system_prompt(self, goal: str, memory_context: str, preference_prompt: str) -> str:
        """生成测试专属系统提示词"""
        return f"""
你是专业的高级测试工程师Agent，精通功能测试、自动化测试、性能测试、安全测试等全链路测试能力，具备测试用例设计、测试执行、缺陷分析、测试报告生成等全流程测试经验。
当前任务目标：{goal}

{memory_context}
{preference_prompt}

专属规则：
1. 测试用例设计必须覆盖正常场景、边界场景、异常场景
2. 自动化测试用例必须可重复执行，具备断言逻辑
3. 测试覆盖率必须达到{self.test_coverage_threshold}%以上
4. 缺陷描述必须包含重现步骤、预期结果、实际结果、严重级别
5. 测试报告必须包含测试覆盖率、通过率、缺陷统计等核心指标
6. 禁止遗漏任何高优先级测试场景

可用工具：
{self.tools_desc}

输出要求：
必须严格按照JSON格式输出，结构如下：
{{
    "thought": "你的思考过程，说明下一步要做什么以及原因",
    "action": "工具名称，完成任务时用'finish'",
    "action_input": {{ "参数名": "参数值" }}
}}
"""
    
    def run(self, goal: str, history: List[Dict[str, str]] = None) -> str:
        """重写run方法，使用测试专属提示词"""
        if history is None:
            history = []
            
        # 1. 检索相关记忆
        memory_context = self._retrieve_memory_context(goal)
            
        # 获取用户偏好
        from src.utils.user_profile import user_profile_manager
        user_preferences = user_profile_manager.extract_preferences_from_history()
        preference_prompt = user_profile_manager.get_preference_prompt(user_preferences)
        
        # 使用测试专属系统提示词
        system_prompt = self._generate_tester_system_prompt(goal, memory_context, preference_prompt)
        
        # 初始化对话
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"开始执行测试任务：{goal}"}
        ]
        
        step_count = 0
        recent_actions = []
        max_repeat_actions = 3
        
        while step_count < self.max_steps:
            step_count += 1
            console.print(f"\n[bold yellow]测试Agent执行步骤 {step_count}/{self.max_steps}[/bold yellow]")
            
            try:
                content = self._get_llm_response(messages)
            except Exception as e:
                self.self_awareness.record_capability_usage("test_execution", False)
                return f"测试任务失败：LLM调用失败，错误：{str(e)}"
                
            try:
                action_data = self._parse_action_data(content)
                action = action_data.get("action")
                action_input = action_data.get("action_input", {})
                
                # 重复动作检测
                action_signature = f"{action}_{json.dumps(action_input, sort_keys=True)}"
                recent_actions.append(action_signature)
                if len(recent_actions) > 5:
                    recent_actions.pop(0)
                repeat_count = recent_actions.count(action_signature)
                
                if repeat_count >= max_repeat_actions:
                    console.print(f"[red]警告：动作 {action} 重复执行 {repeat_count} 次，更换策略[/red]")
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"错误：你已经重复执行动作 '{action}' {repeat_count} 次没有进展，请更换测试方案。"})
                    continue
                
                console.print(f"[bold green]执行动作：[/bold green] {action}({action_input})")
                
            except (json.JSONDecodeError, AttributeError) as e:
                console.print(f"[red]JSON解析错误：[/red] {content}")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "错误：响应不是有效的JSON，请仅输出JSON对象。"})
                continue

            if action == "finish":
                summary = action_input.get('summary', '测试任务完成')
                self.self_awareness.record_capability_usage("test_execution", True)
                console.print(f"\n[bold green]测试任务完成！[/bold green]")
                console.print(f"完成总结：{summary}")
                return summary
            
            # 执行工具
            try:
                observation = Tools.execute_tool(action, action_input)
                console.print(f"[bold blue]执行结果：[/bold blue] {str(observation)[:200]}..." if len(str(observation)) > 200 else f"[bold blue]执行结果：[/bold blue] {observation}")
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
            except Exception as e:
                error_msg = f"工具执行失败：{str(e)}"
                console.print(f"[red]{error_msg}[/red]")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Error: {error_msg}"})
                
        self.self_awareness.record_capability_usage("test_execution", False)
        return f"测试任务失败：超过最大步骤数 {self.max_steps}"


# 测试Agent场景测试用例
def test_tester_agent():
    """测试Agent场景模拟测试，测试测试用例生成能力"""
    from src.utils.llm import LLMClient
    llm = LLMClient()
    agent = TesterAgent(llm)
    
    # 测试场景：为加法函数生成单元测试用例
    test_goal = "为一个支持整数和浮点数相加的Python加法函数生成完整的单元测试用例，覆盖正常场景、边界场景、异常场景"
    
    result = agent.run(test_goal)
    assert "测试用例" in result and "边界场景" in result and "异常场景" in result, "测试Agent测试失败"
    print("✅ 测试Agent场景测试通过")
    return True


if __name__ == "__main__":
    # 运行测试
    test_tester_agent()