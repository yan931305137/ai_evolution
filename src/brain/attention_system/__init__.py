#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注意力系统 (Attention System)
对应人脑: 顶叶皮层 (Parietal Cortex) + 丘脑网状核 (Thalamic Reticular Nucleus)

核心功能:
1. 注意力分配 - 根据任务重要性分配认知资源
2. 选择性注意 - 从复杂环境中筛选相关信息
3. 注意力转移 - 在任务间灵活切换焦点
4. 持续性注意 - 维持对目标的关注
5. 分配性注意 - 同时处理多个信息源
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

from src.brain.common import BrainModule, BrainRegion


@dataclass
class AttentionFocus:
    """注意力焦点"""
    target_id: str
    target_content: Any
    attention_weight: float  # 0-1
    priority_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0  # 持续时长(秒)


@dataclass
class Stimulus:
    """刺激/输入信息"""
    id: str
    content: Any
    modality: str  # visual, auditory, cognitive
    salience: float  # 显著性/突出度 0-1
    relevance: float  # 与当前任务相关性 0-1
    urgency: float  # 紧急程度 0-1
    metadata: Dict = field(default_factory=dict)


class AttentionSystem(BrainModule):
    """
    注意力系统
    模拟顶叶皮层的注意力控制功能
    """
    
    def __init__(self, max_focus_items: int = 5, attention_capacity: float = 1.0):
        super().__init__("AttentionSystem", BrainRegion.PARIETAL_CORTEX)
        
        self.max_focus_items = max_focus_items  # 最大同时关注项目数
        self.attention_capacity = attention_capacity  # 总注意力容量
        
        # 当前注意力焦点
        self.current_focus: List[AttentionFocus] = []
        
        # 注意力历史
        self.attention_history: deque = deque(maxlen=100)
        
        # 干扰抑制
        self.inhibition_list: List[str] = []  # 被抑制的刺激ID
        
        # 注意力参数
        self.decay_rate = 0.1  # 注意力衰减率
        self.boost_factor = 1.5  # 焦点增强因子
        
    def allocate_attention(self, stimuli: List[Stimulus], 
                          task_context: Optional[Dict] = None) -> List[AttentionFocus]:
        """
        分配注意力
        
        基于以下因素计算注意力权重:
        1. 显著性 (Saliency) - 刺激的突出程度
        2. 相关性 (Relevance) - 与当前任务的相关度
        3. 紧急性 (Urgency) - 时间压力
        4. 新颖性 (Novelty) - 是否新信息
        
        Args:
            stimuli: 输入刺激列表
            task_context: 当前任务上下文
            
        Returns:
            注意力焦点列表
        """
        task_context = task_context or {}
        task_goal = task_context.get("goal", "")
        
        # 计算每个刺激的注意力得分
        scored_stimuli = []
        for stimulus in stimuli:
            if stimulus.id in self.inhibition_list:
                continue  # 跳过被抑制的刺激
                
            # 基础得分
            base_score = (stimulus.salience * 0.3 + 
                         stimulus.relevance * 0.4 + 
                         stimulus.urgency * 0.3)
            
            # 目标匹配加成
            goal_match = self._calculate_goal_match(stimulus, task_goal)
            
            # 新颖性加成 (新刺激获得额外关注)
            novelty = 1.0 if stimulus.id not in [h.get("id") for h in self.attention_history] else 0.5
            
            final_score = base_score * 0.6 + goal_match * 0.3 + novelty * 0.1
            
            scored_stimuli.append((stimulus, final_score))
            
        # 按得分排序
        scored_stimuli.sort(key=lambda x: x[1], reverse=True)
        
        # 分配注意力容量
        total_capacity = self.attention_capacity
        new_focus = []
        
        for stimulus, score in scored_stimuli[:self.max_focus_items]:
            # 注意力权重与得分成正比，但不超过剩余容量
            weight = min(score * self.boost_factor, total_capacity)
            total_capacity -= weight
            
            focus = AttentionFocus(
                target_id=stimulus.id,
                target_content=stimulus.content,
                attention_weight=weight,
                priority_score=score
            )
            new_focus.append(focus)
            
            # 记录历史
            self.attention_history.append({
                "id": stimulus.id,
                "timestamp": datetime.now(),
                "weight": weight,
                "score": score
            })
            
            if total_capacity <= 0:
                break
                
        self.current_focus = new_focus
        self.activate(sum(f.attention_weight for f in new_focus))
        
        return new_focus
    
    def filter_noise(self, inputs: List[Any], noise_threshold: float = 0.3,
                    context: Optional[Dict] = None) -> List[Any]:
        """
        过滤噪声/无关信息
        
        将注意力权重低于阈值的信息过滤掉
        
        Args:
            inputs: 输入信息列表
            noise_threshold: 噪声阈值
            context: 上下文信息
            
        Returns:
            过滤后的有效信息
        """
        if not self.current_focus:
            return inputs  # 没有焦点时返回全部
            
        # 只保留与当前焦点相关的输入
        filtered = []
        for inp in inputs:
            inp_id = self._get_input_id(inp)
            # 检查是否与当前焦点相关
            for focus in self.current_focus:
                if self._is_related(inp_id, focus.target_id):
                    if focus.attention_weight >= noise_threshold:
                        filtered.append(inp)
                    break
                    
        return filtered
    
    def shift_attention(self, new_target_id: str, 
                       gradual: bool = True) -> bool:
        """
        转移注意力焦点
        
        Args:
            new_target_id: 新目标ID
            gradual: 是否渐进转移
            
        Returns:
            是否成功转移
        """
        # 查找新目标
        new_focus = None
        for focus in self.current_focus:
            if focus.target_id == new_target_id:
                new_focus = focus
                break
                
        if not new_focus:
            return False
            
        if gradual:
            # 渐进转移: 逐步降低其他焦点，提升新焦点
            for focus in self.current_focus:
                if focus.target_id == new_target_id:
                    focus.attention_weight = min(1.0, focus.attention_weight * self.boost_factor)
                else:
                    focus.attention_weight *= 0.7  # 衰减
        else:
            # 立即转移: 清空其他焦点
            self.current_focus = [new_focus]
            new_focus.attention_weight = 1.0
            
        # 重新归一化
        total = sum(f.attention_weight for f in self.current_focus)
        if total > 0:
            for focus in self.current_focus:
                focus.attention_weight /= total
                
        self.activate(new_focus.attention_weight)
        return True
    
    def inhibit_distraction(self, distraction_id: str, 
                           duration: float = 60.0):
        """
        抑制干扰/分心刺激
        
        Args:
            distraction_id: 干扰源ID
            duration: 抑制持续时间(秒)
        """
        if distraction_id not in self.inhibition_list:
            self.inhibition_list.append(distraction_id)
            
        # 从当前焦点中移除
        self.current_focus = [
            f for f in self.current_focus 
            if f.target_id != distraction_id
        ]
        
    def update_attention(self, time_delta: float = 1.0):
        """
        更新注意力状态 (随时间衰减)
        
        Args:
            time_delta: 时间间隔(秒)
        """
        # 注意力随时间自然衰减
        for focus in self.current_focus:
            focus.duration += time_delta
            focus.attention_weight *= (1 - self.decay_rate * time_delta)
            
        # 移除注意力耗尽的项目
        self.current_focus = [
            f for f in self.current_focus 
            if f.attention_weight > 0.1
        ]
        
        # 清空抑制列表 (简单实现: 定期清空)
        if len(self.attention_history) % 20 == 0:
            self.inhibition_list.clear()
            
    def get_attention_summary(self) -> Dict:
        """获取注意力状态摘要"""
        return {
            "current_focus_count": len(self.current_focus),
            "total_attention_allocated": sum(f.attention_weight for f in self.current_focus),
            "primary_focus": self.current_focus[0].target_id if self.current_focus else None,
            "inhibited_items": len(self.inhibition_list),
            "attention_history_length": len(self.attention_history)
        }
    
    def _calculate_goal_match(self, stimulus: Stimulus, goal: str) -> float:
        """计算刺激与目标的匹配度"""
        if not goal:
            return 0.5
        goal_keywords = set(goal.lower().split())
        content_str = str(stimulus.content).lower()
        content_keywords = set(content_str.split())
        
        if not goal_keywords:
            return 0.5
            
        overlap = goal_keywords & content_keywords
        return len(overlap) / len(goal_keywords)
    
    def _get_input_id(self, inp: Any) -> str:
        """获取输入的唯一标识"""
        if isinstance(inp, dict):
            return inp.get("id", str(hash(str(inp)))[:8])
        return str(hash(str(inp)))[:8]
    
    def _is_related(self, id1: str, id2: str) -> bool:
        """判断两个ID是否相关"""
        return id1 == id2 or id1.startswith(id2) or id2.startswith(id1)
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        operation = context.get("operation", "allocate") if context else "allocate"
        
        if operation == "allocate":
            # 将输入转换为Stimulus列表
            if isinstance(input_data, list):
                stimuli = [
                    Stimulus(**s) if isinstance(s, dict) else Stimulus(id=str(i), content=s, modality="cognitive", salience=0.5, relevance=0.5, urgency=0.5)
                    for i, s in enumerate(input_data)
                ]
            else:
                stimuli = [Stimulus(id="0", content=input_data, modality="cognitive", salience=0.5, relevance=0.5, urgency=0.5)]
                
            focus = self.allocate_attention(stimuli, context)
            return {
                "focus_ids": [f.target_id for f in focus],
                "weights": [f.attention_weight for f in focus],
                "primary": focus[0].target_id if focus else None
            }
            
        elif operation == "filter":
            filtered = self.filter_noise(input_data, context.get("threshold", 0.3))
            return {"filtered": filtered, "count": len(filtered)}
            
        elif operation == "shift":
            success = self.shift_attention(input_data, context.get("gradual", True))
            return {"success": success}
            
        elif operation == "inhibit":
            self.inhibit_distraction(input_data, context.get("duration", 60))
            return {"status": "inhibited"}
            
        return {"error": "Unknown operation"}
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "current_focus": self.get_attention_summary(),
            "capacity_remaining": self.attention_capacity - sum(f.attention_weight for f in self.current_focus)
        }


# 导出
__all__ = ['AttentionSystem', 'AttentionFocus', 'Stimulus']
