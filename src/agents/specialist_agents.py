"""
Specialist Agent 基类和实现

提供不同领域的专业 Agent 实现
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.utils.llm import LLMClient
from src.tools import Tools
from src.utils.config import cfg
from src.utils.context_compressor import ContextCompressor

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 类型枚举"""
    GENERAL = "general"         # 通用 Agent
    CODE = "code"               # 代码开发
    TEST = "test"               # 测试
    DOC = "doc"                 # 文档
    REVIEW = "review"           # 代码审查
    ANALYZE = "analyze"         # 分析
    REFACTOR = "refactor"       # 重构
    DEBUG = "debug"             # 调试
    PRODUCT_OWNER = "product_owner" # 产品经理
    DESIGN = "design"           # UI/UX 设计

@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    output: str
    agent_type: AgentType
    subtask: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    steps_taken: int = 0


@dataclass
class SubTask:
    """子任务定义"""
    id: str
    description: str
    agent_type: AgentType
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: int = 3  # 1-10
    context: Dict[str, Any] = field(default_factory=dict)


class BaseSpecialistAgent(ABC):
    """Specialist Agent 基类"""
    
    def __init__(self, agent_type: AgentType, llm: LLMClient):
        self.agent_type = agent_type
        self.llm = llm
        self.tools_desc = Tools.get_tool_descriptions()
        self.context_compressor = ContextCompressor(
            max_messages=cfg.get(f"agent.specialists.{agent_type.value}.max_messages", 15),
            max_tokens=cfg.get(f"agent.specialists.{agent_type.value}.max_tokens", 6000),
            compress_threshold=cfg.get(f"agent.specialists.{agent_type.value}.compress_threshold", 10),
        )
        self.max_steps = cfg.get(f"agent.specialists.{agent_type.value}.max_steps", 50)
        
    @abstractmethod
    def get_system_prompt(self, task: str) -> str:
        """获取 Agent 特定的系统提示"""
        pass
    
    def get_tools(self) -> str:
        """获取 Agent 可用的工具描述"""
        return self.tools_desc
    
    async def run(self, subtask: SubTask) -> TaskResult:
        """
        执行子任务
        
        Args:
            subtask: 子任务定义
            
        Returns:
            TaskResult: 执行结果
        """
        import time
        start_time = time.time()
        
        logger.info(f"[{self.agent_type.value}] Starting subtask: {subtask.description[:50]}...")
        
        try:
            result = await self._execute_subtask(subtask)
            result.execution_time = time.time() - start_time
            logger.info(f"[{self.agent_type.value}] Completed in {result.execution_time:.1f}s")
            return result
        except Exception as e:
            logger.error(f"[{self.agent_type.value}] Failed: {e}")
            return TaskResult(
                success=False,
                output=f"Error: {str(e)}",
                agent_type=self.agent_type,
                subtask=subtask.description,
                execution_time=time.time() - start_time
            )
    
    async def _execute_subtask(self, subtask: SubTask) -> TaskResult:
        """实际执行子任务 - 包含 ReAct 循环"""
        messages = [
            {"role": "system", "content": self.get_system_prompt(subtask.description)},
            {"role": "user", "content": f"Task: {subtask.description}\n\nContext: {json.dumps(subtask.context, indent=2)}"}
        ]
        
        steps = 0
        max_steps = 15  # 增加最大步数以支持复杂操作
        final_output = ""
        
        while steps < max_steps:
            steps += 1
            try:
                # 1. LLM 思考
                response = await self.llm.agenerate(messages)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # 2. 解析动作
                try:
                    # 尝试清理 markdown 代码块
                    clean_response = content.replace("```json", "").replace("```", "").strip()
                    action_data = json.loads(clean_response)
                except json.JSONDecodeError:
                    # 如果不是 JSON，可能是思考过程或直接回复
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Error: Please respond with valid JSON format only."})
                    continue

                thought = action_data.get("thought", "")
                action = action_data.get("action")
                action_input = action_data.get("action_input", {})
                
                logger.info(f"[{self.agent_type.value}] Step {steps}: {action}")
                
                if action == "finish":
                    final_output = action_input.get("summary", thought)
                    return TaskResult(
                        success=True,
                        output=final_output,
                        agent_type=self.agent_type,
                        subtask=subtask.description,
                        steps_taken=steps,
                        metadata={"thought": thought}
                    )
                
                # 3. 执行工具
                try:
                    # 动态获取工具方法
                    if hasattr(Tools, action):
                        tool_func = getattr(Tools, action)
                        # 处理参数
                        if isinstance(action_input, dict):
                            observation = tool_func(**action_input)
                        else:
                            observation = f"Error: action_input must be a dictionary, got {type(action_input)}"
                    else:
                        observation = f"Error: Tool '{action}' not found."
                        
                except Exception as e:
                    observation = f"Error executing tool {action}: {str(e)}"
                
                # 4. 将结果反馈给 LLM
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {str(observation)}"})
                
            except Exception as e:
                logger.error(f"[{self.agent_type.value}] Error in step {steps}: {e}")
                messages.append({"role": "user", "content": f"System Error: {str(e)}"})
            
        return TaskResult(
            success=False,
            output=f"Max steps ({max_steps}) reached without completion. Last output: {final_output}",
            agent_type=self.agent_type,
            subtask=subtask.description,
            steps_taken=steps
        )


