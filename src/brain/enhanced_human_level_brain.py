#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版人类级大脑 (Enhanced Human-Level Brain)

在 HumanLevelBrain 基础上集成：
1. 扩展本地知识库 (ExtendedKnowledgeBase)
2. 知识图谱 (KnowledgeGraph)
3. 强化学习 (ReinforcementLearningSystem)
4. 自我进化增强

这是 Brain 模块的完全体形态。
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import re
from src.utils.logger import setup_logger

logger = setup_logger(name="EnhancedBrain")

from src.brain.human_level_brain import HumanLevelBrain, DevelopmentalStage
from src.utils.llm import LLMClient

# 导入增强模块
try:
    from src.brain.extended_knowledge_base import ExtendedKnowledgeBase, get_knowledge_base
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False

try:
    from src.brain.knowledge_graph import KnowledgeGraph, get_knowledge_graph
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GRAPH_AVAILABLE = False

try:
    from src.brain.reinforcement_learning import (
        ReinforcementLearningSystem, 
        create_rl_enhanced_brain,
        get_rl_system
    )
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False

try:
    from src.brain.self_evolution_system import SelfEvolutionSystem
    SELF_EVOLUTION_AVAILABLE = True
except ImportError:
    SELF_EVOLUTION_AVAILABLE = False


