"""
Multi-Agent Collaboration System - 多Agent协作架构

实现多个Agent之间的协作与通信机制

核心概念：
- Agent角色：每个Agent有专门的角色和能力
- 消息传递：Agent间通过消息队列通信
- 任务分配：协调者将任务分配给合适的Agent
- 结果聚合：合并多个Agent的结果
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class AgentRole(Enum):
    """Agent角色类型"""
    COORDINATOR = "coordinator"      # 协调者：负责任务分配和结果聚合
    PLANNER = "planner"              # 规划者：负责制定计划
    EXECUTOR = "executor"            # 执行者：负责执行任务
    RESEARCHER = "researcher"        # 研究者：负责信息收集
    CRITIC = "critic"                # 批判者：负责审查和反馈
    SPECIALIST = "specialist"        # 专家：特定领域的专家


class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGNMENT = "task_assignment"      # 任务分配
    TASK_RESULT = "task_result"              # 任务结果
    REQUEST_HELP = "request_help"            # 请求帮助
    BROADCAST = "broadcast"                  # 广播消息
    DIRECT_MESSAGE = "direct_message"        # 直接消息
    STATUS_UPDATE = "status_update"          # 状态更新


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"              # 等待中
    ASSIGNED = "assigned"            # 已分配
    IN_PROGRESS = "in_progress"      # 进行中
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    NEEDS_REVIEW = "needs_review"    # 需要审查


@dataclass
class AgentMessage:
    """Agent间消息"""
    id: str
    sender_id: str
    receiver_id: Optional[str]      # None表示广播
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5               # 1-10，数字越小优先级越高
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }


@dataclass
class CollaborativeTask:
    """协作任务"""
    id: str
    description: str
    required_roles: List[AgentRole]  # 需要的角色
    assigned_agents: Dict[AgentRole, str] = field(default_factory=dict)  # role -> agent_id
    subtasks: List[Dict] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    parent_task_id: Optional[str] = None  # 父任务ID（用于任务分解）
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "required_roles": [r.value for r in self.required_roles],
            "assigned_agents": self.assigned_agents,
            "subtasks": self.subtasks,
            "status": self.status.value,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_task_id": self.parent_task_id
        }


class BaseAgent:
    """
    基础Agent类
    
    所有Agent的基类
    """
    
    def __init__(self, agent_id: str, name: str, role: AgentRole, capabilities: List[str] = None):
        self.id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.collaboration_hub: Optional['CollaborationHub'] = None
        self.is_running = False
        self.task_history: List[Dict] = []
        self.current_task: Optional[CollaborativeTask] = None
        
    async def start(self):
        """启动Agent"""
        self.is_running = True
        asyncio.create_task(self._message_loop())
        print(f"🤖 Agent '{self.name}' ({self.role.value}) 已启动")
    
    async def stop(self):
        """停止Agent"""
        self.is_running = False
        print(f"🛑 Agent '{self.name}' 已停止")
    
    async def _message_loop(self):
        """消息处理循环"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Agent {self.name} 消息处理错误: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """处理消息（子类可重写）"""
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            await self._handle_task_assignment(message)
        elif message.message_type == MessageType.REQUEST_HELP:
            await self._handle_help_request(message)
        elif message.message_type == MessageType.DIRECT_MESSAGE:
            await self._handle_direct_message(message)
    
    async def _handle_task_assignment(self, message: AgentMessage):
        """处理任务分配"""
        task_data = message.content.get("task")
        if task_data:
            task = CollaborativeTask(**task_data)
            self.current_task = task
            result = await self.execute_task(task)
            
            # 发送结果回协调者
            if self.collaboration_hub:
                await self.send_message(
                    receiver_id=message.sender_id,
                    message_type=MessageType.TASK_RESULT,
                    content={
                        "task_id": task.id,
                        "agent_id": self.id,
                        "result": result,
                        "status": "completed"
                    }
                )
    
    async def _handle_help_request(self, message: AgentMessage):
        """处理帮助请求"""
        # 默认实现：记录请求
        print(f"Agent {self.name} 收到帮助请求: {message.content}")
    
    async def _handle_direct_message(self, message: AgentMessage):
        """处理直接消息"""
        print(f"Agent {self.name} 收到消息: {message.content.get('text', '')}")
    
    async def execute_task(self, task: CollaborativeTask) -> Any:
        """
        执行任务（子类必须实现）
        
        Args:
            task: 协作任务
            
        Returns:
            任务执行结果
        """
        raise NotImplementedError("子类必须实现execute_task方法")
    
    async def send_message(self, receiver_id: Optional[str], message_type: MessageType, content: Dict):
        """
        发送消息
        
        Args:
            receiver_id: 接收者ID，None表示广播
            message_type: 消息类型
            content: 消息内容
        """
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=self.id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content
        )
        
        if self.collaboration_hub:
            await self.collaboration_hub.route_message(message)
    
    def get_info(self) -> Dict:
        """获取Agent信息"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "status": "running" if self.is_running else "stopped",
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "task_count": len(self.task_history)
        }


