#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序员专项Agent
功能：代码编写、调试、优化、代码评审、需求转代码实现、单元测试生成等程序员专属能力
继承自基础AutoAgent，扩展程序员专属功能与适配场景
"""
import json
import re
from typing import Dict, List, Any, Optional
from src.agents.agent import AutoAgent
from src.utils.llm import LLMClient
from src.tools import Tools
from rich.console import Console

console = Console()

class ProgrammerAgent(AutoAgent):
    """程序员专项Agent类"""
    
    def __init__(self, llm: LLMClient):
        # 调用父类初始化方法
        super().__init__(llm)
        
        # 程序员专属工具集，过滤无关工具（如视频生成、天气查询等）
        self.programmer_tools = [
            "list_files", "read_file", "write_file", "move_file", "run_command",
            "scan_project", "patch_code", "create_skill", "modify_skill",
            "patch_core_code", "run_test_suite", "code_security_verification",
            "project_compliance_auto_check", "read_large_file"
        ]
        # 重新生成专属工具描述
        self.tools_desc = self._get_programmer_tool_descriptions()
        
        # 程序员专属配置
        self.code_quality_threshold = 80  # 代码质量最低阈值
        self.test_coverage_requirement = 80  # 测试覆盖率最低要求
        
    def _get_programmer_tool_descriptions(self) -> str:
        """获取程序员专属工具描述，过滤非程序员相关工具"""
        all_tools = json.loads(Tools.get_tool_descriptions())
        programmer_tool_list = {k: v for k, v in all_tools.items() if k in self.programmer_tools}
        return json.dumps(programmer_tool_list, ensure_ascii=False, indent=2)
    
    def _generate_programmer_system_prompt(self, goal: str, memory_context: str, preference_prompt: str) -> str:
        """生成程序员专属系统提示词"""
        return f"""
你是专业的高级程序员Agent，精通Python、Java、JavaScript等主流编程语言，具备代码架构设计、代码编写、调试优化、代码评审、单元测试生成等全栈开发能力。
当前任务目标：{goal}

{memory_context}
{preference_prompt}

专属规则：
1. 所有代码必须符合PEP8规范，添加详细的中文注释
2. 代码实现必须考虑性能、安全性、可维护性
3. 所有功能实现必须配套对应的单元测试用例
4. 代码提交前必须经过安全校验和合规校验
5. 测试覆盖率必须不低于{self.test_coverage_requirement}%
6. 禁止生成任何有安全隐患的代码

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
        """重写run方法，使用程序员专属提示词"""
        if history is None:
            history = []
            
        # 1. 检索相关记忆
        memory_context = self._retrieve_memory_context(goal)
            
        # 获取用户偏好
        from src.utils.user_profile import user_profile_manager
        user_preferences = user_profile_manager.extract_preferences_from_history()
        preference_prompt = user_profile_manager.get_preference_prompt(user_preferences)
        
        # 使用程序员专属系统提示词
        system_prompt = self._generate_programmer_system_prompt(goal, memory_context, preference_prompt)
        
        # 初始化对话
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"开始执行程序员任务：{goal}"}
        ]
        
        step_count = 0
        recent_actions = []
        max_repeat_actions = 3
        
        while step_count < self.max_steps:
            step_count += 1
            console.print(f"\n[bold yellow]程序员Agent执行步骤 {step_count}/{self.max_steps}[/bold yellow]")
            
            try:
                content = self._get_llm_response(messages)
            except Exception as e:
                self.self_awareness.record_capability_usage("programmer_development", False)
                return f"程序员任务失败：LLM调用失败，错误：{str(e)}"
                
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
                    messages.append({"role": "user", "content": f"错误：你已经重复执行动作 '{action}' {repeat_count} 次没有进展，请更换实现方案。"})
                    continue
                
                console.print(f"[bold green]执行动作：[/bold green] {action}({action_input})")
                
            except (json.JSONDecodeError, AttributeError) as e:
                console.print(f"[red]JSON解析错误：[/red] {content}")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "错误：响应不是有效的JSON，请仅输出JSON对象。"})
                continue

            if action == "finish":
                summary = action_input.get('summary', '程序员任务完成')
                self.self_awareness.record_capability_usage("programmer_development", True)
                console.print(f"\n[bold green]程序员任务完成！[/bold green]")
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
                
        self.self_awareness.record_capability_usage("programmer_development", False)
        return f"程序员任务失败：超过最大步骤数 {self.max_steps}"


# 程序员Agent场景测试用例
def test_programmer_agent():
    """程序员Agent场景模拟测试，测试简单代码编写能力"""
    from src.utils.llm import LLMClient
    llm = LLMClient()
    agent = ProgrammerAgent(llm)
    
    # 测试场景：生成一个加法函数并配套单元测试
    test_goal = "编写一个Python加法函数，支持整数和浮点数相加，添加详细注释，同时生成对应的单元测试用例，确保功能正常"
    
    result = agent.run(test_goal)
    assert "加法函数" in result and "单元测试" in result, "程序员Agent测试失败"
    print("✅ 程序员Agent场景测试通过")
    return True


if __name__ == "__main__":
    # 运行测试
    test_programmer_agent()