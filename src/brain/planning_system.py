"""
Brain Planning System - Brain本地规划系统

为HumanLevelBrain增加本地任务规划能力，减少对外部LLM的依赖。

核心功能：
1. 任务分解：将复杂任务分解为可执行的子任务
2. 计划生成：基于当前状态生成行动计划
3. 执行监控：跟踪计划执行进度
4. 动态调整：根据反馈调整计划
"""
import json
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 等待执行
    IN_PROGRESS = "in_progress" # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    BLOCKED = "blocked"         # 被阻塞


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 4    # 关键
    HIGH = 3        # 高
    MEDIUM = 2      # 中
    LOW = 1         # 低


@dataclass
class SubTask:
    """子任务"""
    id: str
    description: str
    action: str                     # 动作类型
    action_input: Dict[str, Any]    # 动作参数
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他子任务ID
    estimated_steps: int = 1        # 预估步骤数
    actual_steps: int = 0           # 实际执行步骤
    result: Optional[str] = None    # 执行结果
    error: Optional[str] = None     # 错误信息
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "action": self.action,
            "action_input": self.action_input,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "estimated_steps": self.estimated_steps,
            "actual_steps": self.actual_steps,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class Plan:
    """计划"""
    id: str
    goal: str                       # 目标描述
    subtasks: List[SubTask]         # 子任务列表
    status: TaskStatus = TaskStatus.PENDING
    current_step: int = 0           # 当前执行到的步骤
    total_estimated_steps: int = 0  # 预估总步骤
    context: Dict[str, Any] = field(default_factory=dict)  # 计划上下文
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "status": self.status.value,
            "current_step": self.current_step,
            "total_estimated_steps": self.total_estimated_steps,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_progress(self) -> float:
        """获取计划进度（0-1）"""
        if not self.subtasks:
            return 0.0
        completed = sum(1 for st in self.subtasks if st.status == TaskStatus.COMPLETED)
        return completed / len(self.subtasks)
    
    def get_next_executable_task(self) -> Optional[SubTask]:
        """获取下一个可执行的子任务（依赖已满足）"""
        for subtask in self.subtasks:
            if subtask.status != TaskStatus.PENDING:
                continue
            
            # 检查依赖是否满足
            deps_satisfied = all(
                self._get_subtask_by_id(dep_id).status == TaskStatus.COMPLETED
                for dep_id in subtask.dependencies
            )
            
            if deps_satisfied:
                return subtask
        
        return None
    
    def _get_subtask_by_id(self, task_id: str) -> Optional[SubTask]:
        """通过ID获取子任务"""
        for st in self.subtasks:
            if st.id == task_id:
                return st
        return None


