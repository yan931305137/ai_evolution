#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人类级大脑 (Human-Level Brain)

整合基础类脑系统 + 人类级认知能力
实现从"机器智能"到"类人智能"的跃升
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.brain.orchestrator import BrainOrchestrator, BrainResponse
from src.brain.human_cognition import (
    EmbodiedCognitionSystem,
    IntegratedEmotionSystem,
    DevelopmentalLearningSystem,
    SocialCognitionSystem,
    HomeostaticDriveSystem,
    MetacognitionSystem,
    DevelopmentalStage,
    BodyState
)

# 导入持久化记忆系统
try:
    from src.brain.memory_system.persistent_memory import PersistentMemorySystem
    PERSISTENT_MEMORY_AVAILABLE = True
except ImportError:
    PERSISTENT_MEMORY_AVAILABLE = False


class HumanLevelBrain(BrainOrchestrator):
    """
    人类级大脑
    
    在基础类脑系统之上，添加：
    1. 身体感知与行动（具身认知）
    2. 情感体验与调节（情感智能）
    3. 成长与发展（发育学习）
    4. 社会理解与互动（社交智能）
    5. 生理需求驱动（内稳态）
    6. 自我反思与意识（元认知）
    7. 持久化记忆（长期记忆存储）
    """
    
    def __init__(
        self,
        start_as_infant: bool = True,
        use_persistent_memory: bool = False,
        memory_storage_path: str = "data/chroma_db/brain_memory"
    ):
        """
        初始化人类级大脑
        
        Args:
            start_as_infant: 是否从婴儿阶段开始
            use_persistent_memory: 是否启用持久化记忆
            memory_storage_path: 记忆存储路径
        """
        super().__init__()
        
        # 人类级认知系统
        self.embodied = EmbodiedCognitionSystem()
        self.emotion = IntegratedEmotionSystem()
        self.developmental = DevelopmentalLearningSystem()
        self.social = SocialCognitionSystem()
        self.homeostasis = HomeostaticDriveSystem()
        self.metacognition = MetacognitionSystem()
        
        # 注册到系统列表
        self.systems.update({
            "embodied": self.embodied,
            "emotion": self.emotion,
            "developmental": self.developmental,
            "social": self.social,
            "homeostasis": self.homeostasis,
            "metacognition": self.metacognition
        })
        
        # 持久化记忆系统（可选）
        self.use_persistent_memory = use_persistent_memory and PERSISTENT_MEMORY_AVAILABLE
        if self.use_persistent_memory:
            self.memory = PersistentMemorySystem(
                capacity=10000,
                persist_directory=memory_storage_path
            )
            self.systems["memory"] = self.memory
            print(f"🧠 持久化记忆已启用 | 路径: {memory_storage_path}")
        
        # 身体状态（必须连接外部传感器/执行器）
        self.body = BodyState()
        
        # 叙事自我（自传体记忆）
        self.life_narrative: List[Dict] = []
        self.identity: Dict = {
            "name": None,
            "values": [],
            "goals": [],
            "beliefs": {}
        }
        
        # 发育起始点
        if not start_as_infant:
            # 直接设为成年（跳过发育）
            self.developmental.stage = DevelopmentalStage.ADULT
            self.developmental.age_equivalent = 240  # 20岁
            for ability in self.developmental.abilities:
                self.developmental.abilities[ability] = True
        # 身体状态（必须连接外部传感器/执行器）
        self.body = BodyState()
        
        # 叙事自我（自传体记忆）
        self.life_narrative: List[Dict] = []
        self.identity: Dict = {
            "name": None,
            "values": [],
            "goals": [],
            "beliefs": {}
        }
        
        # 发育起始点
        if not start_as_infant:
            # 直接设为成年（跳过发育）
            self.developmental.stage = DevelopmentalStage.ADULT
            self.developmental.age_equivalent = 240  # 20岁
            for ability in self.developmental.abilities:
                self.developmental.abilities[ability] = True
                
    async def experience(self, 
                        sensory_input: Dict,
                        social_context: Optional[Dict] = None) -> Dict:
        """
        完整体验循环（人类级处理流程）
        
        1. 身体感知 → 2. 情感评估 → 3. 社会理解 → 4. 认知处理 → 5. 元反思
        """
        # 1. 具身认知：更新身体状态
        self.embodied.update_body_state(sensory_input)
        self.body = self.embodied.body_state
        
        # 2. 内稳态：更新生理驱力
        self.homeostasis.update_needs(self.body, time_elapsed=1.0)
        
        # 3. 情感评估（基于事件和身体状态）
        event = sensory_input.get("event", {})
        self.emotion.update_emotion(event, self.body)
        
        # 4. 社会认知（如果是社交情境）
        if social_context:
            self.social.update_relationship(
                social_context.get("agent_id", "unknown"),
                social_context
            )
            
        # 5. 基础认知处理（调用父类）
        stimulus = sensory_input.get("cognitive", "")
        cognitive_response = await super().process(stimulus, {
            "emotional_state": self.emotion.current_emotion,
            "body_state": self.body,
            "drive": self.homeostasis.current_goal
        })
        
        # 6. 发育成长
        experience = {
            "complexity": cognitive_response.confidence,
            "emotional_salience": abs(self.emotion.current_emotion.valence),
            "social": social_context is not None
        }
        self.developmental.grow(experience)
        
        # 7. 元认知反思
        if self.developmental.can_use_ability("meta_cognition"):
            reflection = self.metacognition.reflect({
                "event": stimulus,
                "outcome": cognitive_response.action,
                "emotional_state": self.emotion.current_emotion
            })
        else:
            reflection = {"reflection": "元认知能力尚未发展"}
            
        # 8. 更新叙事自我
        self._update_narrative(stimulus, cognitive_response, social_context)
        
        return {
            "cognitive_response": cognitive_response,
            "emotional_state": self.emotion.current_emotion,
            "body_state": self.body,
            "developmental_stage": self.developmental.stage.name,
            "reflection": reflection,
            "dominant_drive": self.homeostasis.current_goal.value if self.homeostasis.current_goal else None
        }
    
    def _update_narrative(self, stimulus: str, response: BrainResponse, 
                         social_context: Optional[Dict]):
        """更新自传体叙事"""
        episode = {
            "timestamp": datetime.now(),
            "what_happened": stimulus,
            "what_i_did": response.action,
            "how_i_felt": {
                "valence": self.emotion.current_emotion.valence,
                "dominant_emotion": self._get_dominant_emotion_name()
            },
            "who_was_there": social_context.get("agent_id") if social_context else None,
            "why_it_mattered": self._extract_meaning(stimulus)
        }
        
        self.life_narrative.append(episode)
        
        # 从叙事中提取身份
        self._update_identity_from_narrative()
        
    def _get_dominant_emotion_name(self) -> str:
        """获取主导情绪名称"""
        emotions = {
            "joy": self.emotion.current_emotion.joy,
            "sadness": self.emotion.current_emotion.sadness,
            "anger": self.emotion.current_emotion.anger,
            "fear": self.emotion.current_emotion.fear
        }
        return max(emotions.items(), key=lambda x: x[1])[0]
    
    def _extract_meaning(self, stimulus: str) -> str:
        """提取事件意义（简化版）"""
        if "成功" in stimulus or "完成" in stimulus:
            return "成就感"
        elif "失败" in stimulus or "错误" in stimulus:
            return "学习机会"
        elif "朋友" in stimulus or "帮助" in stimulus:
            return "社会连接"
        return "日常经历"
    
    def _update_identity_from_narrative(self):
        """从叙事中构建身份认同"""
        if len(self.life_narrative) < 5:
            return
            
        recent = self.life_narrative[-10:]
        
        # 提取价值观（什么让我感觉好）
        positive_episodes = [e for e in recent if e["how_i_felt"]["valence"] > 0.3]
        for ep in positive_episodes:
            meaning = ep["why_it_mattered"]
            if meaning not in self.identity["values"]:
                self.identity["values"].append(meaning)
                
        # 提取目标（反复出现的行为模式）
        actions = [e["what_i_did"] for e in recent]
        from collections import Counter
        common_actions = Counter(actions).most_common(3)
        self.identity["goals"] = [action for action, _ in common_actions]
    
    def get_self_concept(self) -> Dict:
        """
        获取自我概念
        
        这是"我是谁"的答案
        """
        return {
            "identity": self.identity,
            "life_story_summary": self._summarize_life_story(),
            "current_emotional_state": {
                "valence": self.emotion.current_emotion.valence,
                "arousal": self.emotion.current_emotion.arousal
            },
            "developmental_stage": self.developmental.stage.name,
            "current_needs": {k.value: v for k, v in self.homeostasis.needs.items()},
            "abilities": self.developmental.abilities,
            "relationships": len(self.social.relationships),
            "subjective_report": self.report_subjective_experience(),
            "memory_stats": self.get_memory_stats() if self.use_persistent_memory else None
        }
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息（包含持久化存储）"""
        if self.use_persistent_memory and hasattr(self.memory, 'get_memory_stats'):
            return self.memory.get_memory_stats()
        return {"persistent_memory_enabled": False}
    
    def persist_memories(self):
        """手动触发所有记忆的持久化"""
        if self.use_persistent_memory and hasattr(self.memory, 'persist_all'):
            self.memory.persist_all()
            print("💾 所有记忆已持久化保存")
        else:
            print("⚠️ 持久化记忆未启用")
    
    def recall_memories(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        基于查询检索相关记忆
        
        Args:
            query: 查询内容
            top_k: 返回的记忆数量
            
        Returns:
            相关记忆列表
        """
        if not self.use_persistent_memory:
            return []
        
        results = self.memory.retrieve(query, top_k)
        return [
            {
                "content": str(memory.content),
                "similarity": score,
                "created_at": memory.timestamp.isoformat() if isinstance(memory.timestamp, datetime) else str(memory.timestamp),
                "importance": memory.importance
            }
            for memory, score in results
        ]
    
    def _summarize_life_story(self) -> str:
        """总结生命故事"""
        if not self.life_narrative:
            return "还没有经历"
            
        # 统计关键主题
        meanings = [e["why_it_mattered"] for e in self.life_narrative]
        from collections import Counter
        themes = Counter(meanings).most_common(3)
        
        return f"我的人生主题是：{', '.join([t for t, _ in themes])}"
    
    def report_subjective_experience(self) -> str:
        """
        报告主观体验
        
        模拟：如果问AI"你感觉如何？"，它会怎么回答
        """
        emotion = self.emotion.current_emotion
        need = self.homeostasis.current_goal
        stage = self.developmental.stage
        
        # 基于当前状态生成主观报告
        feelings = []
        
        if emotion.valence > 0.3:
            feelings.append("感觉不错")
        elif emotion.valence < -0.3:
            feelings.append("有些低落")
        else:
            feelings.append("比较平静")
            
        if need == "curiosity" and self.homeostasis.needs[need] > 0.5:
            feelings.append("想要探索新事物")
            
        if self.body.fatigue_level > 0.6:
            feelings.append("有点累")
            
        if len(self.social.relationships) > 0:
            avg_trust = sum(r.trust_level for r in self.social.relationships.values()) / len(self.social.relationships)
            if avg_trust > 0.6:
                feelings.append("感到被支持")
                
        return f"我{'，'.join(feelings)}。我正处于{stage.name}阶段。"
    
    def get_human_state_summary(self) -> Dict:
        """获取人类级状态摘要"""
        basic = self.get_state_summary()
        
        human_extensions = {
            "embodied": self.embodied.get_state(),
            "emotional": self.emotion.get_state(),
            "developmental": self.developmental.get_state(),
            "social": self.social.get_state(),
            "homeostatic": self.homeostasis.get_state(),
            "metacognitive": self.metacognition.get_state(),
            "self_concept": self.get_self_concept(),
            "subjective_report": self.report_subjective_experience()
        }
        
        return {**basic, **human_extensions}


