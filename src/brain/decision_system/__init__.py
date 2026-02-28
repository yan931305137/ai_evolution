#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策系统 (Decision System)
对应人脑: 前额叶皮层 (Prefrontal Cortex)

核心功能:
1. 工作记忆管理 - 维护当前任务上下文
2. 逻辑推理 - 基于规则的演绎和归纳
3. 决策生成 - 多选项评估和选择
4. 规划 - 目标分解和步骤生成
5. 行为抑制 - 控制冲动，选择最优而非本能反应
6. 认知灵活性 - 根据反馈调整策略
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import heapq

from src.brain.common import BrainModule, BrainRegion, DecisionOutput


@dataclass
class Option:
    """决策选项"""
    id: str
    description: str
    expected_utility: float  # 预期效用
    probability: float  # 成功概率
    cost: float  # 成本/风险
    constraints: List[str] = field(default_factory=list)


@dataclass
class Plan:
    """执行计划"""
    goal: str
    steps: List[Dict]
    estimated_duration: float
    required_resources: List[str]
    fallback_plans: List[List[Dict]] = field(default_factory=list)


class DecisionSystem(BrainModule):
    """
    决策系统
    模拟前额叶皮层的执行功能
    """
    
    def __init__(self, max_options: int = 10):
        super().__init__("DecisionSystem", BrainRegion.PREFRONTAL_CORTEX)
        
        self.max_options = max_options
        self.working_memory: Dict[str, Any] = {}  # 工作记忆
        self.decision_history: List[Dict] = []  # 决策历史
        self.current_goal: Optional[str] = None
        
        # 决策策略参数
        self.exploration_rate = 0.2  # 探索率 (epsilon-greedy)
        self.risk_tolerance = 0.5  # 风险容忍度
        
    def evaluate_options(self, options: List[Option], 
                        context: Optional[Dict] = None) -> List[Tuple[Option, float]]:
        """
        评估多个选项
        
        综合考虑:
        1. 预期效用
        2. 成功概率
        3. 成本/风险
        4. 与当前目标的匹配度
        
        Returns:
            [(Option, score), ...] 按得分排序
        """
        scored_options = []
        
        for option in options:
            # 基础得分: 期望效用 = 效用 * 概率 - 成本
            expected_value = (option.expected_utility * option.probability - 
                            option.cost * (1 - self.risk_tolerance))
            
            # 目标匹配度加成
            goal_match = 0.0
            if self.current_goal and context:
                goal_match = self._calculate_goal_match(option, self.current_goal)
            
            # 历史表现调整
            history_bonus = self._get_history_bonus(option.id)
            
            final_score = expected_value * 0.6 + goal_match * 0.3 + history_bonus * 0.1
            scored_options.append((option, final_score))
            
        # 按得分排序
        scored_options.sort(key=lambda x: x[1], reverse=True)
        return scored_options
    
    def generate_decision(self, context: Dict, 
                         options_data: Optional[List[Dict]] = None) -> DecisionOutput:
        """
        生成最优决策
        
        Args:
            context: 当前上下文，包含 situation, constraints, goal 等
            options_data: 可选选项列表，为None时自动生成
            
        Returns:
            DecisionOutput: 决策结果
        """
        # 更新工作记忆
        self.working_memory.update(context)
        self.current_goal = context.get("goal")
        
        # 生成或解析选项
        if options_data:
            options = [Option(**opt) for opt in options_data]
        else:
            options = self._generate_options_from_context(context)
            
        if not options:
            return DecisionOutput(
                action="wait",
                confidence=0.0,
                reasoning="没有可行的选项",
                expected_outcome={}
            )
            
        # 评估选项
        scored_options = self.evaluate_options(options, context)
        
        # epsilon-greedy: 小概率随机探索
        import random
        if random.random() < self.exploration_rate and len(scored_options) > 1:
            best_option, score = scored_options[1]  # 选择次优
        else:
            best_option, score = scored_options[0]
            
        # 构建决策输出
        decision = DecisionOutput(
            action=best_option.id,
            confidence=min(1.0, max(0.0, (score + 1) / 2)),  # 归一化到0-1
            reasoning=self._generate_reasoning(best_option, scored_options),
            expected_outcome={
                "utility": best_option.expected_utility,
                "probability": best_option.probability,
                "cost": best_option.cost
            },
            alternatives=[
                {"action": opt.id, "score": s} 
                for opt, s in scored_options[1:4]
            ]
        )
        
        # 记录决策历史
        self.decision_history.append({
            "timestamp": datetime.now(),
            "context": context,
            "decision": decision,
            "options_evaluated": len(options)
        })
        
        self.activate(decision.confidence)
        return decision
    
    def generate_plan(self, goal: str, 
                     constraints: Optional[List[str]] = None,
                     available_resources: Optional[List[str]] = None) -> Plan:
        """
        生成执行计划
        
        将目标分解为可执行的步骤
        
        Args:
            goal: 目标描述
            constraints: 约束条件列表
            available_resources: 可用资源
            
        Returns:
            Plan: 执行计划
        """
        constraints = constraints or []
        available_resources = available_resources or []
        
        # 目标分解 (简化版，实际可用递归分解)
        steps = self._decompose_goal(goal, constraints)
        
        # 资源需求分析
        required_resources = self._analyze_resource_requirements(steps)
        
        # 检查资源可用性
        missing_resources = [r for r in required_resources if r not in available_resources]
        if missing_resources:
            # 生成备选方案
            fallback = self._generate_fallback_plan(steps, available_resources)
        else:
            fallback = []
            
        # 估算时间 (简化版)
        estimated_duration = len(steps) * 10  # 假设每步10分钟
        
        plan = Plan(
            goal=goal,
            steps=steps,
            estimated_duration=estimated_duration,
            required_resources=required_resources,
            fallback_plans=[fallback] if fallback else []
        )
        
        self.activate(0.5)
        return plan
    
    def update_strategy(self, feedback: Dict):
        """
        根据反馈更新决策策略
        
        模拟前额叶皮层的认知灵活性
        
        Args:
            feedback: 包含 outcome, reward, expected_vs_actual 等
        """
        outcome = feedback.get("outcome", "neutral")  # success, failure, neutral
        reward = feedback.get("reward", 0.0)
        
        if outcome == "success":
            # 降低探索率，更信任当前策略
            self.exploration_rate *= 0.95
        elif outcome == "failure":
            # 增加探索率，尝试新策略
            self.exploration_rate = min(0.5, self.exploration_rate * 1.2)
            
        # 根据奖励调整风险偏好
        if reward > 0.5:
            self.risk_tolerance *= 1.05  # 更愿意冒险
        elif reward < -0.5:
            self.risk_tolerance *= 0.95  # 更保守
            
        self.activate(abs(reward))
    
    def _generate_options_from_context(self, context: Dict) -> List[Option]:
        """基于上下文生成选项"""
        situation = context.get("situation", "")
        options = []
        
        # 基于关键词匹配生成默认选项
        if "problem" in situation.lower():
            options.extend([
                Option("analyze", "分析问题", 0.7, 0.8, 0.3),
                Option("solve", "直接解决", 0.9, 0.5, 0.6),
                Option("escalate", "上报处理", 0.5, 0.9, 0.1)
            ])
        else:
            options.extend([
                Option("proceed", "继续执行", 0.8, 0.9, 0.2),
                Option("wait", "等待观察", 0.6, 0.95, 0.1),
                Option("abort", "终止任务", 0.3, 1.0, 0.05)
            ])
            
        return options[:self.max_options]
    
    def _calculate_goal_match(self, option: Option, goal: str) -> float:
        """计算选项与目标的匹配度"""
        goal_keywords = set(goal.lower().split())
        option_keywords = set(option.description.lower().split())
        
        if not goal_keywords:
            return 0.5
            
        overlap = goal_keywords & option_keywords
        return len(overlap) / len(goal_keywords)
    
    def _get_history_bonus(self, option_id: str) -> float:
        """基于历史表现计算加成"""
        relevant_decisions = [
            d for d in self.decision_history 
            if d["decision"].action == option_id
        ]
        
        if not relevant_decisions:
            return 0.0
            
        # 最近5次的平均成功率
        recent = relevant_decisions[-5:]
        success_count = sum(1 for d in recent if d.get("success", False))
        return (success_count / len(recent) - 0.5) * 0.2
    
    def _generate_reasoning(self, chosen: Option, all_options: List[Tuple[Option, float]]) -> str:
        """生成决策理由"""
        reason = f"选择 '{chosen.description}' 因为: "
        
        if chosen.expected_utility > 0.8:
            reason += "预期效用高; "
        if chosen.probability > 0.8:
            reason += "成功概率大; "
        if chosen.cost < 0.3:
            reason += "成本低; "
            
        if len(all_options) > 1:
            reason += f"优于其他{len(all_options)-1}个选项"
            
        return reason
    
    def _decompose_goal(self, goal: str, constraints: List[str]) -> List[Dict]:
        """将目标分解为步骤"""
        # 简化版目标分解
        steps = []
        
        # 分析阶段
        steps.append({
            "id": 1,
            "action": "analyze",
            "description": f"分析目标: {goal}",
            "dependencies": []
        })
        
        # 规划阶段
        steps.append({
            "id": 2,
            "action": "plan",
            "description": "制定执行计划",
            "dependencies": [1]
        })
        
        # 执行阶段
        steps.append({
            "id": 3,
            "action": "execute",
            "description": "执行计划",
            "dependencies": [2]
        })
        
        # 验证阶段
        steps.append({
            "id": 4,
            "action": "verify",
            "description": "验证结果",
            "dependencies": [3]
        })
        
        return steps
    
    def _analyze_resource_requirements(self, steps: List[Dict]) -> List[str]:
        """分析步骤所需资源"""
        resources = set()
        for step in steps:
            action = step.get("action", "")
            if action == "analyze":
                resources.add("computation")
            elif action == "execute":
                resources.add("execution_environment")
        return list(resources)
    
    def _generate_fallback_plan(self, steps: List[Dict], available_resources: List[str]) -> List[Dict]:
        """生成备选计划"""
        # 简化版：跳过需要缺失资源的步骤
        return [step for step in steps if step["action"] != "execute"]
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        operation = context.get("operation", "decide") if context else "decide"
        
        if operation == "decide":
            decision = self.generate_decision(input_data, context.get("options"))
            return {
                "action": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning
            }
        elif operation == "plan":
            plan = self.generate_plan(
                goal=input_data,
                constraints=context.get("constraints") if context else None
            )
            return {
                "steps": plan.steps,
                "estimated_duration": plan.estimated_duration
            }
        elif operation == "feedback":
            self.update_strategy(input_data)
            return {"status": "strategy_updated"}
            
        return {"error": "Unknown operation"}
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "working_memory_keys": list(self.working_memory.keys()),
            "current_goal": self.current_goal,
            "exploration_rate": self.exploration_rate,
            "risk_tolerance": self.risk_tolerance,
            "decision_count": len(self.decision_history)
        }


# 导出
__all__ = ['DecisionSystem', 'Option', 'Plan']