class CoordinatorAgent(BaseAgent):
    """
    协调者Agent
    
    负责任务分配、进度跟踪和结果聚合
    """
    
    def __init__(self, agent_id: str = None, name: str = "Coordinator"):
        super().__init__(
            agent_id=agent_id or str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.COORDINATOR,
            capabilities=["task_decomposition", "agent_coordination", "result_aggregation"]
        )
        self.tasks: Dict[str, CollaborativeTask] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}  # task_id -> {agent_id: result}
        
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.id] = agent
        agent.collaboration_hub = self.collaboration_hub
        print(f"📋 协调者注册Agent: {agent.name} ({agent.role.value})")
    
    async def create_collaborative_task(
        self,
        description: str,
        required_roles: List[AgentRole],
        decomposition_strategy: str = "auto"
    ) -> CollaborativeTask:
        """
        创建协作任务
        
        Args:
            description: 任务描述
            required_roles: 需要的角色
            decomposition_strategy: 分解策略
            
        Returns:
            协作任务
        """
        task_id = str(uuid.uuid4())[:8]
        
        # 任务分解
        subtasks = self._decompose_task(description, decomposition_strategy)
        
        task = CollaborativeTask(
            id=task_id,
            description=description,
            required_roles=required_roles,
            subtasks=subtasks
        )
        
        self.tasks[task_id] = task
        
        # 分配任务给合适的Agent
        await self._assign_task(task)
        
        return task
    
    def _decompose_task(self, description: str, strategy: str) -> List[Dict]:
        """分解任务"""
        # 简化的任务分解逻辑
        # 实际应该使用LLM或规划算法
        
        if "代码" in description or "programming" in description.lower():
            return [
                {"step": 1, "action": "analyze_requirements", "description": "分析需求"},
                {"step": 2, "action": "design_solution", "description": "设计方案"},
                {"step": 3, "action": "implement_code", "description": "编写代码"},
                {"step": 4, "action": "review_code", "description": "代码审查"}
            ]
        elif "研究" in description or "research" in description.lower():
            return [
                {"step": 1, "action": "gather_information", "description": "收集信息"},
                {"step": 2, "action": "analyze_data", "description": "分析数据"},
                {"step": 3, "action": "synthesize_findings", "description": "综合发现"}
            ]
        else:
            return [
                {"step": 1, "action": "understand_task", "description": "理解任务"},
                {"step": 2, "action": "execute_task", "description": "执行任务"},
                {"step": 3, "action": "verify_result", "description": "验证结果"}
            ]
    
    async def _assign_task(self, task: CollaborativeTask):
        """分配任务给Agent"""
        for role in task.required_roles:
            # 找到具有该角色的可用Agent
            suitable_agents = [
                agent for agent in self.agents.values()
                if agent.role == role and agent.is_running
            ]
            
            if suitable_agents:
                # 选择第一个可用的（实际应该根据负载和能力选择）
                selected_agent = suitable_agents[0]
                task.assigned_agents[role] = selected_agent.id
                
                # 发送任务分配消息
                await self.send_message(
                    receiver_id=selected_agent.id,
                    message_type=MessageType.TASK_ASSIGNMENT,
                    content={
                        "task": task.to_dict(),
                        "role": role.value
                    }
                )
                
                task.status = TaskStatus.ASSIGNED
                print(f"📤 任务 '{task.id}' 分配给 {selected_agent.name} (角色: {role.value})")
    
    async def _handle_message(self, message: AgentMessage):
        """处理消息"""
        await super()._handle_message(message)
        
        if message.message_type == MessageType.TASK_RESULT:
            await self._handle_task_result(message)
    
    async def _handle_task_result(self, message: AgentMessage):
        """处理任务结果"""
        task_id = message.content.get("task_id")
        agent_id = message.content.get("agent_id")
        result = message.content.get("result")
        
        if task_id not in self.task_results:
            self.task_results[task_id] = {}
        
        self.task_results[task_id][agent_id] = result
        
        # 检查是否所有Agent都完成了
        task = self.tasks.get(task_id)
        if task:
            completed_count = len(self.task_results.get(task_id, {}))
            required_count = len(task.assigned_agents)
            
            if completed_count >= required_count:
                # 聚合结果
                aggregated_result = self._aggregate_results(task_id)
                task.results = aggregated_result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                
                print(f"✅ 任务 '{task_id}' 完成！结果已聚合")
                print(f"   参与Agent: {list(self.task_results[task_id].keys())}")
    
    def _aggregate_results(self, task_id: str) -> Dict:
        """聚合多个Agent的结果"""
        results = self.task_results.get(task_id, {})
        
        # 简化的聚合策略
        return {
            "task_id": task_id,
            "contributing_agents": list(results.keys()),
            "individual_results": results,
            "summary": self._generate_summary(results),
            "aggregated_at": datetime.now().isoformat()
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """生成结果摘要"""
        # 简化的摘要生成
        agent_count = len(results)
        return f"来自{agent_count}个Agent的协作结果"
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task": task.to_dict(),
            "completed_agents": list(self.task_results.get(task_id, {}).keys()),
            "progress": len(self.task_results.get(task_id, {})) / max(len(task.assigned_agents), 1)
        }
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [task.to_dict() for task in self.tasks.values()]


