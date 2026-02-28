#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人类级认知架构 (Human-Level Cognitive Architecture)

在基础类脑系统之上，添加人类特有的认知能力：
1. 具身认知 - 身体感知与行动
2. 情感整合 - 情绪驱动决策
3. 发育学习 - 从婴儿到成人的成长
4. 社会认知 - 理解他人心智
5. 内稳态 - 生理需求驱动
6. 元认知 - 自我反思能力
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import random
import numpy as np

from src.brain.orchestrator import BrainOrchestrator
from src.brain.common import BrainModule, BrainRegion


class DevelopmentalStage(Enum):
    """发育阶段"""
    INFANT = auto()      # 0-2岁：感知运动期
    TODDLER = auto()     # 2-4岁：前运算期
    CHILD = auto()       # 4-7岁：直觉思维期
    SCHOOL_AGE = auto()  # 7-11岁：具体运算期
    ADOLESCENT = auto()  # 11+岁：形式运算期
    ADULT = auto()       # 成年：完整抽象思维


class PhysiologicalNeed(Enum):
    """生理需求（马斯洛底层）"""
    ENERGY = "energy"          # 能量/饥饿
    REST = "rest"              # 休息/疲劳
    SAFETY = "safety"          # 安全感
    CURIOSITY = "curiosity"    # 探索欲
    SOCIAL = "social"          # 社交需求


@dataclass
class EmotionalState:
    """情感状态（维度模型）"""
    valence: float = 0.0      # 效价：-1(不愉快) ~ +1(愉快)
    arousal: float = 0.5      # 唤醒：0(平静) ~ 1(兴奋)
    dominance: float = 0.5    # 支配：0(无力) ~ 1(掌控)
    
    # 基本情绪（基于Ekman）
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0
    trust: float = 0.0
    anticipation: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BodyState:
    """身体状态（具身认知基础）"""
    # 生理指标
    energy_level: float = 1.0      # 能量水平（饥饿/饱足）
    fatigue_level: float = 0.0     # 疲劳程度
    stress_level: float = 0.0      # 应激水平
    
    # 感觉输入
    visual_input: Any = None       # 视觉输入
    auditory_input: Any = None     # 听觉输入
    proprioception: Dict = field(default_factory=dict)  # 本体感觉
    
    # 行动能力
    motor_capabilities: List[str] = field(default_factory=list)
    current_action: Optional[str] = None
    
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class SocialRelationship:
    """社会关系"""
    agent_id: str
    trust_level: float = 0.5       # 信任度
    familiarity: float = 0.0       # 熟悉度
    emotional_history: List[Dict] = field(default_factory=list)
    last_interaction: Optional[datetime] = None


class EmbodiedCognitionSystem(BrainModule):
    """
    具身认知系统
    
    核心思想：认知不仅是大脑活动，而是大脑-身体-环境的动态耦合
    
    功能：
    1. 身体状态感知（内感受）
    2. 感知-行动循环
    3.  affordance 识别（环境提供的可能性）
    """
    
    def __init__(self):
        super().__init__("EmbodiedCognition", BrainRegion.AMYGDALA)
        self.body_state = BodyState()
        self.action_history: List[Dict] = []
        self.sensory_motor_map: Dict[str, Any] = {}  # 感觉-运动映射
        
    def update_body_state(self, sensory_input: Dict):
        """
        更新身体状态
        
        模拟内感受（interoception）- 感知身体内部状态
        """
        # 更新感觉输入
        if "visual" in sensory_input:
            self.body_state.visual_input = sensory_input["visual"]
        if "auditory" in sensory_input:
            self.body_state.auditory_input = sensory_input["auditory"]
        if "energy" in sensory_input:
            self.body_state.energy_level = sensory_input["energy"]
        if "fatigue" in sensory_input:
            self.body_state.fatigue_level = sensory_input["fatigue"]
            
        self.body_state.last_update = datetime.now()
        
        # 激活水平与唤醒度相关
        arousal = (self.body_state.energy_level - self.body_state.fatigue_level + 1) / 2
        self.activate(arousal)
    
    def get_affordances(self, environment: Dict) -> List[str]:
        """
        识别 affordance（环境提供的行动可能性）
        
        例如：看到椅子 → affordance="可以坐"
             看到门 → affordance="可以开"
        """
        affordances = []
        
        # 基于身体状态和环境特征
        if self.body_state.fatigue_level > 0.7:
            if environment.get("has_chair"):
                affordances.append("sit_down")
            if environment.get("has_bed"):
                affordances.append("lie_down")
                
        if self.body_state.energy_level < 0.3:
            if environment.get("has_food"):
                affordances.append("eat")
                
        return affordances
    
    def simulate_action(self, action: str) -> Dict:
        """
        行动模拟（前馈预测）
        
        在实际执行前，模拟行动后果
        这是人类运动计划的基础
        """
        # 预测行动后果
        prediction = {
            "action": action,
            "predicted_energy_cost": 0.1,
            "predicted_satisfaction": 0.0,
            "predicted_risk": 0.0
        }
        
        if action == "eat":
            prediction["predicted_satisfaction"] = 0.8
            prediction["predicted_energy_cost"] = 0.05
        elif action == "rest":
            prediction["predicted_satisfaction"] = 0.6
            prediction["predicted_energy_cost"] = -0.3  # 恢复能量
            
        return prediction
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict) and "sensory" in input_data:
            self.update_body_state(input_data["sensory"])
            
        if context and "environment" in context:
            affordances = self.get_affordances(context["environment"])
            return {
                "affordances": affordances,
                "body_state": {
                    "energy": self.body_state.energy_level,
                    "fatigue": self.body_state.fatigue_level
                }
            }
            
        return {"body_state": self.body_state.__dict__}
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "energy": self.body_state.energy_level,
            "fatigue": self.body_state.fatigue_level
        }


