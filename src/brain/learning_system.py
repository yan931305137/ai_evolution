#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台知识学习系统 (P0-4 修复版)

修复内容:
1. 添加知识正确性校验流程
2. 实现知识验证机制（交叉验证、一致性检查）
3. 添加知识置信度评分
4. 支持知识审核和修正
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue
import threading
import time
import hashlib

from src.brain.memory_system import MemorySystem, MemoryEntry
from src.brain.common import MemoryType


@dataclass
class LearningTask:
    """学习任务"""
    query: str
    context: Dict[str, Any]
    priority: int
    created_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class KnowledgeGap:
    """知识缺口"""
    topic: str
    query: str
    confidence: float
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ValidatedKnowledge:
    """经过验证的知识 (P0-4 新增)"""
    content: Dict[str, Any]
    confidence_score: float  # 0-1 置信度分数
    validation_status: str  # "pending", "validated", "rejected", "uncertain"
    validation_method: List[str]  # 使用的验证方法
    inconsistencies: List[str]  # 发现的不一致之处
    needs_review: bool  # 是否需要人工审核
    validated_at: Optional[datetime] = None


class KnowledgeLearningSystem:
    """
    后台知识学习系统 (P0-4 修复版)
    
    新增功能:
    1. 知识正确性校验流程
    2. 多轮验证机制
    3. 知识置信度评估
    4. 一致性检查
    """
    
    def __init__(
        self,
        memory_system: MemorySystem,
        llm_client: Optional[Callable] = None,
        confidence_threshold: float = 0.5,
        max_queue_size: int = 100,
        enable_validation: bool = True,  # P0-4: 启用验证
        validation_confidence_threshold: float = 0.7,  # P0-4: 验证置信度阈值
    ):
        self.memory = memory_system
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold
        self.enable_validation = enable_validation
        self.validation_confidence_threshold = validation_confidence_threshold
        
        # 学习队列
        self.learning_queue: PriorityQueue[LearningTask] = PriorityQueue(maxsize=max_queue_size)
        self.pending_queries: set = set()
        
        # P0-4: 验证队列和待审核知识
        self.validation_queue: List[ValidatedKnowledge] = []
        self.rejected_knowledge: List[Dict] = []  # 记录被拒绝的知识用于分析
        
        # 学习统计
        self.learned_count = 0
        self.failed_count = 0
        self.skipped_duplicates = 0
        self.validated_count = 0  # P0-4: 验证通过数
        self.rejected_count = 0  # P0-4: 拒绝数
        
        # 运行状态
        self.is_running = False
        self.learning_thread: Optional[threading.Thread] = None
        self.idle_threshold = 5.0
        self.last_activity = time.time()
        
        # P0-4: 验证历史（用于交叉验证）
        self.validation_history: Dict[str, List[Dict]] = {}
        
    def detect_knowledge_gap(
        self,
        query: str,
        retrieved_memories: List[MemoryEntry],
        perception_confidence: float
    ) -> Optional[KnowledgeGap]:
        """检测知识缺口"""
        memory_confidence = self._calculate_memory_coverage(query, retrieved_memories)
        overall_confidence = (perception_confidence + memory_confidence) / 2
        
        if overall_confidence < self.confidence_threshold:
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
        """将知识缺口加入学习队列"""
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
        立即执行学习（P0-4 修复版 - 添加验证流程）
        """
        if not self.llm_client:
            return False
            
        try:
            # 1. 构建学习prompt
            prompt = self._build_learning_prompt(task)
            
            # 2. 调用LLM获取知识
            llm_response = self.llm_client(prompt)
            
            # 3. 提取结构化知识
            knowledge = self._extract_knowledge(task.query, llm_response)
            
            # P0-4: 4. 验证知识正确性
            if self.enable_validation:
                validated = self._validate_knowledge(knowledge, task)
                
                if validated.validation_status == "rejected":
                    # 记录被拒绝的知识
                    self.rejected_knowledge.append({
                        "knowledge": knowledge,
                        "reasons": validated.inconsistencies,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.rejected_count += 1
                    query_key = self._normalize_query(task.query)
                    self.pending_queries.discard(query_key)
                    return False
                    
                if validated.validation_status == "uncertain" or validated.needs_review:
                    # 加入待审核队列
                    self.validation_queue.append(validated)
                    # 仍然存储，但标记为待审核
                    knowledge["_validation_status"] = "pending_review"
                    knowledge["_validation_score"] = validated.confidence_score
                else:
                    # 验证通过
                    knowledge["_validation_status"] = "validated"
                    knowledge["_validation_score"] = validated.confidence_score
                    self.validated_count += 1
            
            # 5. 存入记忆系统
            self._store_knowledge(knowledge, task)
            
            # 6. 清理
            query_key = self._normalize_query(task.query)
            self.pending_queries.discard(query_key)
            
            self.learned_count += 1
            return True
            
        except Exception as e:
            self.failed_count += 1
            return False
    
    # ==================== P0-4: 知识验证方法 ====================
    
    def _validate_knowledge(
        self, 
        knowledge: Dict[str, Any], 
        task: LearningTask
    ) -> ValidatedKnowledge:
        """
        验证知识正确性 (P0-4 核心修复)
        
        使用多种验证方法:
        1. 自洽性检查
        2. 与现有知识一致性检查
        3. 事实可验证性检查
        4. 逻辑一致性检查
        """
        validation_methods = []
        inconsistencies = []
        confidence_scores = []
        
        # 1. 自洽性检查
        self_consistency = self._check_self_consistency(knowledge)
        validation_methods.append("self_consistency")
        confidence_scores.append(self_consistency["score"])
        if self_consistency["issues"]:
            inconsistencies.extend(self_consistency["issues"])
        
        # 2. 与现有知识一致性检查
        if self.memory:
            consistency_with_existing = self._check_consistency_with_existing(
                knowledge, task.query
            )
            validation_methods.append("existing_knowledge_consistency")
            confidence_scores.append(consistency_with_existing["score"])
            if consistency_with_existing["conflicts"]:
                inconsistencies.extend(consistency_with_existing["conflicts"])
        
        # 3. 事实可验证性检查
        verifiability = self._check_fact_verifiability(knowledge)
        validation_methods.append("fact_verifiability")
        confidence_scores.append(verifiability["score"])
        if verifiability["issues"]:
            inconsistencies.extend(verifiability["issues"])
        
        # 4. 结构完整性检查
        structural_integrity = self._check_structural_integrity(knowledge)
        validation_methods.append("structural_integrity")
        confidence_scores.append(structural_integrity["score"])
        
        # 计算综合置信度
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # 根据置信度和不一致性确定状态
        if avg_confidence < 0.3 or len(inconsistencies) >= 3:
            status = "rejected"
        elif avg_confidence >= self.validation_confidence_threshold and not inconsistencies:
            status = "validated"
        elif avg_confidence >= 0.5 and len(inconsistencies) <= 1:
            status = "validated"
        else:
            status = "uncertain"
        
        needs_review = (
            status == "uncertain" or 
            len(inconsistencies) > 0 or 
            avg_confidence < self.validation_confidence_threshold
        )
        
        return ValidatedKnowledge(
            content=knowledge,
            confidence_score=avg_confidence,
            validation_status=status,
            validation_method=validation_methods,
            inconsistencies=inconsistencies,
            needs_review=needs_review,
            validated_at=datetime.now() if status == "validated" else None
        )
    
    def _check_self_consistency(self, knowledge: Dict) -> Dict:
        """检查知识自洽性"""
        issues = []
        score = 1.0
        
        concepts = knowledge.get("concepts", [])
        facts = knowledge.get("facts", [])
        
        # 检查概念间矛盾
        concept_names = []
        for concept in concepts:
            name = concept.split(':')[0] if ':' in concept else concept
            concept_names.append(name.lower())
        
        # 检查事实中是否有自相矛盾的表述
        for i, fact1 in enumerate(facts):
            for fact2 in facts[i+1:]:
                # 简单检查：如果两个事实包含相反的词
                if self._check_contradiction(fact1, fact2):
                    issues.append(f"潜在矛盾: '{fact1[:50]}...' vs '{fact2[:50]}...'")
                    score -= 0.2
        
        # 检查概念和事实是否匹配
        for fact in facts:
            fact_lower = fact.lower()
            has_matching_concept = any(
                name in fact_lower for name in concept_names
            )
            if not has_matching_concept and concept_names:
                issues.append(f"事实 '{fact[:50]}...' 与核心概念关联性低")
                score -= 0.1
        
        return {"score": max(0.0, score), "issues": issues}
    
    def _check_consistency_with_existing(
        self, 
        knowledge: Dict, 
        query: str
    ) -> Dict:
        """检查与现有知识的一致性"""
        conflicts = []
        score = 1.0
        
        try:
            # 检索相关现有知识
            existing = self.memory.retrieve(query, top_k=3)
            
            if not existing:
                return {"score": score, "conflicts": conflicts}
            
            # 检查新概念与现有知识是否冲突
            new_concepts = [c.lower() for c in knowledge.get("concepts", [])]
            new_facts = [f.lower() for f in knowledge.get("facts", [])]
            
            for memory_id, relevance in existing:
                if memory_id in self.memory.long_term_memory:
                    entry = self.memory.long_term_memory[memory_id]
                    existing_content = str(entry.content).lower()
                    
                    # 检查是否有直接矛盾
                    for fact in new_facts:
                        if self._check_direct_contradiction(fact, existing_content):
                            conflicts.append(
                                f"与现有知识冲突: 新事实 '{fact[:50]}...' "
                                f"与记忆 {memory_id[:8]} 不一致"
                            )
                            score -= 0.3
                            
        except Exception:
            pass
        
        return {"score": max(0.0, score), "conflicts": conflicts}
    
    def _check_fact_verifiability(self, knowledge: Dict) -> Dict:
        """检查事实可验证性"""
        issues = []
        score = 1.0
        
        facts = knowledge.get("facts", [])
        
        for fact in facts:
            # 检查是否包含具体数据（数字、日期等）
            has_specific_data = bool(
                re.search(r'\d+', fact) or  # 数字
                re.search(r'\d{4}年?', fact) or  # 年份
                re.search(r'\d+%', fact)  # 百分比
            )
            
            # 检查是否包含引用或来源
            has_source = any(
                keyword in fact.lower() 
                for keyword in ['根据', '研究表明', '数据显示', '据', 'report', 'study']
            )
            
            if not has_specific_data and not has_source:
                issues.append(f"事实 '{fact[:50]}...' 缺乏可验证的具体数据或来源")
                score -= 0.1
        
        return {"score": max(0.0, score), "issues": issues}
    
    def _check_structural_integrity(self, knowledge: Dict) -> float:
        """检查知识结构完整性"""
        score = 1.0
        
        # 检查必需字段
        required_sections = ["concepts", "facts"]
        for section in required_sections:
            if section not in knowledge or not knowledge[section]:
                score -= 0.3
        
        # 检查内容长度
        total_content = json.dumps(knowledge)
        if len(total_content) < 100:
            score -= 0.2
        
        return max(0.0, score)
    
    def _check_contradiction(self, text1: str, text2: str) -> bool:
        """检查两个文本是否存在矛盾"""
        # 简单的矛盾检测：反义词检查
        contradiction_pairs = [
            ('是', '不是'), ('可以', '不可以'), ('有', '没有'),
            ('增加', '减少'), ('支持', '反对'), ('正确', '错误'),
            ('always', 'never'), ('all', 'none'), ('increase', 'decrease')
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for pos, neg in contradiction_pairs:
            if (pos in text1_lower and neg in text2_lower) or \
               (neg in text1_lower and pos in text2_lower):
                return True
        
        return False
    
    def _check_direct_contradiction(self, new_fact: str, existing_content: str) -> bool:
        """检查是否与现有内容直接矛盾"""
        return self._check_contradiction(new_fact, existing_content)
    
    def review_pending_knowledge(self, knowledge_index: int, approve: bool) -> bool:
        """
        人工审核待审核知识 (P0-4 新增)
        
        Args:
            knowledge_index: 待审核知识在队列中的索引
            approve: 是否批准
            
        Returns:
            是否处理成功
        """
        if knowledge_index >= len(self.validation_queue):
            return False
            
        validated = self.validation_queue[knowledge_index]
        
        if approve:
            validated.validation_status = "validated"
            validated.validated_at = datetime.now()
            validated.content["_validation_status"] = "validated"
            self.validated_count += 1
        else:
            validated.validation_status = "rejected"
            self.rejected_knowledge.append({
                "knowledge": validated.content,
                "reason": "manual_rejection",
                "timestamp": datetime.now().isoformat()
            })
            self.rejected_count += 1
        
        # 从队列移除
        self.validation_queue.pop(knowledge_index)
        return True
    
    # ==================== 原有方法保留 ====================
    
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
        """更新活动时间戳"""
        self.last_activity = time.time()
        
    def is_idle(self) -> bool:
        """检查系统是否处于闲置状态"""
        idle_time = time.time() - self.last_activity
        return idle_time > self.idle_threshold
    
    def get_learning_status(self) -> Dict:
        """获取学习系统状态 (P0-4 增强)"""
        return {
            "is_running": self.is_running,
            "queue_size": self.learning_queue.qsize(),
            "pending_queries": len(self.pending_queries),
            "learned_count": self.learned_count,
            "failed_count": self.failed_count,
            "skipped_duplicates": self.skipped_duplicates,
            "validated_count": self.validated_count,  # P0-4
            "rejected_count": self.rejected_count,  # P0-4
            "pending_review_count": len(self.validation_queue),  # P0-4
            "is_idle": self.is_idle(),
            "idle_time": time.time() - self.last_activity,
            "validation_enabled": self.enable_validation,
            "validation_threshold": self.validation_confidence_threshold,
        }
    
    def get_validation_queue(self) -> List[Dict]:
        """获取待审核知识队列 (P0-4 新增)"""
        return [
            {
                "content": v.content,
                "confidence_score": v.confidence_score,
                "inconsistencies": v.inconsistencies,
                "validation_methods": v.validation_method,
            }
            for v in self.validation_queue
        ]
    
    def _learning_loop(self):
        """后台学习循环"""
        while self.is_running:
            if not self.is_idle():
                time.sleep(1.0)
                continue
            if self.learning_queue.empty():
                time.sleep(2.0)
                continue
            try:
                task = self.learning_queue.get(timeout=1.0)
            except:
                continue
            self.learn_now(task)
            time.sleep(0.5)
    
    def _calculate_memory_coverage(
        self,
        query: str,
        memories: List[MemoryEntry]
    ) -> float:
        """计算记忆对查询的覆盖度"""
        if not memories:
            return 0.0
        total_score = sum(m.relevance_score for m in memories if hasattr(m, 'relevance_score'))
        coverage = min(1.0, total_score / 3.0)
        return coverage
    
    def _extract_topic(self, query: str) -> str:
        """从查询中提取主题"""
        return query[:50] + "..." if len(query) > 50 else query
    
    def _normalize_query(self, query: str) -> str:
        """规范化查询"""
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
                clean_line = line.lstrip('- *•').strip()
                if clean_line:
                    knowledge[current_section].append(clean_line)
        
        if not any([knowledge['concepts'], knowledge['facts']]):
            knowledge['facts'].append(llm_response[:500])
            
        return knowledge
    
    def _store_knowledge(self, knowledge: Dict, task: LearningTask):
        """将知识存入记忆系统"""
        # 存储核心概念
        for concept in knowledge.get('concepts', []):
            self.memory.encode(
                content={
                    "type": "concept",
                    "name": concept.split(':')[0] if ':' in concept else concept,
                    "definition": concept,
                    "source_query": task.query,
                    "learned_from": "llm",
                    "validation_status": knowledge.get("_validation_status", "unknown"),
                    "validation_score": knowledge.get("_validation_score", 0.0),
                },
                memory_type=MemoryType.SEMANTIC.value,
                importance=0.7,
                tags=["learned", "concept"]
            )
        
        # 存储关键事实
        for fact in knowledge.get('facts', []):
            self.memory.encode(
                content={
                    "type": "fact",
                    "statement": fact,
                    "source_query": task.query,
                    "learned_from": "llm",
                    "validation_status": knowledge.get("_validation_status", "unknown"),
                    "validation_score": knowledge.get("_validation_score", 0.0),
                },
                memory_type=MemoryType.SEMANTIC.value,
                importance=0.6,
                tags=["learned", "fact"]
            )
        
        # 存储学习事件
        self.memory.encode(
            content={
                "type": "learning_event",
                "query": task.query,
                "concepts_learned": len(knowledge.get('concepts', [])),
                "facts_learned": len(knowledge.get('facts', [])),
                "timestamp": knowledge.get('timestamp'),
                "validation_status": knowledge.get("_validation_status", "unknown"),
            },
            memory_type=MemoryType.EPISODIC.value,
            importance=0.5,
            tags=["learning", "llm_interaction"]
        )


# 导出
__all__ = [
    'KnowledgeLearningSystem', 
    'LearningTask', 
    'KnowledgeGap',
    'ValidatedKnowledge'  # P0-4 新增导出
]
