"""
多 Agent 系统入口

提供简单易用的多 Agent 协调接口
"""
import asyncio
import logging
from typing import Optional

from src.utils.llm import LLMClient
from src.utils.config import cfg
from src.agents.agent import AutoAgent
from src.agents.orchestrator import AgentOrchestrator, ExecutionMode
from src.agents.specialist_agents import AgentType

logger = logging.getLogger(__name__)


class MultiAgentRunner:
    """
    多 Agent 运行器
    
    智能选择使用单 Agent 还是多 Agent 模式
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.llm = LLMClient(api_key=api_key)
        self.single_agent = AutoAgent(llm=self.llm)
        self.orchestrator = AgentOrchestrator(llm=self.llm)
        self.multi_agent_enabled = cfg.get("agent.multi_agent.enabled", True)
        self.auto_detect = cfg.get("agent.multi_agent.auto_detect", True)
        self.complexity_threshold = cfg.get("agent.multi_agent.complexity_threshold", 4)
    
    async def run(self, goal: str, force_mode: Optional[str] = None) -> str:
        """
        执行任务
        
        Args:
            goal: 任务目标
            force_mode: 强制模式 - "single", "multi", 或 None (自动)
        
        Returns:
            执行结果
        """
        logger.info(f"Running task: {goal[:100]}...")
        
        # 决定使用哪种模式
        use_multi = self._should_use_multi_agent(goal, force_mode)
        
        if use_multi:
            logger.info("Using Multi-Agent mode")
            result = await self.orchestrator.execute(goal)
            return f"{result.summary}\n\n## Detailed Results\n\n{result.final_output}"
        else:
            logger.info("Using Single-Agent mode")
            return self.single_agent.run(goal)
    
    def _should_use_multi_agent(self, goal: str, force_mode: Optional[str]) -> bool:
        """判断是否使用多 Agent 模式"""
        # 强制模式
        if force_mode == "multi":
            return True
        if force_mode == "single":
            return False
        
        # 检查全局配置
        if not self.multi_agent_enabled:
            return False
        
        # 自动检测
        if self.auto_detect:
            complexity = self._assess_complexity(goal)
            logger.info(f"Task complexity assessed as: {complexity}/10")
            return complexity >= self.complexity_threshold
        
        return False
    
    def _assess_complexity(self, goal: str) -> int:
        """快速评估任务复杂度"""
        # 简单启发式规则
        complexity = 1
        
        # 基于关键词评估
        indicators = {
            3: ["修改", "update", "fix simple", "添加简单", "优化简单"],
            5: ["实现功能", "添加功能", "add feature", "implement"],
            7: ["重构", "refactor", "redesign", "优化架构", "设计模式"],
            9: ["多模块", "multi-module", "architecture redesign", "系统重构"],
        }
        
        goal_lower = goal.lower()
        for level, keywords in indicators.items():
            if any(kw in goal_lower for kw in keywords):
                complexity = max(complexity, level)
        
        # 基于任务长度评估
        if len(goal) > 200:
            complexity += 1
        if len(goal) > 500:
            complexity += 1
        
        # 基于子任务数量评估（逗号、分号分隔）
        subtask_count = goal.count(",") + goal.count(";") + goal.count("\n")
        if subtask_count > 3:
            complexity += 1
        if subtask_count > 6:
            complexity += 1
        
        return min(10, complexity)


# 便捷函数
async def run_with_agents(goal: str, api_key: Optional[str] = None, mode: Optional[str] = None) -> str:
    """
    使用多 Agent 系统运行任务
    
    Args:
        goal: 任务目标
        api_key: LLM API 密钥
        mode: 模式 - "auto" | "single" | "multi"
    
    Returns:
        执行结果
    
    Example:
        >>> result = await run_with_agents("重构用户认证模块")
        >>> result = await run_with_agents("添加登录功能", mode="multi")
    """
    runner = MultiAgentRunner(api_key=api_key)
    return await runner.run(goal, force_mode=mode)


def run_sync(goal: str, api_key: Optional[str] = None, mode: Optional[str] = None) -> str:
    """
    同步版本的多 Agent 运行
    
    Example:
        >>> result = run_sync("分析代码并添加测试")
    """
    return asyncio.run(run_with_agents(goal, api_key, mode))


# 直接运行特定类型的 Specialist Agent
async def run_specialist(agent_type: str, task: str, api_key: Optional[str] = None) -> str:
    """
    运行特定类型的 Specialist Agent
    
    Args:
        agent_type: Agent 类型 - "code", "test", "doc", "review", "analyze", "refactor", "debug"
        task: 任务描述
        api_key: LLM API 密钥
    
    Returns:
        执行结果
    
    Example:
        >>> result = await run_specialist("test", "为 user_service.py 添加单元测试")
        >>> result = await run_specialist("review", "审查 auth.py 的代码质量")
    """
    from src.agents.specialist_agents import create_agent, SubTask, AgentType
    
    llm = LLMClient(api_key=api_key)
    agent_type_enum = AgentType(agent_type)
    agent = create_agent(agent_type_enum, llm)
    
    subtask = SubTask(
        id="direct_task",
        description=task,
        agent_type=agent_type_enum,
        dependencies=[]
    )
    
    result = await agent.run(subtask)
    return result.output


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        test_goal = " ".join(sys.argv[1:])
    else:
        test_goal = "分析 src/agents/agent.py 的代码结构，然后为其添加单元测试"
    
    print(f"Testing Multi-Agent system with goal:")
    print(f"  {test_goal}")
    print("-" * 60)
    
    result = run_sync(test_goal)
    print(result)
