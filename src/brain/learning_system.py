#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台知识学习系统 (Background Knowledge Learning)

实现"闲时学习"机制：
1. 实时响应时检测知识缺口
2. 将待学习内容加入队列
3. 系统闲置时调用LLM补充知识
4. 提取结构化知识存入记忆

对应人脑：睡眠中的记忆巩固、复习学习
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue
import threading
import time

from src.brain.memory_system import MemorySystem, MemoryEntry
from src.brain.common import MemoryType


@dataclass
class LearningTask:
    """学习任务"""
    query: str  # 待学习的查询
    context: Dict[str, Any]  # 上下文信息
    priority: int  # 优先级 (1-10, 数字越小越优先)
    created_at: datetime = field(default_factory=datetime.now)
    source: str = ""  # 来源（哪个对话触发）
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class KnowledgeGap:
    """知识缺口"""
    topic: str  # 缺失知识的主题
    query: str  # 具体问题
    confidence: float  # 当前置信度
    detected_at: datetime = field(default_factory=datetime.now)
    

class KnowledgeLearningSystem:
    """
    后台知识学习系统
    
    功能：
    1. 检测知识缺口
    2. 管理学习队列
    3. 闲时调用LLM
    4. 知识结构化存储
    """
    
    def __init__(
        self,
        memory_system: MemorySystem,
        llm_client: Optional[Callable] = None,
        confidence_threshold: float = 0.5,
        max_queue_size: int = 100
    ):
        self.memory = memory_system
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold
        
        # 学习队列
        self.learning_queue: PriorityQueue[LearningTask] = PriorityQueue(maxsize=max_queue_size)
        self.pending_queries: set = set()  # 去重集合
        
        # 学习统计
        self.learned_count = 0
        self.failed_count = 0
        self.skipped_duplicates = 0
        
        # 运行状态
        self.is_running = False
        self.learning_thread: Optional[threading.Thread] = None
        self.idle_threshold = 5.0  # 闲置阈值（秒）
        self.last_activity = time.time()
        
    def detect_knowledge_gap(
        self,
        query: str,
        retrieved_memories: List[MemoryEntry],
        perception_confidence: float
    ) -> Optional[KnowledgeGap]:
        """
        检测知识缺口
        
        当以下条件满足时，认为存在知识缺口：
        1. 记忆检索结果为空或置信度低
        2. 感知系统对输入理解不确定
        3. 问题涉及具体事实性知识
        
        Args:
            query: 用户查询
            retrieved_memories: 检索到的记忆
            perception_confidence: 感知置信度
            
        Returns:
            KnowledgeGap或None
        """
        # 计算记忆覆盖度
        memory_confidence = self._calculate_memory_coverage(query, retrieved_memories)
        
        # 综合置信度
        overall_confidence = (perception_confidence + memory_confidence) / 2
        
        if overall_confidence < self.confidence_threshold:
            # 提取主题
            topic = self._extract_topic(query)
            
            return KnowledgeGap(
                topic=topic,
                query=query,
                confidence=overall_confidence
            )
            
        return None
    
    def enqueue_learning(
        self,
        gap: KnowledgeGap,
        context: Optional[Dict] = None,
        priority: int = 5
    ) -> bool:
        """
        将知识缺口加入学习队列
        
        Args:
            gap: 知识缺口
            context: 额外上下文
            priority: 优先级（1最优先，10最慢）
            
        Returns:
            是否成功加入队列
        """
        # 去重检查
        query_key = self._normalize_query(gap.query)
        if query_key in self.pending_queries:
            self.skipped_duplicates += 1
            return False
            
        task = LearningTask(
            query=gap.query,
            context=context or {},
            priority=priority,
            source=context.get("conversation_id", "unknown")
        )
        
        try:
            self.learning_queue.put(task)
            self.pending_queries.add(query_key)
            return True
        except:
            return False
    
    def learn_now(self, task: LearningTask) -> bool:
        """
        立即执行学习（同步）
        
        用于：
        1. 高优先级知识
        2. 用户明确要求补充
        3. 测试调试
        
        Args:
            task: 学习任务
            
        Returns:
            是否学习成功
        """
        if not self.llm_client:
            return False
            
        try:
            # 1. 构建学习prompt
            prompt = self._build_learning_prompt(task)
            
            # 2. 调用LLM
            llm_response = self.llm_client(prompt)
            
            # 3. 提取结构化知识
            knowledge = self._extract_knowledge(
                task.query,
                llm_response
            )
            
            # 4. 存入记忆系统
            self._store_knowledge(knowledge, task)
            
            # 5. 从待处理集合移除
            query_key = self._normalize_query(task.query)
            self.pending_queries.discard(query_key)
            
            self.learned_count += 1
            return True
            
        except Exception as e:
            self.failed_count += 1
            return False
    
    def start_background_learning(self):
        """启动后台学习线程"""
        if self.is_running:
            return
            
        self.is_running = True
        self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()
        
    def stop_background_learning(self):
        """停止后台学习"""
        self.is_running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=2.0)
            
    def update_activity(self):
        """更新活动时间戳（在主线程调用）"""
        self.last_activity = time.time()
        
    def is_idle(self) -> bool:
        """检查系统是否处于闲置状态"""
        idle_time = time.time() - self.last_activity
        return idle_time > self.idle_threshold
    
    def get_learning_status(self) -> Dict:
        """获取学习系统状态"""
        return {
            "is_running": self.is_running,
            "queue_size": self.learning_queue.qsize(),
            "pending_queries": len(self.pending_queries),
            "learned_count": self.learned_count,
            "failed_count": self.failed_count,
            "skipped_duplicates": self.skipped_duplicates,
            "is_idle": self.is_idle(),
            "idle_time": time.time() - self.last_activity
        }
    
    def _learning_loop(self):
        """后台学习循环"""
        while self.is_running:
            # 检查是否闲置
            if not self.is_idle():
                time.sleep(1.0)
                continue
                
            # 检查队列
            if self.learning_queue.empty():
                time.sleep(2.0)
                continue
                
            # 获取任务
            try:
                task = self.learning_queue.get(timeout=1.0)
            except:
                continue
                
            # 执行学习
            self.learn_now(task)
            
            # 短暂休息，避免占用资源
            time.sleep(0.5)
    
    def _calculate_memory_coverage(
        self,
        query: str,
        memories: List[MemoryEntry]
    ) -> float:
        """计算记忆对查询的覆盖度"""
        if not memories:
            return 0.0
            
        # 基于记忆相关性和数量
        total_score = sum(m.relevance_score for m in memories if hasattr(m, 'relevance_score'))
        coverage = min(1.0, total_score / 3.0)  # 期望3条高质量记忆
        
        return coverage
    
    def _extract_topic(self, query: str) -> str:
        """从查询中提取主题"""
        # 简单提取前10个字符作为主题
        return query[:50] + "..." if len(query) > 50 else query
    
    def _normalize_query(self, query: str) -> str:
        """规范化查询（用于去重）"""
        # 转小写，去除多余空格
        return " ".join(query.lower().split())
    
    def _build_learning_prompt(self, task: LearningTask) -> str:
        """构建学习用的prompt"""
        prompt = f"""请详细解答以下问题，并提供结构化的知识提取：

问题：{task.query}

请按以下格式回答：

[核心概念]
提供2-3个核心概念的定义

[关键事实]
列出3-5个关键事实/知识点

[相关概念]
提及相关的概念或知识领域

[应用场景]
说明这个知识的实际应用场景

[详细解答]
详细的解答内容
"""
        return prompt
    
    def _extract_knowledge(
        self,
        query: str,
        llm_response: str
    ) -> Dict[str, Any]:
        """从LLM响应中提取结构化知识"""
        knowledge = {
            "query": query,
            "raw_response": llm_response,
            "concepts": [],
            "facts": [],
            "related": [],
            "applications": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 简单解析（实际可用更复杂的NLP）
        lines = llm_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if '[核心概念]' in line:
                current_section = 'concepts'
            elif '[关键事实]' in line:
                current_section = 'facts'
            elif '[相关概念]' in line:
                current_section = 'related'
            elif '[应用场景]' in line:
                current_section = 'applications'
            elif line and current_section and not line.startswith('['):
                # 清理markdown标记
                clean_line = line.lstrip('- *•').strip()
                if clean_line:
                    knowledge[current_section].append(clean_line)
        
        # 如果没有结构化提取，保存整段文本
        if not any([knowledge['concepts'], knowledge['facts']]):
            knowledge['facts'].append(llm_response[:500])
            
        return knowledge
    
    def _store_knowledge(self, knowledge: Dict, task: LearningTask):
        """将知识存入记忆系统"""
        # 1. 存储核心概念（语义记忆）
        for concept in knowledge.get('concepts', []):
            self.memory.encode(
                content={
                    "type": "concept",
                    "name": concept.split(':')[0] if ':' in concept else concept,
                    "definition": concept,
                    "source_query": task.query,
                    "learned_from": "llm"
                },
                memory_type=MemoryType.SEMANTIC.value,
                importance=0.7,
                tags=["learned", "concept"]
            )
        
        # 2. 存储关键事实（语义记忆）
        for fact in knowledge.get('facts', []):
            self.memory.encode(
                content={
                    "type": "fact",
                    "statement": fact,
                    "source_query": task.query,
                    "learned_from": "llm"
                },
                memory_type=MemoryType.SEMANTIC.value,
                importance=0.6,
                tags=["learned", "fact"]
            )
        
        # 3. 存储学习事件（情景记忆）
        self.memory.encode(
            content={
                "type": "learning_event",
                "query": task.query,
                "concepts_learned": len(knowledge.get('concepts', [])),
                "facts_learned": len(knowledge.get('facts', [])),
                "timestamp": knowledge.get('timestamp')
            },
            memory_type=MemoryType.EPISODIC.value,
            importance=0.5,
            tags=["learning", "llm_interaction"]
        )


# 简单的LLM客户端示例（实际使用时可替换为真实API）
def create_simple_llm_client() -> Callable[[str], str]:
    """创建简单的LLM客户端（演示用）"""
    def llm_client(prompt: str) -> str:
        # 这里应该调用实际的LLM API
        # 如 OpenAI, Claude, 或本地模型
        return f"""[核心概念]
- 概念A: 这是与问题相关的重要概念
- 概念B: 另一个核心概念的定义

[关键事实]
- 事实1: 关于这个问题的重要事实
- 事实2: 另一个需要知道的事实
- 事实3: 补充的关键信息

[相关概念]
- 相关领域1
- 相关领域2

[应用场景]
- 场景1: 实际应用示例
- 场景2: 另一个应用场景

[详细解答]
这是对"{prompt[:30]}..."的详细解答内容。
在实际实现中，这里会调用真实的LLM API获取答案。
"""
    return llm_client


# 导出
__all__ = [
    'KnowledgeLearningSystem',
    'LearningTask',
    'KnowledgeGap',
    'create_simple_llm_client'
]
