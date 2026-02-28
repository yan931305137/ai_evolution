"""
动态 Agent 管理工具

提供创建和管理动态 Agent 的工具函数
"""
import logging
from typing import Optional, List

from src.utils.llm import LLMClient
from src.storage.memory import memory

logger = logging.getLogger(__name__)

# 全局 LLM 客户端（将在 AutoAgent 中设置）
_global_llm: Optional[LLMClient] = None
_global_factory = None


def _get_factory(llm: LLMClient):
    """延迟导入避免循环依赖"""
    global _global_factory
    if _global_factory is None:
        from src.agents.dynamic_agent_factory import DynamicAgentFactory
        _global_factory = DynamicAgentFactory(llm)
    return _global_factory


def set_global_llm(llm: LLMClient):
    """设置全局 LLM 客户端"""
    global _global_llm
    _global_llm = llm


def _get_llm() -> LLMClient:
    """获取 LLM 客户端"""
    global _global_llm
    if _global_llm is None:
        _global_llm = LLMClient()
    return _global_llm


def spawn_agent(task_description: str, agent_name: Optional[str] = None) -> str:
    """
    创建一个新的 Specialist Agent 来处理特定类型的任务。
    
    当你需要一个具有特定专业知识的 Agent 时调用此函数。
    Agent 会根据任务描述自动分析所需能力并生成相应的 Specialist。
    
    Args:
        task_description: 任务描述，用于确定 Agent 的专业方向和能力
        agent_name: 可选的 Agent 名称（如果不提供则自动生成）
    
    Returns:
        agent_id: 新创建的 Agent ID，用于后续委派任务
        
    Example:
        >>> agent_id = spawn_agent("编写单元测试和集成测试")
        >>> agent_id = spawn_agent("重构遗留代码", agent_name="legacy_refactorer")
    """
    try:
        llm = _get_llm()
        factory = _get_factory(llm)
        
        # 如果提供了名称，修改任务描述以包含名称提示
        if agent_name:
            task_description = f"[{agent_name}] {task_description}"
        
        agent_id = factory.create_agent(task_description)
        
        logger.info(f"Spawned new agent: {agent_id}")
        return f"Agent created successfully. ID: {agent_id}"
        
    except Exception as e:
        logger.error(f"Failed to spawn agent: {e}")
        return f"Error spawning agent: {str(e)}"


def delegate_task(agent_id: str, subtask: str, context: Optional[dict] = None) -> str:
    """
    委派任务给之前创建的 Agent。
    
    使用 spawn_agent 创建的 Agent ID 来分配具体任务。
    Agent 会独立执行该任务并返回结果。
    
    Args:
        agent_id: spawn_agent 返回的 Agent ID
        subtask: 具体的子任务描述
        context: 可选的上下文信息（如相关文件路径、前置任务结果等）
    
    Returns:
        任务执行结果
        
    Example:
        >>> result = delegate_task("testing_specialist", "为 auth.py 添加单元测试")
        >>> result = delegate_task("doc_agent", "生成 API 文档", 
        ...                        context={"files": ["api.py", "models.py"]})
    """
    try:
        llm = _get_llm()
        factory = _get_factory(llm)
        
        # 获取 Agent 实例
        agent = factory.get_agent(agent_id, llm)
        if not agent:
            return f"Error: Agent '{agent_id}' not found. Use spawn_agent() to create it first."
        
        # 延迟导入避免循环依赖
        from src.agents.specialist_agents import SubTask
        
        # 创建子任务
        subtask_obj = SubTask(
            id=f"task_{agent_id}_{hash(subtask) % 10000}",
            description=subtask,
            agent_type=agent.agent_type,
            context=context or {}
        )
        
        logger.info(f"Delegating task to {agent_id}: {subtask[:50]}...")
        
        # 执行子任务（同步执行，因为工具函数是同步的）
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(agent.run(subtask_obj))
        
        # 更新统计
        factory.update_agent_stats(agent_id, result.success)
        
        # 存储到记忆
        memory.add_memory(
            content=f"Agent {agent_id} executed: {subtask}\nResult: {result.output[:200]}",
            context={
                "agent_id": agent_id,
                "task": subtask,
                "success": result.success,
                "type": "delegated_task"
            }
        )
        
        status = "✓ Success" if result.success else "✗ Failed"
        output = f"""[{status}] Agent '{agent_id}' completed task

Task: {subtask}
Execution Time: {result.execution_time:.1f}s
Steps Taken: {result.steps_taken}

Output:
{result.output}
"""
        
        logger.info(f"Task completed by {agent_id}: {result.success}")
        return output
        
    except Exception as e:
        logger.error(f"Failed to delegate task: {e}")
        return f"Error delegating task: {str(e)}"


