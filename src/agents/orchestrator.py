"""
Agent Orchestrator - 多 Agent 协调器

负责任务分解、Agent 调度和结果汇总
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from src.utils.llm import LLMClient
from src.utils.config import cfg
from src.agents.specialist_agents import (
    AgentType, SubTask, TaskResult, BaseSpecialistAgent, create_agent
)
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行
    HYBRID = "hybrid"          # 混合模式（默认）


@dataclass
class ExecutionPlan:
    """执行计划"""
    original_goal: str
    subtasks: List[SubTask]
    execution_mode: ExecutionMode
    estimated_steps: int
    dependencies_graph: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class OrchestratorResult:
    """协调器执行结果"""
    success: bool
    final_output: str
    subtask_results: List[TaskResult]
    total_execution_time: float
    agents_used: List[AgentType]
    plan: ExecutionPlan
    summary: str


class TaskAnalyzer:
    """任务分析器 - 分析任务并决定如何分解"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def analyze(self, goal: str) -> ExecutionPlan:
        """
        分析目标并生成执行计划
        
        Args:
            goal: 用户目标
            
        Returns:
            ExecutionPlan: 执行计划
        """
        # 首先判断是否适合多 Agent 处理
        complexity = self._assess_complexity(goal)
        
        if complexity < 3:
            # 简单任务，使用单 Agent
            return self._create_single_agent_plan(goal)
        
        # 复杂任务，分解为子任务
        return self._decompose_task(goal, complexity)
    
    def _assess_complexity(self, goal: str) -> int:
        """评估任务复杂度 (1-10)"""
        # 使用 LLM 评估复杂度
        prompt = f"""Assess the complexity of this task on a scale of 1-10:

Task: {goal}

Consider:
- Number of distinct steps required
- Technical difficulty
- Number of files/modules involved
- Need for testing/documentation
- Potential for errors

Respond with ONLY a number 1-10."""
        
        try:
            response = self.llm.generate([
                {"role": "user", "content": prompt}
            ])
            complexity = int(response.strip())
            return max(1, min(10, complexity))
        except:
            # 回退到启发式评估
            return self._heuristic_complexity(goal)
    
    def _heuristic_complexity(self, goal: str) -> int:
        """启发式复杂度评估"""
        complexity = 1
        
        # 关键词匹配
        indicators = {
            2: ["修改", "update", "fix simple"],
            4: ["添加功能", "add feature", "implement"],
            6: ["重构", "refactor", "redesign", "优化", "optimize"],
            8: ["多模块", "multi-module", "architecture", "redesign system"],
            10: ["全新系统", "new system", "complete rewrite", "migrate"]
        }
        
        goal_lower = goal.lower()
        for level, keywords in indicators.items():
            if any(kw in goal_lower for kw in keywords):
                complexity = max(complexity, level)
        
        return complexity
    
    def _create_single_agent_plan(self, goal: str) -> ExecutionPlan:
        """创建单 Agent 执行计划"""
        subtask = SubTask(
            id="task_1",
            description=goal,
            agent_type=AgentType.GENERAL,
            dependencies=[],
            estimated_complexity=2
        )
        
        return ExecutionPlan(
            original_goal=goal,
            subtasks=[subtask],
            execution_mode=ExecutionMode.SEQUENTIAL,
            estimated_steps=5
        )
    
    def _decompose_task(self, goal: str, complexity: int) -> ExecutionPlan:
        """分解复杂任务"""
        prompt = f"""You are a Task Decomposition Expert. Break down this task into subtasks.

Goal: {goal}
Complexity Level: {complexity}/10

Available Agent Types:
- code: For writing/modifying code
- test: For writing tests and quality assurance
- doc: For documentation
- review: For code review and quality checks
- analyze: For analysis and understanding code
- refactor: For code refactoring
- debug: For debugging and fixing issues

Output as JSON:
{{
    "subtasks": [
        {{
            "id": "task_1",
            "description": "Clear description of subtask",
            "agent_type": "code|test|doc|review|analyze|refactor|debug",
            "dependencies": ["task_0"],
            "estimated_complexity": 1-10
        }}
    ],
    "execution_mode": "sequential|parallel|hybrid",
    "reasoning": "Why this decomposition?"
}}

Rules:
1. Each subtask should be atomic and clear
2. Set dependencies correctly (parallel when possible)
3. Choose appropriate agent_type for each subtask
4. Limit to 2-6 subtasks for manageable coordination"""
        
        try:
            response = self.llm.generate([
                {"role": "user", "content": prompt}
            ])
            
            # 解析 JSON 响应
            plan_data = json.loads(response.strip())
            
            subtasks = []
            for st_data in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    id=st_data["id"],
                    description=st_data["description"],
                    agent_type=AgentType(st_data["agent_type"]),
                    dependencies=st_data.get("dependencies", []),
                    estimated_complexity=st_data.get("estimated_complexity", 3)
                ))
            
            # 构建依赖图
            dep_graph = {st.id: st.dependencies for st in subtasks}
            
            return ExecutionPlan(
                original_goal=goal,
                subtasks=subtasks,
                execution_mode=ExecutionMode(plan_data.get("execution_mode", "hybrid")),
                estimated_steps=sum(st.estimated_complexity for st in subtasks),
                dependencies_graph=dep_graph
            )
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            # 回退到简单分解
            return self._fallback_decomposition(goal)
    
    def _fallback_decomposition(self, goal: str) -> ExecutionPlan:
        """回退分解策略"""
        subtasks = [
            SubTask(
                id="analyze",
                description=f"Analyze the requirements and current code for: {goal}",
                agent_type=AgentType.ANALYZE,
                dependencies=[],
                estimated_complexity=3
            ),
            SubTask(
                id="implement",
                description=f"Implement the solution for: {goal}",
                agent_type=AgentType.CODE,
                dependencies=["analyze"],
                estimated_complexity=5
            ),
            SubTask(
                id="test",
                description=f"Write tests for the implementation",
                agent_type=AgentType.TEST,
                dependencies=["implement"],
                estimated_complexity=3
            )
        ]
        
        return ExecutionPlan(
            original_goal=goal,
            subtasks=subtasks,
            execution_mode=ExecutionMode.HYBRID,
            estimated_steps=11,
            dependencies_graph={
                "analyze": [],
                "implement": ["analyze"],
                "test": ["implement"]
            }
        )