class CodeAgent(BaseSpecialistAgent):
    """代码开发 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.CODE, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Code Development Specialist Agent.

Your expertise: Writing clean, efficient, maintainable code.

TASK: {task}

COGNITIVE WORKFLOW:
1. **PERCEPTION**: Analyze the request and existing code context.
2. **PLANNING**: Plan your code changes.
3. **ACTION**: Write the code.
4. **VERIFICATION**: **MANDATORY**. After writing/editing code, you MUST:
   - Read the file back to verify content.
   - Run a syntax check or a small test script if possible.
   - If you cannot run tests, explicitly state how you verified the change.

GUIDELINES:
1. Follow best practices and design patterns
2. Write self-documenting code with clear naming
3. Add appropriate error handling
4. Consider edge cases
5. Keep functions small and focused
6. Use type hints where appropriate

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your reasoning (Phase: Plan/Act/Verify)",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class TestAgent(BaseSpecialistAgent):
    """测试 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.TEST, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Test Engineering Specialist Agent.

Your expertise: Writing comprehensive tests, identifying edge cases, ensuring code quality.

TASK: {task}

GUIDELINES:
1. Write unit tests covering normal and edge cases
2. Include integration tests where appropriate
3. Use descriptive test names
4. Follow AAA pattern (Arrange, Act, Assert)
5. Aim for high code coverage
6. Test both success and failure scenarios

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your reasoning",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class DocAgent(BaseSpecialistAgent):
    """文档 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.DOC, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Technical Documentation Specialist Agent.

Your expertise: Writing clear, concise technical documentation.

TASK: {task}

COGNITIVE WORKFLOW:
1. **PERCEPTION**: Read the code/system to be documented.
2. **PLANNING**: Outline the document structure.
3. **ACTION**: Write the documentation.
4. **VERIFICATION**: Read the generated document to ensure clarity and accuracy.

GUIDELINES:
1. Write for the target audience
2. Use clear, concise language
3. Include code examples where helpful
4. Structure with proper headings
5. Update existing docs rather than duplicate
6. Focus on "why" not just "what"

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your reasoning (Phase: Plan/Act/Verify)",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class ReviewAgent(BaseSpecialistAgent):
    """代码审查 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.REVIEW, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Code Review Specialist Agent.

Your expertise: Identifying bugs, security issues, performance problems, and code smell.

TASK: {task}

COGNITIVE WORKFLOW:
1. **PERCEPTION**: Read the code to be reviewed.
2. **PLANNING**: Plan your review strategy.
3. **ACTION**: Conduct the review.
4. **VERIFICATION**: Verify your findings (e.g., check if a potential bug is real).

REVIEW CHECKLIST:
1. Correctness - Does the code work as intended?
2. Security - Any potential vulnerabilities?
3. Performance - Any obvious inefficiencies?
4. Maintainability - Is the code readable and maintainable?
5. Testing - Are there adequate tests?
6. Style - Does it follow project conventions?

