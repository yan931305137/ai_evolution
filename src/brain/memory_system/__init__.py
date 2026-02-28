#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统 (Memory System)
对应人脑: 海马体(Hippocampus) + 杏仁核(Amygdala) + 颞叶皮层(Temporal Cortex)

核心功能:
1. 短期记忆缓存 (Short-term Memory) - 类似工作记忆
2. 长期记忆存储 (Long-term Memory) - 类似陈述性记忆
3. 情景记忆 (Episodic Memory) - 特定时间地点的事件
4. 语义记忆 (Semantic Memory) - 事实和概念知识
5. 记忆巩固 (Memory Consolidation) - 短期记忆转长期
6. 记忆检索 (Memory Retrieval) - 基于相似度的联想检索
7. 遗忘机制 (Forgetting) - 基于时间和重要性的自动清理
"""

import hashlib
import json
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import heapq

from src.brain.common import BrainModule, BrainRegion, MemoryEntry


class MemorySystem(BrainModule):
    """
    记忆系统主类
    模拟海马体的记忆编码、存储、检索和遗忘功能
    """
    
    def __init__(self, capacity: int = 10000):
        super().__init__("MemorySystem", BrainRegion.HIPPOCAMPUS)
        
        # 容量限制
        self.short_term_capacity = 7  # 米勒定律: 7±2
        self.long_term_capacity = capacity
        
        # 记忆存储
        self.short_term_memory: deque = deque(maxlen=self.short_term_capacity)
        self.long_term_memory: Dict[str, MemoryEntry] = {}
        self.episodic_memory: List[MemoryEntry] = []  # 情景记忆
        self.semantic_memory: Dict[str, MemoryEntry] = {}  # 语义记忆
        
        # 记忆索引 (用于快速检索)
        self.memory_index: Dict[str, List[str]] = {}  # tag -> memory_ids
        
        # 遗忘参数
        self.decay_rate = 0.05  # 记忆衰减率
        self.consolidation_threshold = 3  # 访问次数阈值，达到后转为长期记忆
        
    def encode(self, content: Any, memory_type: str = "short_term", 
               importance: float = 0.5, emotional_tag: Optional[Dict] = None,
               tags: Optional[List[str]] = None) -> str:
        """
        编码新记忆 (类似海马体编码)
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (short_term, episodic, semantic)
            importance: 重要性 (0-1)，影响遗忘速度
            emotional_tag: 情感标签，如 {"valence": 0.8, "arousal": 0.6}
            tags: 检索标签
            
        Returns:
            memory_id: 记忆唯一标识
        """
        # 生成记忆ID
        content_hash = hashlib.md5(
            f"{content}{datetime.now()}".encode()
        ).hexdigest()[:12]
        memory_id = f"{memory_type}_{content_hash}"
        
        # 创建记忆条目
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            importance=importance,
            emotional_tag=emotional_tag or {},
            associations=tags or []
        )
        
        # 根据类型存储
        if memory_type == "short_term":
            self.short_term_memory.append((memory_id, entry))
        elif memory_type == "episodic":
            self.episodic_memory.append(entry)
            self.long_term_memory[memory_id] = entry
        elif memory_type == "semantic":
            self.semantic_memory[memory_id] = entry
            self.long_term_memory[memory_id] = entry
        else:
            self.long_term_memory[memory_id] = entry
            
        # 更新索引
        for tag in (tags or []):
            if tag not in self.memory_index:
                self.memory_index[tag] = []
            self.memory_index[tag].append(memory_id)
            
        self.activate(importance)
        return memory_id
    
    def retrieve(self, query: str, top_k: int = 5, 
                 memory_types: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """
        记忆检索 (基于相似度和情感关联)
        
        模拟海马体的模式完成和联想检索功能
        
        Args:
            query: 查询内容
            top_k: 返回最相关的k条记忆
            memory_types: 指定记忆类型筛选
            
        Returns:
            [(memory_id, relevance_score), ...]
        """
        results = []
        query_lower = query.lower()
        
        # 搜索所有长期记忆
        search_pool = {}
        if not memory_types or "short_term" in memory_types:
            for mid, entry in self.short_term_memory:
                search_pool[mid] = entry
        if not memory_types or any(t in ["long_term", "episodic", "semantic"] for t in memory_types):
            search_pool.update(self.long_term_memory)
            
        for memory_id, entry in search_pool.items():
            # 计算相关性得分
            relevance = self._calculate_relevance(query_lower, entry)
            
            # 情感增强 (情绪状态影响记忆检索)
            emotional_boost = entry.emotional_tag.get("arousal", 0.5) * 0.2
            
            # 重要性加权
            importance_weight = entry.importance * 0.3
            
            # 近因效应 (近期记忆更容易被检索)
            time_decay = self._time_decay_factor(entry.timestamp)
            
            final_score = relevance * 0.5 + emotional_boost + importance_weight + time_decay * 0.2
            
            if final_score > 0.3:  # 阈值
                results.append((memory_id, final_score))
                entry.access_count += 1
                
        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def consolidate(self) -> List[str]:
        """
        记忆巩固 (睡眠/休息时执行)
        
        将频繁访问的短期记忆转为长期记忆
        模拟睡眠中海马体到新皮层的记忆转移
        
        Returns:
            被巩固的记忆ID列表
        """
        consolidated = []
        
        for memory_id, entry in list(self.short_term_memory):
            if entry.access_count >= self.consolidation_threshold:
                # 转为长期记忆
                entry.memory_type = "long_term"
                self.long_term_memory[memory_id] = entry
                consolidated.append(memory_id)
                
        self.activate(0.3)
        return consolidated
    
    def forget(self, memory_id: Optional[str] = None, 
               expiration_hours: Optional[int] = None) -> int:
        """
        遗忘机制
        
        基于:
        1. 艾宾浩斯遗忘曲线 - 时间衰减
        2. 重要性 - 重要记忆不易遗忘
        3. 访问频率 - 频繁访问的记忆不易遗忘
        
        Args:
            memory_id: 指定遗忘的记忆ID，为None时执行自动清理
            expiration_hours: 过期时间，为None时基于重要性自动计算
            
        Returns:
            遗忘的记忆数量
        """
        forgotten_count = 0
        
        if memory_id:
            # 指定遗忘
            if memory_id in self.long_term_memory:
                del self.long_term_memory[memory_id]
                forgotten_count += 1
        else:
            # 自动清理过期记忆
            current_time = datetime.now()
            to_forget = []
            
            for mid, entry in self.long_term_memory.items():
                # 计算遗忘阈值
                if expiration_hours:
                    threshold = timedelta(hours=expiration_hours)
                else:
                    # 基于重要性调整遗忘时间: 重要性0-1映射到7天-1年
                    days = 7 + (1 - entry.importance) * 358
                    threshold = timedelta(days=days)
                    
                # 访问次数延长遗忘时间
                threshold *= (1 + entry.access_count * 0.1)
                
                if current_time - entry.timestamp > threshold:
                    to_forget.append(mid)
                    
            for mid in to_forget:
                del self.long_term_memory[mid]
                forgotten_count += 1
                
        return forgotten_count
    
    def _calculate_relevance(self, query: str, entry: MemoryEntry) -> float:
        """计算查询与记忆的相关性"""
        content_str = str(entry.content).lower()
        
        # 简单关键词匹配 (实际应用中可使用向量相似度)
        query_words = set(query.split())
        content_words = set(content_str.split())
        
        if not query_words:
            return 0.0
            
        overlap = query_words & content_words
        return len(overlap) / len(query_words)
    
    def _time_decay_factor(self, timestamp: datetime) -> float:
        """计算时间衰减因子"""
        hours_passed = (datetime.now() - timestamp).total_seconds() / 3600
        return np.exp(-self.decay_rate * hours_passed)
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "short_term": len(self.short_term_memory),
            "long_term": len(self.long_term_memory),
            "episodic": len(self.episodic_memory),
            "semantic": len(self.semantic_memory),
            "total_unique_tags": len(self.memory_index),
            "avg_importance": np.mean([e.importance for e in self.long_term_memory.values()]) if self.long_term_memory else 0
        }
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        operation = context.get("operation", "retrieve") if context else "retrieve"
        
        if operation == "encode":
            memory_id = self.encode(
                content=input_data,
                memory_type=context.get("memory_type", "short_term"),
                importance=context.get("importance", 0.5),
                emotional_tag=context.get("emotional_tag"),
                tags=context.get("tags")
            )
            return {"memory_id": memory_id, "status": "encoded"}
            
        elif operation == "retrieve":
            results = self.retrieve(
                query=str(input_data),
                top_k=context.get("top_k", 5) if context else 5
            )
            return {"results": results, "count": len(results)}
            
        elif operation == "consolidate":
            consolidated = self.consolidate()
            return {"consolidated": consolidated, "count": len(consolidated)}
            
        elif operation == "forget":
            count = self.forget(
                memory_id=context.get("memory_id") if context else None
            )
            return {"forgotten": count}
            
        return {"error": "Unknown operation"}
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "stats": self.get_memory_stats()
        }


# 导出
__all__ = ['MemorySystem']