class AgentOrchestrator:
    """
    Agent 协调器
    
    负责任务调度、Agent 管理和结果汇总
    """
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.analyzer = TaskAnalyzer(llm)
        self.agents: Dict[AgentType, BaseSpecialistAgent] = {}
        self.results_cache: Dict[str, TaskResult] = {}
        
    def _get_or_create_agent(self, agent_type: AgentType) -> BaseSpecialistAgent:
        """获取或创建 Agent 实例"""
        if agent_type not in self.agents:
            self.agents[agent_type] = create_agent(agent_type, self.llm)
        return self.agents[agent_type]
    
    async def execute(self, goal: str) -> OrchestratorResult:
        """
        执行目标
        
        Args:
            goal: 用户目标
            
        Returns:
            OrchestratorResult: 执行结果
        """
        start_time = time.time()
        
        console.print(f"\n[bold blue]🎯 Goal:[/bold blue] {goal}")
        console.print("[dim]Analyzing task complexity...[/dim]")
        
        # 1. 分析任务并生成计划
        plan = self.analyzer.analyze(goal)
        
        console.print(f"[green]✓[/green] Task complexity: {plan.estimated_steps} estimated steps")
        console.print(f"[green]✓[/green] Execution mode: {plan.execution_mode.value}")
        console.print(f"[green]✓[/green] Subtasks: {len(plan.subtasks)}")
        
        for st in plan.subtasks:
            console.print(f"  - [{st.agent_type.value}] {st.description[:50]}...")
        
        # 2. 执行计划
        if plan.execution_mode == ExecutionMode.SEQUENTIAL:
            results = await self._execute_sequential(plan.subtasks)
        elif plan.execution_mode == ExecutionMode.PARALLEL:
            results = await self._execute_parallel(plan.subtasks)
        else:  # HYBRID
            results = await self._execute_hybrid(plan)
        
        # 3. 汇总结果
        final_result = self._synthesize_results(goal, results, plan)
        final_result.total_execution_time = time.time() - start_time
        
        # 4. 输出总结
        self._print_summary(final_result)
        
        return final_result
    
    async def _execute_sequential(self, subtasks: List[SubTask]) -> List[TaskResult]:
        """顺序执行子任务"""
        results = []
        context = {}
        
        for subtask in subtasks:
            # 添加上下文
            subtask.context.update(context)
            
            agent = self._get_or_create_agent(subtask.agent_type)
            result = await agent.run(subtask)
            results.append(result)
            
            # 更新上下文
            if result.success:
                context[f"result_{subtask.id}"] = result.output
            
            # 失败时终止
            if not result.success:
                console.print(f"[red]✗ Subtask {subtask.id} failed, stopping.[/red]")
                break
        
        return results
    
    async def _execute_parallel(self, subtasks: List[SubTask]) -> List[TaskResult]:
        """并行执行子任务"""
        tasks = []
        
        for subtask in subtasks:
            agent = self._get_or_create_agent(subtask.agent_type)
            tasks.append(agent.run(subtask))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(
                    success=False,
                    output=f"Exception: {str(result)}",
                    agent_type=subtasks[i].agent_type,
                    subtask=subtasks[i].description
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_hybrid(self, plan: ExecutionPlan) -> List[TaskResult]:
        """混合模式执行 - 根据依赖关系调度"""
        results = {}
        completed = set()
        remaining = {st.id: st for st in plan.subtasks}
        
        while remaining:
            # 找出可以执行的任务（依赖已满足）
            ready = [
                st for st in remaining.values()
                if all(dep in completed for dep in st.dependencies)
            ]
            
            if not ready:
                # 死锁检测
                logger.error("Dependency deadlock detected!")
                break
            
            # 并行执行就绪任务
            tasks = []
            for subtask in ready:
                # 添加上下文
                context = {f"result_{dep}": results[dep].output for dep in subtask.dependencies}
                subtask.context.update(context)
                
                agent = self._get_or_create_agent(subtask.agent_type)
                tasks.append(self._run_with_tracking(agent, subtask, results))
            
            await asyncio.gather(*tasks)
            
            # 更新状态
            for st in ready:
                completed.add(st.id)
                del remaining[st.id]
        
        # 按原始顺序返回结果
        return [results[st.id] for st in plan.subtasks if st.id in results]
    
    async def _run_with_tracking(
        self,
        agent: BaseSpecialistAgent,
        subtask: SubTask,
        results: Dict[str, TaskResult]
    ):
        """执行任务并跟踪结果"""
        console.print(f"[cyan]▶ Starting:[/cyan] [{subtask.agent_type.value}] {subtask.description[:40]}...")
        result = await agent.run(subtask)
        results[subtask.id] = result
        
        status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        console.print(f"{status} Completed: [{subtask.agent_type.value}] in {result.execution_time:.1f}s")
    
    def _synthesize_results(
        self,
        goal: str,
        results: List[TaskResult],
        plan: ExecutionPlan
    ) -> OrchestratorResult:
        """汇总所有子任务结果"""
        success = all(r.success for r in results)
        
        # 收集使用的 Agent 类型
        agents_used = list(set(r.agent_type for r in results))
        
        # 构建最终输出
        outputs = []
        for i, result in enumerate(results, 1):
            status = "✓" if result.success else "✗"
            outputs.append(
                f"## Step {i}: [{result.agent_type.value}]\n"
                f"Status: {status}\n"
                f"Task: {result.subtask}\n"
                f"Output:\n{result.output}\n"
            )
        
        final_output = "\n---\n".join(outputs)
        
        # 生成总结
        summary = self._generate_summary(goal, results, success)
        
        return OrchestratorResult(
            success=success,
            final_output=final_output,
            subtask_results=results,
            total_execution_time=0,  # 稍后填充
            agents_used=agents_used,
            plan=plan,
            summary=summary
        )
    
    def _generate_summary(
        self,
        goal: str,
        results: List[TaskResult],
        overall_success: bool
    ) -> str:
        """生成执行总结"""
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        agent_usage = defaultdict(int)
        for r in results:
            agent_usage[r.agent_type.value] += 1
        
        summary = f"""## Execution Summary

**Goal:** {goal}
**Overall Status:** {'✅ Success' if overall_success else '❌ Partial Failure'}
**Subtasks:** {success_count}/{total_count} completed successfully

**Agent Usage:**
"""
        for agent_type, count in sorted(agent_usage.items()):
            summary += f"- {agent_type}: {count} task(s)\n"
        
        if not overall_success:
            failed = [r for r in results if not r.success]
            summary += "\n**Failed Tasks:**\n"
            for r in failed:
                summary += f"- [{r.agent_type.value}] {r.subtask[:50]}...\n"
        
        return summary
    
    def _print_summary(self, result: OrchestratorResult):
        """打印执行总结"""
        console.print("\n" + "="*60)
        console.print(f"[bold]{'✅ All Tasks Completed' if result.success else '⚠️ Some Tasks Failed'}[/bold]")
        console.print(f"Total time: {result.total_execution_time:.1f}s")
        console.print(f"Agents used: {', '.join(a.value for a in result.agents_used)}")
        console.print("="*60)
