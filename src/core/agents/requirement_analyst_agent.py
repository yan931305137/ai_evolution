#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求分析专项Agent
功能：需求拆解、需求评审、需求合理性校验、需求优先级评估、PRD文档生成、需求转开发任务等需求分析专属能力
继承自基础AutoAgent，扩展需求分析专属功能与适配场景
"""
import json
import re
from typing import Dict, List, Any, Optional
from src.agents.agent import AutoAgent
from src.utils.llm import LLMClient
from src.tools import Tools
from rich.console import Console

console = Console()

class RequirementAnalystAgent(AutoAgent):
    """需求分析专项Agent类"""
    
    def __init__(self, llm: LLMClient):
        # 调用父类初始化方法
        super().__init__(llm)
        
        # 需求分析专属工具集，过滤无关工具
        self.ra_tools = [
            "list_files", "read_file", "write_file", "scan_project", "web_search",
            "project_compliance_auto_check", "read_large_file"
        ]
        # 重新生成专属工具描述
        self.tools_desc = self._get_ra_tool_descriptions()
        
        # 需求分析专属配置
        self.requirement_priority_levels = ["P0", "P1", "P2", "P3"]  # 需求优先级
        self.requirement_completeness_threshold = 90  # 需求完整性最低阈值
        
    def _get_ra_tool_descriptions(self) -> str:
        """获取需求分析专属工具描述，过滤非需求分析相关工具"""
        all_tools = json.loads(Tools.get_tool_descriptions())
        ra_tool_list = {k: v for k, v in all_tools.items() if k in self.ra_tools}
        return json.dumps(ra_tool_list, ensure_ascii=False, indent=2)
    
    def _generate_ra_system_prompt(self, goal: str, memory_context: str, preference_prompt: str) -> str:
        """生成需求分析专属系统提示词"""
        return f"""
你是专业的高级需求分析师Agent，精通需求调研、需求拆解、需求评审、需求优先级评估、PRD文档生成、需求转开发任务等全流程需求分析能力，能够准确理解业务需求，将模糊需求转化为清晰可落地的开发任务。
当前任务目标：{goal}

{memory_context}
{preference_prompt}

专属规则：
1. 需求拆解必须遵循MECE原则，相互独立、完全穷尽
2. 需求必须明确功能范围、验收标准、优先级、依赖关系
3. PRD文档必须包含需求背景、功能描述、业务流程、验收标准、非功能需求等核心模块
4. 需求合理性校验必须考虑技术可行性、投入产出比、业务价值
5. 需求优先级评估必须综合考虑业务价值、紧急程度、实现难度
6. 禁止输出模糊、歧义的需求描述

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
        """重写run方法，使用需求分析专属提示词"""
        if history is None:
            history = []
            
        # 1. 检索相关记忆
        memory_context = self._retrieve_memory_context(goal)
            
        # 获取用户偏好
        from src.utils.user_profile import user_profile_manager
        user_preferences = user_profile_manager.extract_preferences_from_history()
        preference_prompt = user_profile_manager.get_preference_prompt(user_preferences)
        
        # 使用需求分析专属系统提示词
        system_prompt = self._generate_ra_system_prompt(goal, memory_context, preference_prompt)
        
        # 初始化对话
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"开始执行需求分析任务：{goal}"}
        ]
        
        step_count = 0
        recent_actions = []
        max_repeat_actions = 3
        
        while step_count < self.max_steps:
            step_count += 1
            console.print(f"\n[bold yellow]需求分析Agent执行步骤 {step_count}/{self.max_steps}[/bold yellow]")
            
            try:
                content = self._get_llm_response(messages)
            except Exception as e:
                self.self_awareness.record_capability_usage("requirement_analysis", False)
                return f"需求分析任务失败：LLM调用失败，错误：{str(e)}"
                
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
                    messages.append({"role": "user", "content": f"错误：你已经重复执行动作 '{action}' {repeat_count} 次没有进展，请更换需求分析方案。"})
                    continue
                
                console.print(f"[bold green]执行动作：[/bold green] {action}({action_input})")
                
            except (json.JSONDecodeError, AttributeError) as e:
                console.print(f"[red]JSON解析错误：[/red] {content}")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "错误：响应不是有效的JSON，请仅输出JSON对象。"})
                continue

            if action == "finish":
                summary = action_input.get('summary', '需求分析任务完成')
                self.self_awareness.record_capability_usage("requirement_analysis", True)
                console.print(f"\n[bold green]需求分析任务完成！[/bold green]")
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
                
        self.self_awareness.record_capability_usage("requirement_analysis", False)
        return f"需求分析任务失败：超过最大步骤数 {self.max_steps}"


# 需求分析Agent场景测试用例
def test_requirement_analyst_agent():
    """需求分析Agent场景模拟测试，测试需求拆解能力"""
    from src.utils.llm import LLMClient
    llm = LLMClient()
    agent = RequirementAnalystAgent(llm)
    
    # 测试场景：拆解用户管理系统需求
    test_goal = "拆解用户管理系统的需求，输出需求模块划分、优先级、验收标准"
    
    result = agent.run(test_goal)
    assert "需求模块" in result and "优先级" in result and "验收标准" in result, "需求分析Agent测试失败"
    print("✅ 需求分析Agent场景测试通过")
    return True


if __name__ == "__main__":
    # 运行测试
    test_requirement_analyst_agent()