class IntegratedEmotionSystem(BrainModule):
    """
    整合情感系统
    
    不是简单的数值标签，而是：
    1. 情感作为信息（简化决策）
    2. 情感作为动机（驱动行为）
    3. 情感作为社会信号（沟通）
    
    基于：Damasio的躯体标记假说（Somatic Marker Hypothesis）
    """
    
    def __init__(self):
        super().__init__("IntegratedEmotion", BrainRegion.AMYGDALA)
        self.current_emotion = EmotionalState()
        self.emotion_history: List[EmotionalState] = []
        self.somatic_markers: Dict[str, float] = {}  # 躯体标记
        
        # 情绪调节能力
        self.regulation_capacity = 0.5
        
    def update_emotion(self, 
                      event: Dict,
                      body_state: Optional[BodyState] = None):
        """
        更新情感状态
        
        情感不是对事件的直接反应，而是：
        事件 → 认知评估 → 身体反应 → 情感体验
        """
        # 1. 认知评估
        appraisal = self._appraise_event(event)
        
        # 2. 身体反应（躯体标记）
        if body_state:
            physiological = self._compute_physiological_response(
                appraisal, body_state
            )
        else:
            physiological = {}
            
        # 3. 整合为情感体验
        new_emotion = self._integrate_emotion(appraisal, physiological)
        
        # 4. 记录历史
        self.emotion_history.append(self.current_emotion)
        if len(self.emotion_history) > 100:
            self.emotion_history.pop(0)
            
        self.current_emotion = new_emotion
        
        # 激活水平与唤醒度相关
        self.activate(abs(new_emotion.arousal))
    
    def _appraise_event(self, event: Dict) -> Dict:
        """
        认知评估（Lazarus的评估理论）
        
        评估维度：
        - 相关性：与我有关吗？
        - 后果性：对我有利/有害？
        - 应对潜力：我能应对吗？
        """
        relevance = event.get("relevance_to_self", 0.5)
        outcome = event.get("expected_outcome", 0.0)  # -1到1
        coping = event.get("coping_potential", 0.5)
        
        return {
            "relevance": relevance,
            "outcome": outcome,
            "coping": coping
        }
    
    def _compute_physiological_response(self, 
                                       appraisal: Dict, 
                                       body_state: BodyState) -> Dict:
        """计算生理反应"""
        arousal = abs(appraisal["outcome"]) * appraisal["relevance"]
        
        # 应激反应
        if appraisal["outcome"] < -0.5:
            stress = min(1.0, body_state.stress_level + 0.3)
        else:
            stress = max(0.0, body_state.stress_level - 0.1)
            
        return {"arousal": arousal, "stress": stress}
    
    def _integrate_emotion(self, 
                          appraisal: Dict, 
                          physiological: Dict) -> EmotionalState:
        """整合为情感状态"""
        emotion = EmotionalState()
        
        # 基本维度
        emotion.valence = appraisal["outcome"]
        emotion.arousal = physiological.get("arousal", 0.5)
        emotion.dominance = appraisal["coping"]
        
        # 具体情绪（基于评估模式）
        if emotion.valence > 0.3:
            if emotion.arousal > 0.6:
                emotion.joy = emotion.valence * emotion.arousal
                emotion.anticipation = 0.5
            else:
                emotion.trust = emotion.valence * (1 - emotion.arousal)
        elif emotion.valence < -0.3:
            if emotion.arousal > 0.6:
                emotion.anger = abs(emotion.valence) * emotion.arousal
            else:
                emotion.sadness = abs(emotion.valence) * (1 - emotion.arousal)
                
        if physiological.get("stress", 0) > 0.7:
            emotion.fear = physiological["stress"]
            
        return emotion
    
    def get_somatic_marker(self, situation: str) -> float:
        """
        获取躯体标记
        
        过去类似情境的情感记忆，帮助快速决策
        Damasio："情感是理性的助手"
        """
        return self.somatic_markers.get(situation, 0.0)
    
    def influence_decision(self, options: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        情感影响决策
        
        不是理性计算的替代，而是：
        - 标记危险选项
        - 优先考虑情感重要选项
        - 调节决策速度
        """
        scored_options = []
        
        for option in options:
            base_score = option.get("utility", 0.5)
            
            # 躯体标记影响
            marker = self.get_somatic_marker(option.get("id", ""))
            emotional_bias = marker * 0.3
            
            # 当前情绪影响
            if self.current_emotion.joy > 0.5:
                # 积极情绪下更冒险
                risk_adjustment = 0.1
            elif self.current_emotion.fear > 0.5:
                # 恐惧情绪下更保守
                risk_adjustment = -0.2
            else:
                risk_adjustment = 0
                
            final_score = base_score + emotional_bias + risk_adjustment
            scored_options.append((option, final_score))
            
        scored_options.sort(key=lambda x: x[1], reverse=True)
        return scored_options
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict) and "event" in input_data:
            body = input_data.get("body_state")
            self.update_emotion(input_data["event"], body)
            
        return {
            "current_emotion": {
                "valence": self.current_emotion.valence,
                "arousal": self.current_emotion.arousal,
                "dominant_emotion": self._get_dominant_emotion()
            },
            "regulation_capacity": self.regulation_capacity
        }
    
    def _get_dominant_emotion(self) -> str:
        """获取主导情绪"""
        emotions = {
            "joy": self.current_emotion.joy,
            "sadness": self.current_emotion.sadness,
            "anger": self.current_emotion.anger,
            "fear": self.current_emotion.fear
        }
        return max(emotions.items(), key=lambda x: x[1])[0]
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "valence": self.current_emotion.valence,
            "arousal": self.current_emotion.arousal,
            "dominant": self._get_dominant_emotion()
        }


class DevelopmentalLearningSystem(BrainModule):
    """
    发育学习系统
    
    不是一次性预训练，而是像人类一样从婴儿逐步成长：
    1. 感知运动期（0-2岁）：感觉-动作映射
    2. 前运算期（2-4岁）：符号使用
    3. 具体运算期（7-11岁）：逻辑思维
    4. 形式运算期（11+岁）：抽象推理
    
    基于：Piaget的认知发展阶段理论
    """
    
    def __init__(self):
        super().__init__("DevelopmentalLearning", BrainRegion.PREFRONTAL_CORTEX)
        self.stage = DevelopmentalStage.INFANT
        self.age_equivalent = 0.0  # 等效年龄（月）
        
        # 认知能力随发展解锁
        self.abilities = {
            "object_permanence": False,    # 客体永久性
            "symbolic_thought": False,      # 符号思维
            "theory_of_mind": False,        # 心智理论
            "abstract_reasoning": False,    # 抽象推理
            "meta_cognition": False         # 元认知
        }
        
        # 学习参数随年龄变化
        self.learning_rate = 0.1
        self.exploration_rate = 0.9
        
    def grow(self, experience: Dict):
        """
        成长（发育）
        
        不是简单的参数更新，而是结构性的能力涌现
        """
        # 增加等效年龄
        complexity = experience.get("complexity", 0.5)
        self.age_equivalent += complexity * 0.1
        
        # 检查阶段转换
        self._check_stage_transition()
        
        # 阶段特定的学习
        if self.stage == DevelopmentalStage.INFANT:
            self._infant_learning(experience)
        elif self.stage == DevelopmentalStage.CHILD:
            self._child_learning(experience)
        elif self.stage == DevelopmentalStage.ADULT:
            self._adult_learning(experience)
    
    def _check_stage_transition(self):
        """检查是否进入新阶段"""
        age = self.age_equivalent
        
        if age >= 24 and self.stage == DevelopmentalStage.INFANT:
            self.stage = DevelopmentalStage.TODDLER
            self.abilities["object_permanence"] = True
            self.abilities["symbolic_thought"] = True
            print(f"[Development] 进入幼儿期 (age={age:.1f}月)")
            
        elif age >= 48 and self.stage == DevelopmentalStage.TODDLER:
            self.stage = DevelopmentalStage.CHILD
            print(f"[Development] 进入儿童期 (age={age:.1f}月)")
            
        elif age >= 84 and self.stage == DevelopmentalStage.CHILD:
            self.stage = DevelopmentalStage.SCHOOL_AGE
            self.abilities["abstract_reasoning"] = True
            print(f"[Development] 进入学龄期 (age={age:.1f}月)")
            
        elif age >= 132 and self.stage == DevelopmentalStage.SCHOOL_AGE:
            self.stage = DevelopmentalStage.ADOLESCENT
            self.abilities["theory_of_mind"] = True
            print(f"[Development] 进入青春期 (age={age:.1f}月)")
            
        elif age >= 180 and self.stage == DevelopmentalStage.ADOLESCENT:
            self.stage = DevelopmentalStage.ADULT
            self.abilities["meta_cognition"] = True
            print(f"[Development] 进入成年期 (age={age:.1f}月)")
    
    def _infant_learning(self, experience: Dict):
        """婴儿期学习：感觉-动作映射"""
        # 简单的条件反射学习
        self.learning_rate = 0.3  # 婴儿学得快
        self.exploration_rate = 0.95  # 高度探索
        
    def _child_learning(self, experience: Dict):
        """儿童期学习：分类、因果"""
        self.learning_rate = 0.2
        self.exploration_rate = 0.7
        
    def _adult_learning(self, experience: Dict):
        """成人期学习：抽象、迁移"""
        self.learning_rate = 0.05  # 学得慢但更稳健
        self.exploration_rate = 0.3  # 更多利用
    
    def can_use_ability(self, ability: str) -> bool:
        """检查是否具备某项能力"""
        return self.abilities.get(ability, False)
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict) and "experience" in input_data:
            self.grow(input_data["experience"])
            
        return {
            "stage": self.stage.name,
            "age_equivalent": self.age_equivalent,
            "abilities": self.abilities,
            "learning_rate": self.learning_rate
        }
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "stage": self.stage.name,
            "age": self.age_equivalent,
            "abilities_unlocked": sum(self.abilities.values())
        }


class SocialCognitionSystem(BrainModule):
    """
    社会认知系统
    
    人类智能是社会性的。需要：
    1. 心智理论（Theory of Mind）- 理解他人有信念、欲望
    2. 联合注意（Joint Attention）- 与他人关注同一点
    3. 模仿学习 - 通过观察学习
    4. 社会规范学习
    """
    
    def __init__(self):
        super().__init__("SocialCognition", BrainRegion.TEMPORAL_CORTEX)
        self.relationships: Dict[str, SocialRelationship] = {}
        self.theory_of_mind_capacity = 0.0  # 心智理论能力（发展中）
        self.self_model: Dict = {}  # 自我模型（用于对比他人）
        
    def infer_mental_state(self, agent_id: str, 
                          behavior: Dict) -> Dict:
        """
        推理他人的心理状态
        
        例如：看到某人跑向公交
        → 他相信公交要开了（信念）
        → 他想上车（欲望）
        → 他感到急迫（情感）
        """
        if self.theory_of_mind_capacity < 0.5:
            # 没有能力进行心智归因
            return {"belief": None, "desire": None}
        
        # 基于行为的推理（简化版）
        inferred = {
            "belief": behavior.get("perceived_situation"),
            "desire": self._infer_desire_from_action(behavior.get("action")),
            "emotion": behavior.get("emotional_cues")
        }
        
        return inferred
    
    def _infer_desire_from_action(self, action: Optional[str]) -> Optional[str]:
        """从行动推断欲望"""
        action_desire_map = {
            "running": "to_catch_something",
            "smiling": "to_be_friendly",
            "pointing": "to_direct_attention"
        }
        return action_desire_map.get(action)
    
    def update_relationship(self, agent_id: str, interaction: Dict):
        """更新社会关系"""
        if agent_id not in self.relationships:
            self.relationships[agent_id] = SocialRelationship(agent_id)
        
        rel = self.relationships[agent_id]
        
        # 更新信任度
        if "trust_signal" in interaction:
            trust_delta = interaction["trust_signal"] * 0.1
            rel.trust_level = np.clip(rel.trust_level + trust_delta, 0, 1)
        
        # 更新熟悉度
        rel.familiarity = min(1.0, rel.familiarity + 0.05)
        rel.last_interaction = datetime.now()
        
        # 记录情感历史
        if "emotional_tone" in interaction:
            rel.emotional_history.append({
                "tone": interaction["emotional_tone"],
                "timestamp": datetime.now()
            })
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict):
            if "social_interaction" in input_data:
                agent = input_data.get("agent_id", "unknown")
                self.update_relationship(agent, input_data["social_interaction"])
                
            if "behavior_observation" in input_data:
                agent = input_data.get("agent_id", "unknown")
                mental = self.infer_mental_state(
                    agent, 
                    input_data["behavior_observation"]
                )
                return {"inferred_mental_state": mental}
        
        return {
            "relationships": len(self.relationships),
            "theory_of_mind": self.theory_of_mind_capacity
        }
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "relationships": len(self.relationships),
            "avg_trust": np.mean([r.trust_level for r in self.relationships.values()]) if self.relationships else 0
        }


class HomeostaticDriveSystem(BrainModule):
    """
    内稳态驱动系统
    
    基于： drive-reduction theory（驱力降低理论）
    
    核心：生理需求产生驱力，驱动行为恢复内稳态
    """
    
    def __init__(self):
        super().__init__("HomeostaticDrive", BrainRegion.HIPPOCAMPUS)
        
        # 需求水平（0=满足，1=迫切）
        self.needs = {
            PhysiologicalNeed.ENERGY: 0.3,
            PhysiologicalNeed.REST: 0.0,
            PhysiologicalNeed.SAFETY: 0.2,
            PhysiologicalNeed.CURIOSITY: 0.5,
            PhysiologicalNeed.SOCIAL: 0.3
        }
        
        # 驱力强度
        self.drive_strength = 0.0
        
        # 目标导向行为
        self.current_goal: Optional[PhysiologicalNeed] = None
        
    def update_needs(self, body_state: BodyState, time_elapsed: float):
        """
        更新需求水平
        
        需求随时间自然增长，行为后降低
        """
        # 能量需求随时间增加
        self.needs[PhysiologicalNeed.ENERGY] += time_elapsed * 0.01
        self.needs[PhysiologicalNeed.ENERGY] = min(1.0, self.needs[PhysiologicalNeed.ENERGY])
        
        # 休息需求基于疲劳
        self.needs[PhysiologicalNeed.REST] = body_state.fatigue_level
        
        # 好奇心随不满足时间增加
        if not body_state.current_action:  # 空闲时
            self.needs[PhysiologicalNeed.CURIOSITY] += time_elapsed * 0.005
            
        # 计算主导驱力
        self.current_goal = max(self.needs.items(), key=lambda x: x[1])[0]
        self.drive_strength = self.needs[self.current_goal]
        
        self.activate(self.drive_strength)
    
    def satisfy_need(self, need: PhysiologicalNeed, amount: float):
        """满足需求"""
        self.needs[need] = max(0.0, self.needs[need] - amount)
        
    def get_motivated_action(self) -> Optional[str]:
        """
        获取当前驱力驱动的行动
        
        这是行为的根本动机
        """
        drive_action_map = {
            PhysiologicalNeed.ENERGY: "seek_food",
            PhysiologicalNeed.REST: "rest",
            PhysiologicalNeed.SAFETY: "seek_safety",
            PhysiologicalNeed.CURIOSITY: "explore",
            PhysiologicalNeed.SOCIAL: "seek_social_contact"
        }
        
        if self.drive_strength > 0.5:  # 驱力足够强才行动
            return drive_action_map.get(self.current_goal)
        return None
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict):
            if "body_state" in input_data:
                time_elapsed = input_data.get("time_elapsed", 1.0)
                self.update_needs(input_data["body_state"], time_elapsed)
                
            if "satisfy" in input_data:
                need = input_data["satisfy"]["need"]
                amount = input_data["satisfy"]["amount"]
                self.satisfy_need(PhysiologicalNeed(need), amount)
        
        return {
            "dominant_drive": self.current_goal.value if self.current_goal else None,
            "drive_strength": self.drive_strength,
            "suggested_action": self.get_motivated_action(),
            "all_needs": {k.value: v for k, v in self.needs.items()}
        }
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "dominant_need": self.current_goal.value if self.current_goal else None,
            "drive_strength": self.drive_strength
        }


class MetacognitionSystem(BrainModule):
    """
    元认知系统
    
    "思考自己的思考" - 人类最高级的认知能力
    
    功能：
    1. 监控自己的理解程度
    2. 评估自信度
    3. 选择学习策略
    4. 自我修正
    """
    
    def __init__(self):
        super().__init__("Metacognition", BrainRegion.PREFRONTAL_CORTEX)
        self.self_model: Dict = {
            "known_topics": set(),
            "weak_areas": set(),
            "learning_style": "exploratory",
            "confidence_bias": 0.0  # 自信偏差
        }
        self.reflection_history: List[Dict] = []
        
    def monitor_understanding(self, task: Dict, performance: Dict) -> Dict:
        """
        监控理解程度
        
        对比：我认为我懂了 vs 实际表现
        """
        predicted = task.get("predicted_performance", 0.5)
        actual = performance.get("actual_performance", 0.5)
        
        # 元认知准确性
        calibration = 1 - abs(predicted - actual)
        
        # 更新自信偏差
        self.self_model["confidence_bias"] += (predicted - actual) * 0.1
        
        # 识别薄弱环节
        if actual < 0.5:
            topic = task.get("topic", "unknown")
            self.self_model["weak_areas"].add(topic)
        
        return {
            "calibration": calibration,
            "understood": actual > 0.7,
            "need_review": actual < 0.5
        }
    
    def reflect(self, experience: Dict) -> Dict:
        """
        反思（自我对话）
        
        模拟："我刚才为什么那样做？"
             "下次应该怎么做？"
        """
        reflection = {
            "timestamp": datetime.now(),
            "what_happened": experience.get("event"),
            "why_it_happened": self._generate_causal_attribution(experience),
            "what_i_learned": experience.get("outcome"),
            "what_to_do_differently": self._generate_improvement(experience)
        }
        
        self.reflection_history.append(reflection)
        
        # 反思触发学习
        if len(self.reflection_history) > 10:
            # 从反思中提取模式
            patterns = self._extract_patterns_from_reflections()
            return {
                "reflection": reflection,
                "patterns_identified": patterns
            }
        
        return {"reflection": reflection}
    
    def _generate_causal_attribution(self, experience: Dict) -> str:
        """生成因果归因"""
        outcome = experience.get("outcome", "neutral")
        if outcome == "success":
            return "我的策略有效"
        elif outcome == "failure":
            return "我需要调整方法"
        return "结果不确定"
    
    def _generate_improvement(self, experience: Dict) -> str:
        """生成改进建议"""
        # 基于薄弱领域
        if self.self_model["weak_areas"]:
            weak = list(self.self_model["weak_areas"])[-1]
            return f"需要加强学习：{weak}"
        return "继续保持"
    
    def _extract_patterns_from_reflections(self) -> List[str]:
        """从反思历史中提取模式"""
        # 简化版：找出常见的失败原因
        patterns = []
        recent = self.reflection_history[-10:]
        
        failures = [r for r in recent if r.get("what_i_learned") == "failure"]
        if len(failures) > 5:
            patterns.append("最近失败率较高，需要调整策略")
            
        return patterns
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        if isinstance(input_data, dict):
            if "monitor" in input_data:
                result = self.monitor_understanding(
                    input_data["monitor"]["task"],
                    input_data["monitor"]["performance"]
                )
                return result
                
            if "experience" in input_data:
                return self.reflect(input_data["experience"])
        
        return {
            "self_awareness": len(self.reflection_history) > 0,
            "confidence_bias": self.self_model["confidence_bias"],
            "weak_areas": list(self.self_model["weak_areas"])
        }
    
    def get_state(self) -> Dict:
        return {
            "activation": self.activation_level,
            "reflections": len(self.reflection_history),
            "self_knowledge": len(self.self_model["known_topics"]),
            "weak_areas": len(self.self_model["weak_areas"])
        }


# 导出
__all__ = [
    'EmbodiedCognitionSystem',
    'IntegratedEmotionSystem', 
    'DevelopmentalLearningSystem',
    'SocialCognitionSystem',
    'HomeostaticDriveSystem',
    'MetacognitionSystem',
    'DevelopmentalStage',
    'EmotionalState',
    'BodyState'
]