class BrainPlanner:
    """
    Brain规划器
    
    为HumanLevelBrain提供本地任务规划能力
    """
    
    def __init__(self, brain_reference=None):
        """
        初始化规划器
        
        Args:
            brain_reference: 对Brain实例的引用，用于获取记忆和情感状态
        """
        self.brain = brain_reference
        self.plans: Dict[str, Plan] = {}  # 存储所有计划
        self.current_plan: Optional[Plan] = None
        
        # 任务模板库
        self.task_templates = self._load_task_templates()
        
        # 规划策略
        self.planning_strategies = {
            "sequential": self._plan_sequential,
            "parallel": self._plan_parallel,
            "hierarchical": self._plan_hierarchical,
        }
    
    def _load_task_templates(self) -> Dict[str, Any]:
        """加载任务模板库"""
        return {
            "file_operation": {
                "pattern": r"(读取|写入|修改|删除|创建).{0,10}(文件|文档)",
                "steps": [
                    {"action": "verify_path", "description": "验证文件路径"},
                    {"action": "check_permission", "description": "检查操作权限"},
                    {"action": "execute_operation", "description": "执行文件操作"},
                    {"action": "verify_result", "description": "验证操作结果"}
                ]
            },
            "code_analysis": {
                "pattern": r"(分析|检查|审查).{0,10}(代码|程序|bug)",
                "steps": [
                    {"action": "scan_files", "description": "扫描相关文件"},
                    {"action": "identify_issues", "description": "识别潜在问题"},
                    {"action": "analyze_impact", "description": "分析问题影响"},
                    {"action": "suggest_fixes", "description": "提供修复建议"}
                ]
            },
            "search_query": {
                "pattern": r"(搜索|查找|查询).{0,20}(信息|资料|数据)",
                "steps": [
                    {"action": "parse_query", "description": "解析搜索意图"},
                    {"action": "select_source", "description": "选择搜索源"},
                    {"action": "execute_search", "description": "执行搜索"},
                    {"action": "summarize_results", "description": "总结搜索结果"}
                ]
            },
            "decision_making": {
                "pattern": r"(选择|决定|比较).{0,20}(方案|选项|方法)",
                "steps": [
                    {"action": "identify_options", "description": "识别可选方案"},
                    {"action": "evaluate_criteria", "description": "评估决策标准"},
                    {"action": "compare_options", "description": "比较各方案优劣"},
                    {"action": "recommend_choice", "description": "给出推荐选择"}
                ]
            },
            "learning_task": {
                "pattern": r"(学习|理解|掌握).{0,20}(知识|概念|技能)",
                "steps": [
                    {"action": "assess_knowledge", "description": "评估现有知识"},
                    {"action": "identify_gaps", "description": "识别知识缺口"},
                    {"action": "gather_materials", "description": "收集学习资料"},
                    {"action": "create_plan", "description": "制定学习计划"}
                ]
            }
        }
    
    def plan(self, goal: str, context: Optional[Dict] = None, strategy: str = "auto") -> Plan:
        """
        为给定目标制定计划
        
        Args:
            goal: 目标描述
            context: 额外上下文信息
            strategy: 规划策略 (sequential/parallel/hierarchical/auto)
            
        Returns:
            Plan对象
        """
        import uuid
        
        # 创建新计划
        plan_id = str(uuid.uuid4())[:8]
        
        # 分析目标类型
        task_type = self._analyze_task_type(goal)
        
        # 获取相关记忆
        relevant_memories = []
        if self.brain:
            try:
                memories = self.brain.recall_memories(query=goal, top_k=3)
                relevant_memories = [m.content for m in memories if hasattr(m, 'content')]
            except:
                pass
        
        # 选择规划策略
        if strategy == "auto":
            strategy = self._select_strategy(goal, task_type)
        
        # 生成子任务
        subtasks = self._generate_subtasks(
            goal=goal,
            task_type=task_type,
            context=context or {},
            memories=relevant_memories
        )
        
        # 创建计划
        plan = Plan(
            id=plan_id,
            goal=goal,
            subtasks=subtasks,
            context={
                "task_type": task_type,
                "strategy": strategy,
                "relevant_memories": relevant_memories,
                **(context or {})
            },
            total_estimated_steps=sum(st.estimated_steps for st in subtasks)
        )
        
        # 存储计划
        self.plans[plan_id] = plan
        self.current_plan = plan
        
        return plan
    
    def _analyze_task_type(self, goal: str) -> str:
        """分析任务类型"""
        goal_lower = goal.lower()
        
        for task_type, template in self.task_templates.items():
            if re.search(template["pattern"], goal_lower):
                return task_type
        
        # 默认类型
        return "general"
    
    def _select_strategy(self, goal: str, task_type: str) -> str:
        """选择规划策略"""
        # 根据任务类型选择策略
        if task_type in ["file_operation", "code_analysis"]:
            return "sequential"  # 这些任务通常需要顺序执行
        elif task_type in ["search_query"]:
            return "parallel"    # 搜索可以并行进行
        else:
            return "hierarchical"  # 默认使用分层规划
    
    def _generate_subtasks(
        self,
        goal: str,
        task_type: str,
        context: Dict,
        memories: List[str]
    ) -> List[SubTask]:
        """生成子任务列表"""
        import uuid
        
        subtasks = []
        
        # 如果有模板，使用模板
        if task_type in self.task_templates:
            template = self.task_templates[task_type]
            for i, step in enumerate(template["steps"]):
                subtask = SubTask(
                    id=f"{task_type}_{i}",
                    description=step["description"],
                    action=step["action"],
                    action_input={"goal": goal, "step_index": i},
                    priority=TaskPriority.MEDIUM,
                    estimated_steps=1
                )
                subtasks.append(subtask)
        else:
            # 通用任务分解
            subtasks = self._decompose_generic_task(goal, context, memories)
        
        return subtasks
    
    def _decompose_generic_task(
        self,
        goal: str,
        context: Dict,
        memories: List[str]
    ) -> List[SubTask]:
        """通用任务分解"""
        import uuid
        
        # 基于启发式规则分解任务
        subtasks = []
        
        # 步骤1: 理解任务
        subtasks.append(SubTask(
            id="step_1",
            description="理解任务目标和要求",
            action="analyze_goal",
            action_input={"goal": goal},
            priority=TaskPriority.HIGH,
            estimated_steps=1
        ))
        
        # 步骤2: 收集信息
        subtasks.append(SubTask(
            id="step_2",
            description="收集相关信息和资源",
            action="gather_info",
            action_input={"goal": goal, "memories": memories},
            priority=TaskPriority.HIGH,
            dependencies=["step_1"],
            estimated_steps=2
        ))
        
        # 步骤3: 制定方案
        subtasks.append(SubTask(
            id="step_3",
            description="制定执行方案",
            action="formulate_plan",
            action_input={"goal": goal},
            priority=TaskPriority.MEDIUM,
            dependencies=["step_2"],
            estimated_steps=1
        ))
        
        # 步骤4: 执行方案
        subtasks.append(SubTask(
            id="step_4",
            description="执行方案并监控进度",
            action="execute_plan",
            action_input={"goal": goal},
            priority=TaskPriority.MEDIUM,
            dependencies=["step_3"],
            estimated_steps=3
        ))
        
        # 步骤5: 验证结果
        subtasks.append(SubTask(
            id="step_5",
            description="验证执行结果",
            action="verify_result",
            action_input={"goal": goal},
            priority=TaskPriority.HIGH,
            dependencies=["step_4"],
            estimated_steps=1
        ))
        
        return subtasks
    
    def execute_next_step(self, plan_id: Optional[str] = None) -> Tuple[Optional[SubTask], Dict]:
        """
        执行计划的下一步
        
        Args:
            plan_id: 计划ID，默认为当前计划
            
        Returns:
            (子任务, 执行结果)
        """
        plan = self.plans.get(plan_id) if plan_id else self.current_plan
        if not plan:
            return None, {"error": "No plan found"}
        
        # 获取下一个可执行任务
        subtask = plan.get_next_executable_task()
        if not subtask:
            # 检查是否全部完成
            if all(st.status == TaskStatus.COMPLETED for st in plan.subtasks):
                plan.status = TaskStatus.COMPLETED
                plan.completed_at = datetime.now()
                return None, {"status": "plan_completed", "progress": 1.0}
            else:
                return None, {"status": "blocked", "message": "No executable task available"}
        
        # 更新任务状态
        subtask.status = TaskStatus.IN_PROGRESS
        plan.status = TaskStatus.IN_PROGRESS
        if not plan.started_at:
            plan.started_at = datetime.now()
        
        # 这里应该调用实际的工具执行
        # 简化版本：模拟执行
        result = self._simulate_execution(subtask)
        
        # 更新任务状态
        subtask.actual_steps += 1
        if result.get("success"):
            subtask.status = TaskStatus.COMPLETED
            subtask.result = result.get("output")
            subtask.completed_at = datetime.now()
        else:
            subtask.status = TaskStatus.FAILED
            subtask.error = result.get("error")
        
        plan.current_step += 1
        
        return subtask, result
    
    def _simulate_execution(self, subtask: SubTask) -> Dict:
        """模拟任务执行（实际应该调用工具）"""
        # 在实际实现中，这里应该根据action调用相应的工具
        return {
            "success": True,
            "output": f"Executed {subtask.action}: {subtask.description}",
            "action": subtask.action,
            "action_input": subtask.action_input
        }
    
    def get_plan_status(self, plan_id: Optional[str] = None) -> Dict:
        """获取计划状态"""
        plan = self.plans.get(plan_id) if plan_id else self.current_plan
        if not plan:
            return {"error": "Plan not found"}
        
        return {
            "plan_id": plan.id,
            "goal": plan.goal,
            "status": plan.status.value,
            "progress": plan.get_progress(),
            "current_step": plan.current_step,
            "total_steps": len(plan.subtasks),
            "subtasks_summary": [
                {
                    "id": st.id,
                    "description": st.description,
                    "status": st.status.value
                }
                for st in plan.subtasks
            ]
        }
    
    def adjust_plan(self, plan_id: str, adjustment: Dict) -> bool:
        """
        根据反馈调整计划
        
        Args:
            plan_id: 计划ID
            adjustment: 调整指令
            
        Returns:
            是否调整成功
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        
        adjustment_type = adjustment.get("type")
        
        if adjustment_type == "add_task":
            # 添加新任务
            new_task = SubTask(
                id=adjustment.get("task_id", f"added_{len(plan.subtasks)}"),
                description=adjustment.get("description", ""),
                action=adjustment.get("action", "unknown"),
                action_input=adjustment.get("action_input", {}),
                priority=TaskPriority(adjustment.get("priority", 2))
            )
            plan.subtasks.append(new_task)
            
        elif adjustment_type == "remove_task":
            # 移除任务
            task_id = adjustment.get("task_id")
            plan.subtasks = [st for st in plan.subtasks if st.id != task_id]
            
        elif adjustment_type == "reorder":
            # 重新排序（通过调整dependencies实现）
            pass
        
        return True
    
    def _plan_sequential(self, goal: str, context: Dict) -> List[SubTask]:
        """顺序规划策略"""
        return self._decompose_generic_task(goal, context, [])
    
    def _plan_parallel(self, goal: str, context: Dict) -> List[SubTask]:
        """并行规划策略"""
        # 创建可以并行执行的子任务
        subtasks = self._decompose_generic_task(goal, context, [])
        # 移除依赖关系，使任务可以并行执行
        for st in subtasks:
            st.dependencies = []
        return subtasks
    
    def _plan_hierarchical(self, goal: str, context: Dict) -> List[SubTask]:
        """分层规划策略"""
        # 先进行高层规划，再细化
        return self._decompose_generic_task(goal, context, [])


# 集成到HumanLevelBrain的扩展类
class PlanningCapability:
    """
    规划能力扩展
    
    可以mixin到HumanLevelBrain中
    """
    
    def __init__(self):
        self.planner = None
    
    def enable_planning(self):
        """启用规划能力"""
        self.planner = BrainPlanner(brain_reference=self)
        return self
    
    def plan_task(self, goal: str, **kwargs) -> Plan:
        """制定任务计划"""
        if not self.planner:
            self.enable_planning()
        return self.planner.plan(goal, **kwargs)
    
    def execute_plan_step(self, plan_id: Optional[str] = None):
        """执行计划步骤"""
        if not self.planner:
            return None, {"error": "Planner not enabled"}
        return self.planner.execute_next_step(plan_id)
    
    def get_plan_progress(self, plan_id: Optional[str] = None) -> Dict:
        """获取计划进度"""
        if not self.planner:
            return {"error": "Planner not enabled"}
        return self.planner.get_plan_status(plan_id)