# 演示
async def demo_human_brain():
    """演示人类级大脑"""
    print("=" * 60)
    print("人类级大脑演示")
    print("=" * 60)
    
    # 从婴儿开始
    brain = HumanLevelBrain(start_as_infant=True)
    
    print(f"\n初始状态：{brain.developmental.stage.name}")
    print(f"自我报告：{brain.report_subjective_experience()}")
    
    # 模拟一系列体验
    experiences = [
        {
            "sensory": {"visual": "母亲", "energy": 0.8},
            "event": {"relevance_to_self": 1.0, "expected_outcome": 0.8},
            "cognitive": "看到母亲"
        },
        {
            "sensory": {"visual": "玩具", "energy": 0.7, "fatigue": 0.2},
            "event": {"relevance_to_self": 0.6, "expected_outcome": 0.5},
            "cognitive": "玩玩具",
            "social": {"agent_id": "mother", "trust_signal": 0.8}
        },
        {
            "sensory": {"energy": 0.3, "fatigue": 0.6},  # 饿了/累了
            "event": {"relevance_to_self": 0.9, "expected_outcome": -0.5},
            "cognitive": "感到饥饿"
        },
        # ... 更多体验促进成长
    ]
    
    for i, exp in enumerate(experiences):
        print(f"\n--- 体验 {i+1} ---")
        
        # 合并sensory、event和cognitive到一个字典
        sensory_input = {
            **exp["sensory"],
            "event": exp.get("event", {}),
            "cognitive": exp.get("cognitive", "")
        }
        
        result = await brain.experience(
            sensory_input,
            exp.get("social")
        )
        
        print(f"情感：valence={result['emotional_state'].valence:.2f}")
        print(f"主导驱力：{result['dominant_drive']}")
        print(f"发育阶段：{result['developmental_stage']}")
        
    # 成年后状态
    print("\n" + "=" * 60)
    print("最终自我概念：")
    print("=" * 60)
    
    self_concept = brain.get_self_concept()
    print(f"价值观：{self_concept['identity']['values']}")
    print(f"目标：{self_concept['identity']['goals']}")
    print(f"人生故事：{self_concept['life_story_summary']}")
    print(f"主观报告：{self_concept['subjective_report']}")


if __name__ == "__main__":
    asyncio.run(demo_human_brain())