def list_spawned_agents() -> str:
    """
    列出所有已创建的动态 Agent。
    
    Returns:
        Agent 列表和它们的状态信息
        
    Example:
        >>> print(list_spawned_agents())
    """
    try:
        llm = _get_llm()
        factory = _get_factory(llm)
        agents = factory.list_agents()
        
        if not agents:
            return "No dynamic agents have been created yet.\nUse spawn_agent() to create one."
        
        lines = ["=" * 60, "Dynamic Agent Registry", "=" * 60, ""]
        
        for agent in agents:
            success_rate = (agent.success_count / agent.task_count * 100) if agent.task_count > 0 else 0
            lines.append(f"Agent ID: {agent.agent_id}")
            lines.append(f"  Description: {agent.description}")
            lines.append(f"  Capabilities: {', '.join(agent.capabilities[:3])}")
            lines.append(f"  Created: {agent.created_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"  Tasks: {agent.task_count} (Success: {agent.success_count}, {success_rate:.0f}%)")
            lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return f"Error listing agents: {str(e)}"


def get_agent_info(agent_id: str) -> str:
    """
    获取特定 Agent 的详细信息。
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Agent 详细信息
    """
    try:
        llm = _get_llm()
        factory = _get_factory(llm)
        info = factory.get_agent_info(agent_id)
        
        if not info:
            return f"Agent '{agent_id}' not found."
        
        success_rate = (info.success_count / info.task_count * 100) if info.task_count > 0 else 0
        
        output = f"""Agent ID: {info.agent_id}
Name: {info.name}
Description: {info.description}

Capabilities:
{chr(10).join(f"  - {cap}" for cap in info.capabilities)}

Statistics:
  - Created: {info.created_at.strftime('%Y-%m-%d %H:%M:%S')}
  - Tasks Completed: {info.task_count}
  - Success Rate: {success_rate:.1f}% ({info.success_count}/{info.task_count})
  - File: {info.file_path}
"""
        return output
        
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}")
        return f"Error getting agent info: {str(e)}"


def terminate_agent(agent_id: str) -> str:
    """
    终止并删除一个动态 Agent。
    
    Args:
        agent_id: Agent ID
        
    Returns:
        操作结果
    """
    try:
        llm = _get_llm()
        factory = _get_factory(llm)
        
        if factory.delete_agent(agent_id):
            return f"Agent '{agent_id}' has been terminated and deleted."
        else:
            return f"Agent '{agent_id}' not found."
            
    except Exception as e:
        logger.error(f"Failed to terminate agent: {e}")
        return f"Error terminating agent: {str(e)}"


def spawn_agents_for_project(project_description: str) -> str:
    """
    为整个项目创建一组 Specialist Agent。
    
    根据项目描述自动创建所需的多个 Agent。
    
    Args:
        project_description: 项目描述
        
    Returns:
        创建的 Agent 列表
    """
    try:
        llm = _get_llm()
        
        # 分析项目需求
        prompt = f"""Analyze this project and determine what Specialist Agents are needed:

Project: {project_description}

List the required agents as JSON:
{{
    "agents": [
        {{
            "name": "agent_name",
            "description": "What this agent will do",
            "focus": "Specific focus area"
        }}
    ]
}}

Suggest 2-5 agents that would work together effectively."""
        
        response = llm.generate([{"role": "user", "content": prompt}])
        import json
        data = json.loads(response.strip())
        
        created_agents = []
        for agent_spec in data.get("agents", []):
            desc = f"[{agent_spec['name']}] {agent_spec['description']}. Focus: {agent_spec['focus']}"
            result = spawn_agent(desc, agent_name=agent_spec['name'])
            if "Agent created successfully" in result:
                agent_id = result.split("ID: ")[1]
                created_agents.append(agent_id)
        
        return f"Created {len(created_agents)} agents for project:\n" + "\n".join(f"  - {aid}" for aid in created_agents)
        
    except Exception as e:
        logger.error(f"Failed to spawn agents for project: {e}")
        return f"Error: {str(e)}"