class CollaborationHub:
    """
    协作中心
    
    管理所有Agent的通信和协调
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.coordinator: Optional[CoordinatorAgent] = None
        self.message_history: List[AgentMessage] = []
        self.is_running = False
    
    def set_coordinator(self, coordinator: CoordinatorAgent):
        """设置协调者"""
        self.coordinator = coordinator
        coordinator.collaboration_hub = self
        self.agents[coordinator.id] = coordinator
    
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.id] = agent
        agent.collaboration_hub = self
        
        # 同时注册到协调者
        if self.coordinator:
            self.coordinator.register_agent(agent)
    
    async def route_message(self, message: AgentMessage):
        """路由消息到目标Agent"""
        self.message_history.append(message)
        
        if message.receiver_id is None:
            # 广播消息
            for agent in self.agents.values():
                if agent.id != message.sender_id:
                    await agent.message_queue.put(message)
        else:
            # 直接消息
            target_agent = self.agents.get(message.receiver_id)
            if target_agent:
                await target_agent.message_queue.put(message)
    
    async def start(self):
        """启动所有Agent"""
        self.is_running = True
        
        # 启动协调者
        if self.coordinator:
            await self.coordinator.start()
        
        # 启动其他Agent
        for agent in self.agents.values():
            if agent.id != (self.coordinator.id if self.coordinator else None):
                await agent.start()
        
        print(f"🚀 协作中心已启动，共{len(self.agents)}个Agent")
    
    async def stop(self):
        """停止所有Agent"""
        self.is_running = False
        
        for agent in self.agents.values():
            await agent.stop()
        
        print("🛑 协作中心已停止")
    
    async def create_task(self, description: str, required_roles: List[AgentRole]) -> str:
        """
        创建协作任务
        
        Args:
            description: 任务描述
            required_roles: 需要的角色列表
            
        Returns:
            任务ID
        """
        if not self.coordinator:
            raise ValueError("未设置协调者")
        
        task = await self.coordinator.create_collaborative_task(
            description=description,
            required_roles=required_roles
        )
        
        return task.id
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "total_agents": len(self.agents),
            "running_agents": sum(1 for a in self.agents.values() if a.is_running),
            "coordinator": self.coordinator.get_info() if self.coordinator else None,
            "agents": [agent.get_info() for agent in self.agents.values()],
            "total_messages": len(self.message_history),
            "recent_messages": [m.to_dict() for m in self.message_history[-10:]]
        }


# 具体Agent实现示例
class PlannerAgent(BaseAgent):
    """规划者Agent"""
    
    def __init__(self, agent_id: str = None, name: str = "Planner"):
        super().__init__(
            agent_id=agent_id or str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.PLANNER,
            capabilities=["task_planning", "strategy_design", "goal_decomposition"]
        )
    
    async def execute_task(self, task: CollaborativeTask) -> Any:
        """执行规划任务"""
        print(f"📝 PlannerAgent '{self.name}' 正在规划任务: {task.description}")
        
        # 实际应该调用规划算法或LLM
        plan = {
            "steps": task.subtasks,
            "estimated_time": len(task.subtasks) * 10,  # 估算时间
            "resources_needed": ["knowledge_base", "planning_algorithm"]
        }
        
        self.task_history.append({
            "task_id": task.id,
            "plan": plan,
            "completed_at": datetime.now().isoformat()
        })
        
        return plan


class ExecutorAgent(BaseAgent):
    """执行者Agent"""
    
    def __init__(self, agent_id: str = None, name: str = "Executor"):
        super().__init__(
            agent_id=agent_id or str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.EXECUTOR,
            capabilities=["code_execution", "file_operation", "tool_usage"]
        )
    
    async def execute_task(self, task: CollaborativeTask) -> Any:
        """执行具体任务"""
        print(f"⚙️ ExecutorAgent '{self.name}' 正在执行任务: {task.description}")
        
        # 实际应该调用工具执行
        results = []
        for subtask in task.subtasks:
            # 模拟执行
            result = {
                "subtask": subtask,
                "status": "completed",
                "output": f"执行了 {subtask['action']}"
            }
            results.append(result)
        
        self.task_history.append({
            "task_id": task.id,
            "results": results,
            "completed_at": datetime.now().isoformat()
        })
        
        return results


class CriticAgent(BaseAgent):
    """批判者Agent"""
    
    def __init__(self, agent_id: str = None, name: str = "Critic"):
        super().__init__(
            agent_id=agent_id or str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.CRITIC,
            capabilities=["code_review", "quality_assessment", "risk_analysis"]
        )
    
    async def execute_task(self, task: CollaborativeTask) -> Any:
        """执行审查任务"""
        print(f"🔍 CriticAgent '{self.name}' 正在审查: {task.description}")
        
        # 实际应该进行真正的审查
        review = {
            "issues_found": [],
            "suggestions": ["建议添加更多注释", "考虑异常处理"],
            "quality_score": 0.85,
            "approved": True
        }
        
        self.task_history.append({
            "task_id": task.id,
            "review": review,
            "completed_at": datetime.now().isoformat()
        })
        
        return review


# 便捷函数
async def create_collaboration_system() -> CollaborationHub:
    """
    创建并配置协作系统
    
    Returns:
        配置好的CollaborationHub
    """
    hub = CollaborationHub()
    
    # 创建协调者
    coordinator = CoordinatorAgent(name="MainCoordinator")
    hub.set_coordinator(coordinator)
    
    # 创建专业Agent
    planner = PlannerAgent(name="TaskPlanner")
    executor = ExecutorAgent(name="CodeExecutor")
    critic = CriticAgent(name="QualityCritic")
    
    # 注册Agent
    hub.register_agent(planner)
    hub.register_agent(executor)
    hub.register_agent(critic)
    
    return hub