class EnhancedHumanLevelBrain(HumanLevelBrain):
    """
    增强版人类级大脑
    
    集成了所有智能增强模块的完全体 Brain。
    """
    
    def __init__(
        self,
        start_as_infant: bool = False,
        use_persistent_memory: bool = True,
        memory_storage_path: str = "data/chroma_db/brain_memory",
        mode: str = "full",
        # 新增配置参数
        enable_extended_knowledge: bool = True,
        enable_knowledge_graph: bool = True,
        enable_reinforcement_learning: bool = True,
        enable_self_evolution: bool = True,
        knowledge_graph_path: str = "data/brain/knowledge_graph.json",
    ):
        """
        初始化增强版大脑
        
        Args:
            start_as_infant: 是否从婴儿阶段开始
            use_persistent_memory: 是否启用持久化记忆
            memory_storage_path: 记忆存储路径
            mode: 运行模式
            enable_extended_knowledge: 启用扩展知识库
            enable_knowledge_graph: 启用知识图谱
            enable_reinforcement_learning: 启用强化学习
            enable_self_evolution: 启用自我进化
            knowledge_graph_path: 知识图谱存储路径
        """
        super().__init__(
            start_as_infant=start_as_infant,
            use_persistent_memory=use_persistent_memory,
            memory_storage_path=memory_storage_path,
            mode=mode
        )
        
        # 扩展知识库
        self.extended_knowledge = None
        self.enable_extended_knowledge = enable_extended_knowledge and KNOWLEDGE_BASE_AVAILABLE
        if self.enable_extended_knowledge:
            self.extended_knowledge = get_knowledge_base()
            logger.info(f"📚 扩展知识库已启用 | {len(self.extended_knowledge.domains)} 个领域")
        
        # 知识图谱
        self.knowledge_graph = None
        self.enable_knowledge_graph = enable_knowledge_graph and KNOWLEDGE_GRAPH_AVAILABLE
        if self.enable_knowledge_graph:
            self.knowledge_graph = get_knowledge_graph()
            try:
                self.knowledge_graph.load(knowledge_graph_path)
                logger.info(f"🕸️ 知识图谱已加载 | 路径: {knowledge_graph_path}")
            except FileNotFoundError:
                logger.info(f"🕸️ 知识图谱已初始化 | 路径: {knowledge_graph_path}")
        
        # 强化学习系统
        self.rl_system = None
        self.enable_rl = enable_reinforcement_learning and RL_AVAILABLE
        if self.enable_rl:
            self.rl_system = get_rl_system()
            logger.info("🎯 强化学习系统已启用")
        
        # 自我进化系统
        self.self_evolution = None
        self.enable_self_evolution = enable_self_evolution and SELF_EVOLUTION_AVAILABLE
        if self.enable_self_evolution:
            self.self_evolution = SelfEvolutionSystem()
            logger.info("🧬 自我进化系统已启用")
        
        # 当前交互上下文（用于 RL 学习）
        self.current_context = {}
        self.selected_strategy = None
        self.last_response_time = None
        
        # 处理统计
        self.processing_stats = {
            "total_interactions": 0,
            "local_hits": 0,
            "llm_fallbacks": 0,
            "knowledge_graph_queries": 0,
            "rl_strategy_selections": 0,
        }
    
    # ==================== 核心处理流程 ====================
    
    async def process_with_enhancement(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """
        增强版处理流程
        
        整合所有增强模块的智能处理流程：
        1. 扩展知识库检索
        2. 知识图谱查询
        3. 强化学习策略选择
        4. 本地/LLM 混合处理
        5. 学习与进化
        """
        context = context or {}
        start_time = datetime.now()
        
        # 构建上下文
        self.current_context = {
            "input": user_input,
            "has_code": self._detect_code_context(user_input),
            "emotion": context.get("emotion", "neutral"),
            "history_length": len(self.life_narrative) if hasattr(self, 'life_narrative') else 0,
            "domain": self._classify_domain(user_input),
            "timestamp": start_time.isoformat(),
        }
        
        response_parts = []
        knowledge_sources = []
        
        # Step 1: 扩展知识库检索 (L3增强)
        if self.enable_extended_knowledge:
            kb_response = self._query_extended_knowledge(user_input)
            if kb_response:
                response_parts.append(kb_response)
                knowledge_sources.append("extended_knowledge_base")
                self.processing_stats["local_hits"] += 1
        
        # Step 2: 知识图谱查询
        if self.enable_knowledge_graph and not response_parts:
            kg_response = self._query_knowledge_graph(user_input)
            if kg_response:
                response_parts.append(kg_response)
                knowledge_sources.append("knowledge_graph")
                self.processing_stats["knowledge_graph_queries"] += 1
        
        # Step 3: 强化学习策略选择
        processing_level = "L5_llm"  # 默认使用 LLM
        if self.enable_rl:
            processing_level = self._select_processing_level()
            self.selected_strategy = processing_level
            self.processing_stats["rl_strategy_selections"] += 1
        
        # Step 4: 根据策略选择处理方式
        final_response = None
        
        if processing_level in ["L1_template", "L2_rules", "L3_semantic"] and response_parts:
            # 本地处理已生成回复
            final_response = "\n\n".join(response_parts)
        elif processing_level == "L4_inference":
            # 本地推理 + 可能的 LLM 增强
            final_response = await self._local_inference_with_llm(user_input, response_parts)
        else:
            # L5: 使用 LLM 生成
            final_response = await self._generate_with_llm(user_input, context, response_parts)
            self.processing_stats["llm_fallbacks"] += 1
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        self.last_response_time = processing_time
        
        # Step 5: 学习与进化
        if self.enable_rl or self.enable_self_evolution:
            await self._learn_from_interaction(
                user_input, final_response, context, processing_level
            )
        
        # 更新统计
        self.processing_stats["total_interactions"] += 1
        
        return {
            "response": final_response,
            "processing_level": processing_level,
            "knowledge_sources": knowledge_sources,
            "processing_time": processing_time,
            "context": self.current_context,
        }
    
    # ==================== 知识库查询 ====================
    
    def _query_extended_knowledge(self, query: str) -> Optional[str]:
        """查询扩展知识库"""
        if not self.extended_knowledge:
            return None
        
        # 搜索知识库
        matches = self.extended_knowledge.search(query)
        if not matches:
            return None
        
        # 返回最高优先级匹配的回复
        knowledge = matches[0]
        import random
        response = random.choice(knowledge.responses)
        
        # 记录知识来源
        return response
    
    def _query_knowledge_graph(self, query: str) -> Optional[str]:
        """查询知识图谱"""
        if not self.knowledge_graph:
            return None
        
        # 尝试提取实体
        result = self.knowledge_graph.query(query)
        
        if result.get("matches"):
            # 有实体匹配
            match = result["matches"][0]
            entity = match.get("entity", {})
            return self.knowledge_graph.get_knowledge_summary(entity.get("name", ""))
        
        if result.get("inferred"):
            # 有推理结果
            return f"根据我的知识：{result['inferred']}"
        
        return None
    
    # ==================== 强化学习策略 ====================
    
    def _select_processing_level(self) -> str:
        """使用 RL 选择处理级别"""
        if not self.rl_system:
            return "L5_llm"
        
        strategies = ["L1_template", "L2_rules", "L3_semantic", "L4_inference", "L5_llm"]
        
        strategy = self.rl_system.select_response_strategy(
            self.current_context,
            strategies
        )
        
        return strategy
    
    def learn_from_feedback(self, feedback: float, feedback_type: str = "explicit"):
        """
        从用户反馈中学习
        
        Args:
            feedback: -1.0 (非常不满意) 到 1.0 (非常满意)
            feedback_type: 反馈类型 (explicit/implicit)
        """
        if self.enable_rl and self.selected_strategy:
            self.rl_system.learn_from_feedback(
                task_id="response_selection",
                context=self.current_context,
                selected_strategy=self.selected_strategy,
                reward=feedback
            )
            logger.info(f"🎯 RL 学习: {self.selected_strategy} → 反馈 {feedback:+.2f}")
        
        if self.enable_self_evolution:
            # 记录经验到自我进化系统
            experience = {
                "situation": self.current_context.get("input", ""),
                "action": self.selected_strategy,
                "outcome": f"user_feedback: {feedback}",
                "reward": feedback,
            }
            self.self_evolution.add_experience(experience)
    
    # ==================== 辅助方法 ====================
    
    def _detect_code_context(self, text: str) -> bool:
        """检测是否为代码相关上下文"""
        code_keywords = [
            "code", "programming", "python", "javascript", "java", "bug",
            "error", "exception", "function", "class", "def", "import",
            "代码", "编程", "报错", "错误", "函数", "类"
        ]
        return any(kw in text.lower() for kw in code_keywords)
    
    def _classify_domain(self, text: str) -> str:
        """分类领域"""
        domains = {
            "technical": ["python", "java", "code", "programming", "debug", "算法"],
            "emotional": ["难过", "开心", "焦虑", "压力", "feel", "sad", "happy", "stress"],
            "creative": ["write", "story", "创意", "写作", "创作"],
            "learning": ["learn", "study", "学习", "怎么学"],
            "business": ["career", "job", "职业", "工作", "项目"],
        }
        
        text_lower = text.lower()
        for domain, keywords in domains.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        
        return "general"
    
    async def _local_inference_with_llm(
        self, 
        user_input: str, 
        existing_parts: List[str]
    ) -> str:
        """本地推理 + LLM 增强"""
        # 组合已有知识和用户输入
        context = "\n\n".join(existing_parts) if existing_parts else ""
        
        prompt = f"""基于以下背景信息，回复用户的问题：

背景信息：
{context}

用户问题：{user_input}

请给出有帮助的回复："""
        
        try:
            response = await self.llm_client.achat(prompt)
            return response
        except Exception as e:
            # 降级处理
            if existing_parts:
                return "\n\n".join(existing_parts)
            return f"我在思考这个问题时遇到了一些困难。请稍后再试。"
    
    async def _generate_with_llm(
        self, 
        user_input: str, 
        context: Dict,
        existing_parts: List[str]
    ) -> str:
        """使用 LLM 生成回复"""
        # 构建增强的 prompt
        knowledge_context = "\n\n".join(existing_parts) if existing_parts else ""
        
        prompt = user_input
        if knowledge_context:
            prompt = f"[背景知识]\n{knowledge_context}\n\n[用户问题]\n{user_input}"
        
        try:
            response = await self.llm_client.achat(prompt)
            return response
        except Exception as e:
            return f"抱歉，我现在无法处理这个问题。错误: {str(e)}"
    
    async def _learn_from_interaction(
        self,
        user_input: str,
        response: str,
        context: Dict,
        strategy: str
    ):
        """从交互中学习"""
        # 隐式反馈：基于响应时间的简单奖励
        if self.last_response_time:
            if self.last_response_time < 0.5:  # 快速响应
                implicit_reward = 0.1
            elif self.last_response_time > 2.0:  # 慢速响应
                implicit_reward = -0.05
            else:
                implicit_reward = 0.0
            
            # 只在 RL 启用且有策略选择时学习
            if self.enable_rl and self.selected_strategy:
                # 注意：这里只是隐式学习，真正的反馈需要用户显式提供
                pass
    
    # ==================== 统计与导出 ====================
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """获取增强模块统计信息"""
        stats = {
            "base_brain": self.get_human_state_summary() if hasattr(self, 'get_human_state_summary') else {},
            "processing_stats": self.processing_stats,
            "enhanced_features": {
                "extended_knowledge": self.enable_extended_knowledge,
                "knowledge_graph": self.enable_knowledge_graph,
                "reinforcement_learning": self.enable_rl,
                "self_evolution": self.enable_self_evolution,
            },
        }
        
        # 知识库统计
        if self.enable_extended_knowledge and self.extended_knowledge:
            stats["knowledge_base"] = self.extended_knowledge.get_stats()
        
        # 知识图谱统计
        if self.enable_knowledge_graph and self.knowledge_graph:
            stats["knowledge_graph"] = self.knowledge_graph.get_stats()
        
        # RL 统计
        if self.enable_rl and self.rl_system:
            stats["reinforcement_learning"] = self.rl_system.get_learning_stats("response_selection")
        
        return stats
    
    def save_state(self, directory: str):
        """保存所有状态"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        # 保存知识图谱
        if self.enable_knowledge_graph and self.knowledge_graph:
            kg_path = os.path.join(directory, "knowledge_graph.json")
            self.knowledge_graph.save(kg_path)
        
        # 保存 RL 模型
        if self.enable_rl and self.rl_system:
            rl_dir = os.path.join(directory, "rl_models")
            self.rl_system.save_all(rl_dir)
        
        # 保存处理统计
        stats_path = os.path.join(directory, "processing_stats.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.processing_stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 增强大脑状态已保存到: {directory}")
    
    def load_state(self, directory: str):
        """加载所有状态"""
        import os
        
        # 加载知识图谱
        if self.enable_knowledge_graph and self.knowledge_graph:
            kg_path = os.path.join(directory, "knowledge_graph.json")
            if os.path.exists(kg_path):
                self.knowledge_graph.load(kg_path)
        
        # 加载 RL 模型
        if self.enable_rl and self.rl_system:
            rl_dir = os.path.join(directory, "rl_models")
            if os.path.exists(rl_dir):
                self.rl_system.load_all(rl_dir)
        
        # 加载处理统计
        stats_path = os.path.join(directory, "processing_stats.json")
        if os.path.exists(stats_path):
            with open(stats_path, 'r', encoding='utf-8') as f:
                self.processing_stats = json.load(f)
        
        logger.info(f"📂 增强大脑状态已从 {directory} 加载")


# ==================== 便捷函数 ====================

def create_enhanced_brain(
    start_as_infant: bool = False,
    use_persistent_memory: bool = True,
    enable_all_features: bool = True,
) -> EnhancedHumanLevelBrain:
    """
    创建增强版大脑实例
    
    这是创建增强版 Brain 的推荐方式。
    """
    return EnhancedHumanLevelBrain(
        start_as_infant=start_as_infant,
        use_persistent_memory=use_persistent_memory,
        enable_extended_knowledge=enable_all_features,
        enable_knowledge_graph=enable_all_features,
        enable_reinforcement_learning=enable_all_features,
        enable_self_evolution=enable_all_features,
    )


# 全局实例
_enhanced_brain = None


def get_enhanced_brain() -> EnhancedHumanLevelBrain:
    """获取全局增强大脑实例"""
    global _enhanced_brain
    if _enhanced_brain is None:
        _enhanced_brain = create_enhanced_brain()
    return _enhanced_brain
