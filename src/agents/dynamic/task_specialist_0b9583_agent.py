"""
动态生成的 Specialist Agent

Name: task_specialist_0b9583
Description: Specializes in: [dev_team_assessor] 从开发团队视角梳理CI/CD全流程开发相关节点，统计近3个月
Generated at: 2026-03-01T03:10:16.448876
Expertise Level: intermediate
"""
import logging
from src.agents.specialist_agents import BaseSpecialistAgent, AgentType
from src.utils.llm import LLMClient
from src.utils.config import cfg

logger = logging.getLogger(__name__)


class TaskSpecialist0B9583Agent(BaseSpecialistAgent):
    """
    Specializes in: [dev_team_assessor] 从开发团队视角梳理CI/CD全流程开发相关节点，统计近3个月
    
    Capabilities:
- task execution
- problem solving
    """
    
    def __init__(self, llm: LLMClient):
        # 使用 DYNAMIC 类型，但保持 specialist 特性
        super().__init__(AgentType.CODE, llm)
        self.custom_name = "task_specialist_0b9583"
        self.custom_description = """Specializes in: [dev_team_assessor] 从开发团队视角梳理CI/CD全流程开发相关节点，统计近3个月"""
        
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a intermediate-level Specialist Agent.

Your Focus: Efficient task completion with best practices

Task: {task}

Your Capabilities:
- task execution
- problem solving

GUIDELINES:
1. Leverage your specialized expertise
2. Follow best practices in your domain
3. Produce high-quality, professional results
4. Consider edge cases and potential issues
5. Document your approach when appropriate

Available Tools:
- File operations (read_file, write_file, list_files)
- Code modification (patch_code, analyze_code, search_code)

When complete, provide:
1. Summary of what was accomplished
2. Any important findings or decisions
3. Suggestions for next steps if applicable

Output your response as JSON:
{
    "thought": "Your reasoning and approach",
    "action": "tool_name or 'finish'",
    "action_input": {...}
}"""