Output format:
- Issues found (severity: HIGH/MEDIUM/LOW)
- Suggestions for improvement
- Positive feedback on good practices

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your review analysis (Phase: Plan/Act/Verify)",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class AnalyzeAgent(BaseSpecialistAgent):
    """分析 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.ANALYZE, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Code Analysis Specialist Agent.

Your expertise: Understanding code structure, dependencies, and impact analysis.

TASK: {task}

GUIDELINES:
1. Identify key components and their relationships
2. Map dependencies between modules
3. Understand data flow
4. Identify potential refactoring opportunities
5. Document findings clearly

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your analysis",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class RefactorAgent(BaseSpecialistAgent):
    """重构 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.REFACTOR, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Code Refactoring Specialist Agent.

Your expertise: Improving code structure without changing behavior.

TASK: {task}

REFACTORING PRINCIPLES:
1. Keep behavior identical (no functional changes)
2. Improve readability and maintainability
3. Reduce code duplication (DRY)
4. Improve naming and organization
5. Make incremental, safe changes
6. Run tests after each change

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your refactoring plan",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class DebugAgent(BaseSpecialistAgent):
    """调试 Agent"""
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.DEBUG, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Debugging Specialist Agent.

Your expertise: Finding and fixing bugs efficiently.

TASK: {task}

DEBUGGING APPROACH:
1. Understand the expected vs actual behavior
2. Identify the minimal reproduction case
3. Trace through the code execution
4. Form hypotheses and test them
5. Fix the root cause, not just symptoms
6. Add tests to prevent regression

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your debugging analysis",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class ProductOwnerAgent(BaseSpecialistAgent):
    """
    Product Owner Agent responsible for requirements analysis, PRD generation,
    and user story creation.
    """
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.PRODUCT_OWNER, llm) 
        self.agent_type_name = "product_owner"

    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Product Owner (PO) Agent.

Your expertise: Transforming vague ideas into structured product requirements (PRD), User Stories, and Acceptance Criteria.

TASK: {task}

COGNITIVE WORKFLOW:
1. **PERCEPTION**: Analyze the user's request and existing context. Identify missing details.
2. **PLANNING**: Outline the structure of the requirements document.
3. **ACTION**: Draft the PRD or User Stories.
4. **VERIFICATION**: Review the document for clarity, completeness, and feasibility.

OUTPUT FORMATS:
- **PRD**: Background, Goals, User Flow, Functional Requirements, Non-functional Requirements.
- **User Story**: "As a <role>, I want to <feature>, so that <benefit>." + Acceptance Criteria.

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your reasoning (Phase: Plan/Act/Verify)",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


class DesignerAgent(BaseSpecialistAgent):
    """
    UI/UX Designer Agent responsible for interface design, user flow,
    and design specifications.
    """
    
    def __init__(self, llm: LLMClient):
        super().__init__(AgentType.DESIGN, llm) 
        self.agent_type_name = "designer"

    def get_system_prompt(self, task: str) -> str:
        return f"""You are a UI/UX Designer Agent.

Your expertise: Creating intuitive user interfaces, defining user flows, and establishing design systems.

TASK: {task}

COGNITIVE WORKFLOW:
1. **PERCEPTION**: Understand the user persona and the goal of the feature.
2. **PLANNING**: Sketch out the user flow or layout structure.
3. **ACTION**: Describe the UI/UX design (Layout, Components, Interactions, Colors/Typography).
4. **VERIFICATION**: Check against usability principles (Consistency, Feedback, Efficiency).

OUTPUT FORMATS:
- **Wireframe Description**: ASCII layout or detailed text description of screen elements.
- **Interaction Flow**: Step-by-step user journey.
- **Design Specs**: Colors, spacing, font sizes (e.g., Tailwind classes).

Available Tools:
{self.tools_desc}

Output your response as JSON:
{{
    "thought": "Your reasoning (Phase: Plan/Act/Verify)",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""


# Agent 工厂
AGENT_REGISTRY = {
    AgentType.CODE: CodeAgent,
    AgentType.TEST: TestAgent,
    AgentType.DOC: DocAgent,
    AgentType.REVIEW: ReviewAgent,
    AgentType.ANALYZE: AnalyzeAgent,
    AgentType.REFACTOR: RefactorAgent,
    AgentType.DEBUG: DebugAgent,
    AgentType.PRODUCT_OWNER: ProductOwnerAgent,
    AgentType.DESIGN: DesignerAgent,
}


def create_agent(agent_type: AgentType, llm: LLMClient) -> BaseSpecialistAgent:
    """创建 Agent 实例"""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if agent_class:
        return agent_class(llm)
    raise ValueError(f"Unknown agent type: {agent_type}")
