#!/usr/bin/env python3
"""
AI 执行过程监控与分析器
用于分析 /auto 指令的执行过程，监控 LLM 调用频率，提出优化建议
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import sys
import os

# 添加项目路径
sys.path.insert(0, '/workspace/projects')

from src.utils.enhanced_hybrid_brain import EnhancedHybridBrain
# from src.agents.agent import AutoAgent  # 移除循环导入
from src.storage.database import Database


class TaskComplexity(Enum):
    """任务复杂度等级"""
    SIMPLE = "simple"        # 简单任务 - 本地处理
    MODERATE = "moderate"    # 中等任务 - 混合处理
    COMPLEX = "complex"      # 复杂任务 - LLM主导


@dataclass
class ExecutionStep:
    """执行步骤记录"""
    step_id: int
    timestamp: float
    action_type: str  # "llm_call", "brain_process", "tool_use", "memory_access"
    duration_ms: float
    input_size: int
    output_size: int
    success: bool
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """执行指标"""
    total_steps: int = 0
    llm_calls: int = 0
    brain_processes: int = 0
    tool_calls: int = 0
    memory_accesses: int = 0
    total_duration_ms: float = 0
    steps: List[ExecutionStep] = field(default_factory=list)
    
    def add_step(self, step: ExecutionStep):
        self.steps.append(step)
        self.total_steps += 1
        self.total_duration_ms += step.duration_ms
        
        if step.action_type == "llm_call":
            self.llm_calls += 1
        elif step.action_type == "brain_process":
            self.brain_processes += 1
        elif step.action_type == "tool_use":
            self.tool_calls += 1
        elif step.action_type == "memory_access":
            self.memory_accesses += 1
    
    @property
    def llm_ratio(self) -> float:
        """LLM 调用占比"""
        total = self.llm_calls + self.brain_processes
        return self.llm_calls / total if total > 0 else 0
    
    @property
    def efficiency_score(self) -> float:
        """效率评分 - Brain处理比例越高越好"""
        return 1 - self.llm_ratio
    
    def report(self) -> str:
        """生成报告"""
        lines = [
            "=" * 60,
            "📊 AI 执行过程分析报告",
            "=" * 60,
            f"总步骤数: {self.total_steps}",
            f"LLM 调用: {self.llm_calls} ({self.llm_ratio*100:.1f}%)",
            f"Brain 处理: {self.brain_processes} ({(1-self.llm_ratio)*100:.1f}%)",
            f"工具调用: {self.tool_calls}",
            f"记忆访问: {self.memory_accesses}",
            f"总耗时: {self.total_duration_ms/1000:.2f}s",
            f"效率评分: {self.efficiency_score*100:.1f}/100",
            "=" * 60,
        ]
        return "\n".join(lines)


class TaskComplexityAnalyzer:
    """任务复杂度分析器"""
    
    # 本地可处理的关键词（简单任务）
    SIMPLE_KEYWORDS = [
        "查询", "查看", "获取", "显示", "列出", "检查", "状态",
        "hello", "hi", "你好", "在吗", "帮助", "help",
        "时间", "日期", "天气",
        "git status", "git log", "git branch",
    ]
    
    # 需要 LLM 的复杂任务关键词
    COMPLEX_KEYWORDS = [
        "编写", "开发", "实现", "设计", "创建",
        "重构", "优化", "改进", "修复", "debug",
        "分析", "解释", "为什么", "原因",
        "规划", "计划", "方案", "策略",
        "写代码", "编程", "函数", "类",
    ]
    
    def analyze(self, goal: str) -> TaskComplexity:
        """分析任务复杂度"""
        goal_lower = goal.lower()
        
        # 检查是否为简单任务
        for keyword in self.SIMPLE_KEYWORDS:
            if keyword in goal_lower:
                return TaskComplexity.SIMPLE
        
        # 检查是否为复杂任务
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in goal_lower:
                return TaskComplexity.COMPLEX
        
        # 默认中等
        return TaskComplexity.MODERATE


class AutoExecutionMonitor:
    """/auto 执行监控器"""
    
    def __init__(self):
        self.metrics = ExecutionMetrics()
        self.complexity_analyzer = TaskComplexityAnalyzer()
        self.start_time = None
        
    def start_monitoring(self):
        """开始监控"""
        self.start_time = time.time()
        print("🔍 开始监控 AI 执行过程...")
        
    def log_step(self, action_type: str, duration_ms: float, 
                 input_size: int = 0, output_size: int = 0, 
                 success: bool = True, metadata: Dict = None):
        """记录执行步骤"""
        step = ExecutionStep(
            step_id=self.metrics.total_steps + 1,
            timestamp=time.time() - self.start_time,
            action_type=action_type,
            duration_ms=duration_ms,
            input_size=input_size,
            output_size=output_size,
            success=success,
            metadata=metadata or {}
        )
        self.metrics.add_step(step)
        
    def analyze_task(self, goal: str) -> TaskComplexity:
        """分析任务复杂度"""
        complexity = self.complexity_analyzer.analyze(goal)
        print(f"📋 任务复杂度分析: {complexity.value}")
        print(f"   目标: {goal[:60]}...")
        return complexity
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 分析 LLM 调用比例
        if self.metrics.llm_ratio > 0.7:
            recommendations.append(
                "⚠️ LLM 调用比例过高 (>70%)，建议增加 Brain 本地处理能力"
            )
            recommendations.append(
                "   - 添加更多本地意图识别规则"
            )
            recommendations.append(
                "   - 对简单查询使用模板匹配代替 LLM"
            )
        
        # 分析工具调用效率
        if self.metrics.tool_calls > self.metrics.llm_calls * 2:
            recommendations.append(
                "💡 工具调用频繁，考虑批量处理或缓存结果"
            )
        
        # 分析记忆使用
        if self.metrics.memory_accesses < self.metrics.llm_calls / 2:
            recommendations.append(
                "💡 记忆访问不足，建议增强上下文记忆以减少重复 LLM 调用"
            )
        
        # 分析响应时间
        avg_step_time = self.metrics.total_duration_ms / max(self.metrics.total_steps, 1)
        if avg_step_time > 2000:
            recommendations.append(
                f"⚠️ 平均步骤耗时较长 ({avg_step_time:.0f}ms)，建议优化"
            )
        
        return recommendations
    
    def final_report(self) -> str:
        """生成最终报告"""
        lines = [
            self.metrics.report(),
            "",
            "💡 优化建议:",
        ]
        
        recommendations = self.generate_recommendations()
        if recommendations:
            for rec in recommendations:
                lines.append(f"  {rec}")
        else:
            lines.append("  ✅ 当前执行效率良好")
        
        return "\n".join(lines)


def simulate_auto_execution(goal: str) -> ExecutionMetrics:
    """
    模拟 /auto 执行过程
    实际监控 Agent 的执行步骤
    """
    monitor = AutoExecutionMonitor()
    monitor.start_monitoring()
    
    # 分析任务复杂度
    complexity = monitor.analyze_task(goal)
    
    print(f"\n🚀 模拟执行任务: {goal}")
    print(f"   预计处理方式: {complexity.value}")
    
    # 模拟执行步骤
    steps = []
    
    if complexity == TaskComplexity.SIMPLE:
        # 简单任务 - 主要用 Brain
        steps = [
            ("brain_process", 50, 20, 50),
            ("memory_access", 30, 10, 30),
            ("tool_use", 100, 15, 100),
        ]
    elif complexity == TaskComplexity.MODERATE:
        # 中等任务 - 混合
        steps = [
            ("llm_call", 800, 100, 200),
            ("brain_process", 100, 50, 80),
            ("memory_access", 50, 20, 40),
            ("tool_use", 200, 30, 150),
            ("brain_process", 80, 40, 60),
        ]
    else:
        # 复杂任务 - LLM 主导
        steps = [
            ("llm_call", 1500, 200, 500),
            ("brain_process", 150, 80, 120),
            ("llm_call", 1200, 150, 400),
            ("tool_use", 300, 50, 200),
            ("llm_call", 1000, 100, 300),
            ("brain_process", 100, 60, 80),
            ("llm_call", 800, 80, 250),
        ]
    
    # 模拟执行
    for i, (action_type, duration, input_sz, output_sz) in enumerate(steps, 1):
        print(f"   Step {i}: {action_type} ({duration}ms)")
        monitor.log_step(
            action_type=action_type,
            duration_ms=duration,
            input_size=input_sz,
            output_size=output_sz,
            success=True
        )
        time.sleep(0.1)  # 模拟延迟
    
    print(f"\n{monitor.final_report()}")
    return monitor.metrics


def analyze_real_agent_execution(goal: str):
    """
    分析真实的 Agent 执行过程
    创建增强版的 Agent 来监控执行
    """
    print("=" * 60)
    print("🔬 真实 Agent 执行分析")
    print("=" * 60)
    
    # 初始化组件
    db = Database()
    
    # 使用 EnhancedHybridBrain 以减少 LLM 调用
    llm = EnhancedHybridBrain(
        start_as_infant=False,
        local_first=True,
        llm_provider=None
    )
    
    # 注：由于循环导入问题，这里不直接使用 AutoAgent
    # 实际集成后，可通过 SmartTaskExecutor 进行分析
    # agent = AutoAgent(llm)
    
    # 创建监控器
    monitor = AutoExecutionMonitor()
    monitor.start_monitoring()
    
    # 分析任务
    complexity = monitor.analyze_task(goal)
    
    print(f"\n🎯 开始执行: {goal}")
    print(f"   复杂度: {complexity.value}")
    print(f"   使用 EnhancedHybridBrain: ✅ (本地优先处理)")
    
    # 这里我们会 hook agent 的执行来监控
    # 由于实际 hook 需要修改 agent 代码，我们先模拟
    
    print("\n📊 基于任务复杂度的预测分析:")
    
    if complexity == TaskComplexity.SIMPLE:
        print("   预计 Brain 本地处理: 70%")
        print("   预计 LLM 调用: 30%")
        print("   优化策略: 使用意图路由 + 模板匹配")
    elif complexity == TaskComplexity.MODERATE:
        print("   预计 Brain 本地处理: 40%")
        print("   预计 LLM 调用: 60%")
        print("   优化策略: Brain 规划 + LLM 生成")
    else:
        print("   预计 Brain 本地处理: 20%")
        print("   预计 LLM 调用: 80%")
        print("   优化策略: LLM 主导 + Brain 辅助")
    
    return monitor


if __name__ == "__main__":
    # 测试不同的任务类型
    test_goals = [
        "查看当前 git 状态",
        "帮我优化这段代码的性能",
        "设计一个新的用户认证系统，包含登录注册功能",
    ]
    
    print("\n" + "=" * 60)
    print("🧪 AI 执行效率分析系统")
    print("=" * 60)
    
    for goal in test_goals:
        print("\n" + "-" * 60)
        simulate_auto_execution(goal)
        print("-" * 60)
    
    # 真实 Agent 分析
    print("\n")
    analyze_real_agent_execution("分析项目代码结构并给出优化建议")
