#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统 (Memory System) - P0 修复版
对应人脑: 海马体(Hippocampus) + 杏仁核(Amygdala) + 颞叶皮层(Temporal Cortex)

修复内容:
1. P0-2: ID生成逻辑优化，使用 UUID + 时间戳替代 MD5
2. P0-3: 添加完整的状态持久化接口
3. P0-5: 移除100字符检索限制，支持长文本
4. 增强检索相关性计算
"""

import hashlib
import json
import uuid
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import heapq
import re

from src.brain.common import BrainModule, BrainRegion, MemoryEntry


class MemorySystem(BrainModule):
    """
    记忆系统主类 (P0修复版)
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
        self.consolidation_threshold = 3  # 访问次数阈值
        
        # P0-3: 持久化配置
        self._state_version = "2.0-P0"
        
    def _generate_memory_id(self, memory_type: str) -> str:
        """
        生成记忆唯一ID (P0-2 修复)
        
        使用 UUID + 时间戳，避免冲突
        
        Returns:
            格式: {memory_type}_{uuid}_{timestamp}
        """
        unique_id = uuid.uuid4().hex[:16]  # 16字符UUID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # 微秒级时间戳
        return f"{memory_type}_{unique_id}_{timestamp}"
    
    def encode(self, content: Any, memory_type: str = "short_term", 
               importance: float = 0.5, emotional_tag: Optional[Dict] = None,
               tags: Optional[List[str]] = None) -> str:
        """
        编码新记忆 (P0-2 修复 - 使用新的ID生成)
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性 (0-1)
            emotional_tag: 情感标签
            tags: 检索标签
            
        Returns:
            memory_id: 记忆唯一标识
        """
        # P0-2: 使用优化的ID生成
        memory_id = self._generate_memory_id(memory_type)
        
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
                 memory_types: Optional[List[str]] = None,
                 min_relevance: float = 0.1) -> List[Tuple[str, float]]:
        """
        记忆检索 (P0-5 修复 - 支持长文本，移除100字符限制)
        
        Args:
            query: 查询内容 (支持任意长度)
            top_k: 返回最相关的k条记忆
            memory_types: 指定记忆类型筛选
            min_relevance: 最小相关性阈值
            
        Returns:
            [(memory_id, relevance_score), ...]
        """
        results = []
        query_lower = query.lower()
        
        # P0-5: 支持长文本查询，分段处理
        query_segments = self._segment_long_text(query_lower, max_segment_len=100)
        
        # 搜索所有长期记忆
        search_pool = {}
        if not memory_types or "short_term" in memory_types:
            for mid, entry in self.short_term_memory:
                search_pool[mid] = entry
        if not memory_types or any(t in ["long_term", "episodic", "semantic"] for t in memory_types):
            search_pool.update(self.long_term_memory)
            
        for memory_id, entry in search_pool.items():
            # P0-5: 使用增强的相关性计算
            relevance = self._calculate_relevance_enhanced(query_segments, entry)
            
            # 情感增强
            emotional_boost = entry.emotional_tag.get("arousal", 0.5) * 0.2
            
            # 重要性加权
            importance_weight = entry.importance * 0.3
            
            # 近因效应
            time_decay = self._time_decay_factor(entry.timestamp)
            
            final_score = relevance * 0.5 + emotional_boost + importance_weight + time_decay * 0.2
            
            if final_score > min_relevance:  # P0-5: 使用参数化阈值
                results.append((memory_id, final_score))
                entry.access_count += 1
                
        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _segment_long_text(self, text: str, max_segment_len: int = 100) -> List[str]:
        """
        长文本分段 (P0-5 修复辅助方法)
        
        将长文本切分为多个片段用于检索
        
        Args:
            text: 原始文本
            max_segment_len: 每段最大长度
            
        Returns:
            文本片段列表
        """
        if len(text) <= max_segment_len:
            return [text]
            
        segments = []
        # 按句子边界切分
        sentences = re.split(r'[.!?。！？\n]+', text)
        
        current_segment = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_segment) + len(sentence) <= max_segment_len:
                current_segment += " " + sentence if current_segment else sentence
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence[:max_segment_len]
                
        if current_segment:
            segments.append(current_segment)
            
        # 确保至少返回一个片段
        if not segments:
            segments = [text[:max_segment_len]]
            
        return segments
    
    def _calculate_relevance_enhanced(self, query_segments: List[str], 
                                       entry: MemoryEntry) -> float:
        """
        增强的相关性计算 (P0-5 修复)
        
        支持多片段匹配和长文本
        """
        content_str = str(entry.content).lower()
        
        # 对每个查询片段计算相关性，取最高值
        max_relevance = 0.0
        
        for segment in query_segments:
            # 关键词匹配
            query_words = set(segment.split())
            content_words = set(content_str.split())
            
            if not query_words:
                continue
                
            overlap = query_words & content_words
            relevance = len(overlap) / len(query_words)
            
            # 短语匹配 bonus
            if segment in content_str:
                relevance += 0.2
                
            max_relevance = max(max_relevance, relevance)
            
        return min(1.0, max_relevance)
    
    def _calculate_relevance(self, query: str, entry: MemoryEntry) -> float:
        """计算查询与记忆的相关性 (兼容旧版本)"""
        return self._calculate_relevance_enhanced([query], entry)
    
    def consolidate(self) -> List[str]:
        """记忆巩固"""
        consolidated = []
        
        for memory_id, entry in list(self.short_term_memory):
            if entry.access_count >= self.consolidation_threshold:
                entry.memory_type = "long_term"
                self.long_term_memory[memory_id] = entry
                consolidated.append(memory_id)
                
        self.activate(0.3)
        return consolidated
    
    def forget(self, memory_id: Optional[str] = None, 
               expiration_hours: Optional[int] = None) -> int:
        """遗忘机制"""
        forgotten_count = 0
        
        if memory_id:
            if memory_id in self.long_term_memory:
                del self.long_term_memory[memory_id]
                forgotten_count += 1
        else:
            current_time = datetime.now()
            to_forget = []
            
            for mid, entry in self.long_term_memory.items():
                if expiration_hours:
                    threshold = timedelta(hours=expiration_hours)
                else:
                    days = 7 + (1 - entry.importance) * 358
                    threshold = timedelta(days=days)
                    
                threshold *= (1 + entry.access_count * 0.1)
                
                if current_time - entry.timestamp > threshold:
                    to_forget.append(mid)
                    
            for mid in to_forget:
                del self.long_term_memory[mid]
                forgotten_count += 1
                
        return forgotten_count
    
    def _time_decay_factor(self, timestamp: datetime) -> float:
        """计算时间衰减因子"""
        hours_passed = (datetime.now() - timestamp).total_seconds() / 3600
        return np.exp(-self.decay_rate * hours_passed)
    
    # ==================== P0-3: 持久化接口 ====================
    
    def save_state(self, filepath: str):
        """
        保存系统状态到文件 (P0-3 修复)
        
        支持完整状态持久化:
        - 所有记忆数据
        - 记忆索引
        - 系统参数
        - 统计信息
        """
        state = {
            "version": self._state_version,
            "saved_at": datetime.now().isoformat(),
            "config": {
                "short_term_capacity": self.short_term_capacity,
                "long_term_capacity": self.long_term_capacity,
                "decay_rate": self.decay_rate,
                "consolidation_threshold": self.consolidation_threshold,
            },
            "short_term_memory": [
                {
                    "id": mid,
                    "content": entry.content,
                    "memory_type": entry.memory_type,
                    "importance": entry.importance,
                    "emotional_tag": entry.emotional_tag,
                    "associations": entry.associations,
                    "access_count": entry.access_count,
                    "timestamp": entry.timestamp.isoformat(),
                }
                for mid, entry in self.short_term_memory
            ],
            "long_term_memory": {
                mid: {
                    "content": entry.content,
                    "memory_type": entry.memory_type,
                    "importance": entry.importance,
                    "emotional_tag": entry.emotional_tag,
                    "associations": entry.associations,
                    "access_count": entry.access_count,
                    "timestamp": entry.timestamp.isoformat(),
                }
                for mid, entry in self.long_term_memory.items()
            },
            "episodic_memory": [
                {
                    "content": entry.content,
                    "memory_type": entry.memory_type,
                    "importance": entry.importance,
                    "emotional_tag": entry.emotional_tag,
                    "associations": entry.associations,
                    "access_count": entry.access_count,
                    "timestamp": entry.timestamp.isoformat(),
                }
                for entry in self.episodic_memory
            ],
            "semantic_memory": {
                mid: {
                    "content": entry.content,
                    "memory_type": entry.memory_type,
                    "importance": entry.importance,
                    "emotional_tag": entry.emotional_tag,
                    "associations": entry.associations,
                    "access_count": entry.access_count,
                    "timestamp": entry.timestamp.isoformat(),
                }
                for mid, entry in self.semantic_memory.items()
            },
            "memory_index": self.memory_index,
            "activation_level": self.activation_level,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
            
    def load_state(self, filepath: str):
        """
        从文件加载系统状态 (P0-3 修复)
        
        恢复完整的记忆系统状态
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
        # 恢复配置
        config = state.get("config", {})
        self.short_term_capacity = config.get("short_term_capacity", 7)
        self.long_term_capacity = config.get("long_term_capacity", 10000)
        self.decay_rate = config.get("decay_rate", 0.05)
        self.consolidation_threshold = config.get("consolidation_threshold", 3)
        
        # 恢复短期记忆
        self.short_term_memory.clear()
        for item in state.get("short_term_memory", []):
            entry = MemoryEntry(
                content=item["content"],
                memory_type=item["memory_type"],
                importance=item["importance"],
                emotional_tag=item.get("emotional_tag", {}),
                associations=item.get("associations", []),
            )
            entry.access_count = item.get("access_count", 0)
            entry.timestamp = datetime.fromisoformat(item["timestamp"])
            self.short_term_memory.append((item["id"], entry))
            
        # 恢复长期记忆
        self.long_term_memory.clear()
        for mid, item in state.get("long_term_memory", {}).items():
            entry = MemoryEntry(
                content=item["content"],
                memory_type=item["memory_type"],
                importance=item["importance"],
                emotional_tag=item.get("emotional_tag", {}),
                associations=item.get("associations", []),
            )
            entry.access_count = item.get("access_count", 0)
            entry.timestamp = datetime.fromisoformat(item["timestamp"])
            self.long_term_memory[mid] = entry
            
        # 恢复情景记忆
        self.episodic_memory.clear()
        for item in state.get("episodic_memory", []):
            entry = MemoryEntry(
                content=item["content"],
                memory_type=item["memory_type"],
                importance=item["importance"],
                emotional_tag=item.get("emotional_tag", {}),
                associations=item.get("associations", []),
            )
            entry.access_count = item.get("access_count", 0)
            entry.timestamp = datetime.fromisoformat(item["timestamp"])
            self.episodic_memory.append(entry)
            
        # 恢复语义记忆
        self.semantic_memory.clear()
        for mid, item in state.get("semantic_memory", {}).items():
            entry = MemoryEntry(
                content=item["content"],
                memory_type=item["memory_type"],
                importance=item["importance"],
                emotional_tag=item.get("emotional_tag", {}),
                associations=item.get("associations", []),
            )
            entry.access_count = item.get("access_count", 0)
            entry.timestamp = datetime.fromisoformat(item["timestamp"])
            self.semantic_memory[mid] = entry
            
        # 恢复索引
        self.memory_index = state.get("memory_index", {})
        
        # 恢复激活水平
        self.activation_level = state.get("activation_level", 0.0)
    
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
                top_k=context.get("top_k", 5) if context else 5,
                memory_types=context.get("memory_types"),
                min_relevance=context.get("min_relevance", 0.1)
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
            
        elif operation == "save_state":
            self.save_state(context.get("filepath", "memory_state.json"))
            return {"status": "saved"}
            
        elif operation == "load_state":
            self.load_state(context.get("filepath", "memory_state.json"))
            return {"status": "loaded"}
            
        return {"error": "Unknown operation"}
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "stats": self.get_memory_stats(),
            "version": self._state_version,
        }


# 导出
__all__ = ['MemorySystem']
