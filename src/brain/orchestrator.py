#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大脑协调器 (Brain Orchestrator)

整合五个核心系统:
1. 感知系统 (Perception) - 枕/颞叶
2. 注意力系统 (Attention) - 顶叶
3. 记忆系统 (Memory) - 海马体
4. 决策系统 (Decision) - 前额叶
5. 价值系统 (Value) - 伏隔核

模拟大脑各区域的协调工作，实现类脑智能的集成控制。
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

from src.brain.common import BrainState, BrainModule
from src.brain.perception_system import PerceptionSystem, ModalityType
from src.brain.attention_system import AttentionSystem, Stimulus
from src.brain.memory_system import MemorySystem, MemoryEntry, MemoryType
from src.brain.decision_system import DecisionSystem, Option
from src.brain.value_system import ValueSystem, ValueAssessment


class ProcessingMode(Enum):
    """处理模式"""
    SERIAL = "serial"  # 串行处理
    PARALLEL = "parallel"  # 并行处理
    ADAPTIVE = "adaptive"  # 自适应模式


@dataclass
class BrainResponse:
    """大脑响应"""
    action: str
    content: Any
    confidence: float
    processing_time: float
    systems_involved: List[str]
    metadata: Dict = field(default_factory=dict)


class BrainOrchestrator:
    """
    大脑协调器
    
    功能:
    1. 系统初始化与管理
    2. 信息流向控制
    3. 跨系统协调
    4. 全局状态维护
    5. 学习与适应
    """
    
    def __init__(self, mode: ProcessingMode = ProcessingMode.ADAPTIVE):
        self.mode = mode
        
        # 初始化五个核心系统
        self.perception = PerceptionSystem()
        self.attention = AttentionSystem()
        self.memory = MemorySystem()
        self.decision = DecisionSystem()
        self.value = ValueSystem()
        
        # 系统注册表
        self.systems: Dict[str, BrainModule] = {
            "perception": self.perception,
            "attention": self.attention,
            "memory": self.memory,
            "decision": self.decision,
            "value": self.value
        }
        
        # 全局状态
        self.state = BrainState()
        self.processing_history: List[Dict] = []
        
        # 循环计数器 (用于定期清理)
        self.cycle_count = 0
        
        # 是否启用调试日志
        self.debug = False
        
    async def process(self, input_data: Any, 
                     context: Optional[Dict] = None) -> BrainResponse:
        """
        主处理流程
        
        模拟大脑的完整信息处理流程:
        感知 -> 注意 -> 记忆检索 -> 价值评估 -> 决策 -> 记忆存储
        
        Args:
            input_data: 输入数据
            context: 处理上下文
            
        Returns:
            BrainResponse: 处理结果
        """
        start_time = time.time()
        context = context or {}
        systems_involved = []
        
        if self.debug:
            print(f"[Brain] Processing input: {str(input_data)[:50]}...")
        
        # 1. 感知处理
        perception_result = self.perception.process(input_data, context)
        systems_involved.append("perception")
        
        modality = perception_result.get("modality", "unknown")
        features = perception_result.get("features", {})
        
        if self.debug:
            print(f"[Brain] Perception: modality={modality}")
        
        # 2. 注意力分配
        stimulus = Stimulus(
            id=f"input_{time.time()}",
            content=input_data,
            modality=modality if modality != "unknown" else "cognitive",
            salience=features.get("complexity_score", 0.5) if isinstance(features, dict) else 0.5,
            relevance=context.get("relevance", 0.5),
            urgency=features.get("emotional_markers", {}).get("urgent", 0.0) if isinstance(features, dict) else 0.0
        )
        
        attention_result = self.attention.process([stimulus], {
            "operation": "allocate",
            "goal": context.get("goal", "")
        })
        systems_involved.append("attention")
        
        primary_focus = attention_result.get("primary")
        
        if self.debug:
            print(f"[Brain] Attention: primary_focus={primary_focus}")
        
        # 3. 记忆检索 (相关经验)
        memory_query = str(input_data)[:100]
        relevant_memories = self.memory.search(
            query=memory_query,
            k=3,
            include_emotional=True
        )
        systems_involved.append("memory")
        
        if self.debug and relevant_memories:
            print(f"[Brain] Memory: retrieved {len(relevant_memories)} entries")
        
        # 4. 价值评估
        value_context = {
            "goal_alignment": 0.7 if context.get("goal") else 0.3,
            "feasibility": 0.8,
            "uncertainty": 1 - perception_result.get("confidence", 0.5)
        }
        value_result = self.value.process(input_data, {
            "operation": "evaluate",
            **value_context
        })
        systems_involved.append("value")
        
        motivation = value_result.get("motivation", 0.5)
        
        if self.debug:
            print(f"[Brain] Value: motivation={motivation:.2f}")
        
        # 5. 决策生成
        decision_context = {
            "situation": str(input_data),
            "goal": context.get("goal", "process_input"),
            "relevant_memories": [
                {"content": m.content, "emotional_valence": m.emotional_valence}
                for m in relevant_memories
            ],
            "motivation": motivation,
            "constraints": context.get("constraints", [])
        }
        
        decision_result = self.decision.process(input_data, {
            "operation": "decide",
            **decision_context
        })
        systems_involved.append("decision")
        
        action = decision_result.get("action", "process")
        confidence = decision_result.get("confidence", 0.5)
        
        if self.debug:
            print(f"[Brain] Decision: action={action}, confidence={confidence:.2f}")
        
        # 6. 保存到记忆
        self.memory.store(MemoryEntry(
            content={
                "input": str(input_data)[:200],
                "action": action,
                "context": context
            },
            memory_type=MemoryType.WORKING,  # 先存为工作记忆
            importance=motivation * 0.8,
            emotional_valence=value_result.get("value", 0.0)
        ))
        
        # 7. 周期性维护
        self.cycle_count += 1
        if self.cycle_count % 10 == 0:
            self._maintenance()
        
        # 构建响应
        processing_time = time.time() - start_time
        
        response = BrainResponse(
            action=action,
            content={
                "perception": perception_result,
                "attention": attention_result,
                "decision": decision_result,
                "value": value_result,
                "relevant_memories": len(relevant_memories)
            },
            confidence=confidence,
            processing_time=processing_time,
            systems_involved=systems_involved,
            metadata={
                "cycle": self.cycle_count,
                "modality": modality,
                "motivation": motivation
            }
        )
        
        # 记录历史
        self.processing_history.append({
            "timestamp": datetime.now(),
            "response": response,
            "input_summary": str(input_data)[:100]
        })
        
        return response
    
    def learn(self, outcome: Dict):
        """
        从结果中学习
        
        更新各系统的参数和状态
        
        Args:
            outcome: 执行结果，包含 success, reward 等
        """
        # 价值系统学习
        self.value.process(None, {
            "operation": "reward",
            "outcome": outcome
        })
        
        # 决策系统反馈
        feedback = {
            "outcome": "success" if outcome.get("success") else "failure",
            "reward": outcome.get("reward", 0.0)
        }
        self.decision.process(feedback, {"operation": "feedback"})
        
        # 记忆巩固
        self.memory.consolidate()
        
        if self.debug:
            print(f"[Brain] Learning from outcome: success={outcome.get('success')}")
    
    def get_state_summary(self) -> Dict:
        """获取大脑状态摘要"""
        return {
            "processing_cycles": self.cycle_count,
            "systems": {
                name: system.get_state()
                for name, system in self.systems.items()
            },
            "dopamine_level": self.value.get_dopamine_level(),
            "motivation": self.value.get_motivation_state(),
            "current_attention": self.attention.get_attention_summary(),
            "working_memory_size": len(self.memory.working_memory),
            "long_term_memory_size": self.memory.long_term_memory.get("stats", {}).get("count", 0)
        }
    
    def reset(self):
        """重置大脑状态"""
        self.cycle_count = 0
        self.processing_history.clear()
        
        # 重置各系统
        for system in self.systems.values():
            if hasattr(system, 'reset'):
                system.reset()
                
        if self.debug:
            print("[Brain] State reset")
    
    def _maintenance(self):
        """周期性维护"""
        # 记忆遗忘
        self.memory.forget()
        
        # 注意力更新
        self.attention.update_attention()
        
        if self.debug:
            print(f"[Brain] Maintenance cycle {self.cycle_count}")
    
    # 便捷方法
    
    def perceive(self, input_data: Any, modality: Optional[str] = None) -> Dict:
        """感知接口"""
        return self.perception.process(input_data, {"modality": modality} if modality else None)
    
    def decide(self, context: Dict, options: Optional[List[Dict]] = None) -> Dict:
        """决策接口"""
        return self.decision.process(context, {"operation": "decide", "options": options})
    
    def evaluate(self, target: Any, context: Optional[Dict] = None) -> Dict:
        """价值评估接口"""
        return self.value.process(target, {"operation": "evaluate", **(context or {})})
    
    def recall(self, query: str, k: int = 3) -> List[MemoryEntry]:
        """记忆检索接口"""
        return self.memory.search(query, k=k)
    
    def focus(self, stimuli: List[Dict], goal: Optional[str] = None) -> Dict:
        """注意力分配接口"""
        stimulus_objects = [
            Stimulus(**s) for s in stimuli
        ]
        return self.attention.process(stimulus_objects, {"operation": "allocate", "goal": goal})


# 单例模式
_brain_instance: Optional[BrainOrchestrator] = None


def get_brain() -> BrainOrchestrator:
    """获取大脑协调器实例 (单例)"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = BrainOrchestrator()
    return _brain_instance


def reset_brain():
    """重置大脑实例"""
    global _brain_instance
    if _brain_instance:
        _brain_instance.reset()
    _brain_instance = None


# 导出
__all__ = [
    'BrainOrchestrator', 
    'BrainResponse', 
    'ProcessingMode',
    'get_brain',
    'reset_brain'
]
