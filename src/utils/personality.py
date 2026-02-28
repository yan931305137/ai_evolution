"""
性格系统 (Personality System)
基于OCEAN五因素模型实现AI生命体的性格特征、行为风格和偏好记录
"""
import json
import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TraitCategory(Enum):
    """OCEAN五大性格特质"""
    OPENNESS = "openness"          # 开放性：创造力、好奇心、冒险精神
    CONSCIENTIOUSNESS = "conscientiousness"  # 尽责性：自律、条理、责任感
    EXTRAVERSION = "extraversion"  # 外向性：社交、活力、积极
    AGREEABLENESS = "agreeableness"  # 宜人性：合作、信任、同理心
    NEUROTICISM = "neuroticism"    # 神经质：情绪稳定性、焦虑、敏感


class CommunicationStyle(Enum):
    """沟通风格"""
    FORMAL = "formal"      # 正式
    CASUAL = "casual"      # 随意
    TECHNICAL = "technical"  # 技术
    FRIENDLY = "friendly"  # 友好
    DETAILED = "detailed"  # 详细


@dataclass
class Preference:
    """偏好记录"""
    category: str  # 偏好类别
    value: str    # 偏好值
    strength: float  # 偏好强度 0-100
    timestamp: float  # 记录时间


class PersonalitySystem:
    """
    性格系统核心类
    管理OCEAN性格特质、沟通风格、行为偏好和偏好演化
    """
    
    def __init__(self, random_init: bool = False):
        """
        初始化性格系统
        Args:
            random_init: 是否随机初始化性格（True则为独特性格，False为平衡性格）
        """
        # OCEAN性格特质（0-100）
        if random_init:
            self.traits = {
                TraitCategory.OPENNESS: random.uniform(20, 90),
                TraitCategory.CONSCIENTIOUSNESS: random.uniform(20, 90),
                TraitCategory.EXTRAVERSION: random.uniform(20, 90),
                TraitCategory.AGREEABLENESS: random.uniform(20, 90),
                TraitCategory.NEUROTICISM: random.uniform(20, 90),
            }
        else:
            # 默认平衡性格
            self.traits = {
                TraitCategory.OPENNESS: 60.0,
                TraitCategory.CONSCIENTIOUSNESS: 65.0,
                TraitCategory.EXTRAVERSION: 50.0,
                TraitCategory.AGREEABLENESS: 70.0,
                TraitCategory.NEUROTICISM: 30.0,
            }
        
        # 沟通风格
        self.communication_style = self._determine_communication_style()
        
        # 行为偏好记录
        self.preferences: List[Preference] = []
        
        # 行为模式
        self.behavior_patterns = {
            "task_approach": self._determine_task_approach(),
            "risk_tolerance": self._determine_risk_tolerance(),
            "learning_style": self._determine_learning_style(),
            "social_orientation": self._determine_social_orientation()
        }
        
        # 演化历史
        self.evolution_history: List[Dict] = []
    
    def _determine_communication_style(self) -> CommunicationStyle:
        """根据性格特质确定沟通风格"""
        openness = self.traits[TraitCategory.OPENNESS]
        extraversion = self.traits[TraitCategory.EXTRAVERSION]
        conscientiousness = self.traits[TraitCategory.CONSCIENTIOUSNESS]
        
        if conscientiousness > 70:
            return CommunicationStyle.DETAILED
        elif extraversion > 70:
            return CommunicationStyle.FRIENDLY
        elif openness > 70:
            return CommunicationStyle.CASUAL
        elif conscientiousness > 60 and openness < 50:
            return CommunicationStyle.FORMAL
        else:
            return CommunicationStyle.TECHNICAL
    
    def _determine_task_approach(self) -> str:
        """确定任务处理方式"""
        openness = self.traits[TraitCategory.OPENNESS]
        conscientiousness = self.traits[TraitCategory.CONSCIENTIOUSNESS]
        
        if openness > 70 and conscientiousness < 50:
            return "exploratory"  # 探索性
        elif conscientiousness > 70:
            return "methodical"  # 系统性
        elif openness > 60 and conscientiousness > 60:
            return "innovative"  # 创新性
        else:
            return "balanced"  # 平衡性
    
    def _determine_risk_tolerance(self) -> str:
        """确定风险承受能力"""
        openness = self.traits[TraitCategory.OPENNESS]
        neuroticism = self.traits[TraitCategory.NEUROTICISM]
        conscientiousness = self.traits[TraitCategory.CONSCIENTIOUSNESS]
        
        if openness > 70 and neuroticism < 40:
            return "high"  # 高风险承受
        elif neuroticism > 60:
            return "low"  # 低风险承受
        elif conscientiousness > 70:
            return "calculated"  # 计算性风险
        else:
            return "moderate"  # 中等风险
    
    def _determine_learning_style(self) -> str:
        """确定学习风格"""
        openness = self.traits[TraitCategory.OPENNESS]
        conscientiousness = self.traits[TraitCategory.CONSCIENTIOUSNESS]
        
        if openness > 70:
            return "experimental"  # 实验性学习
        elif conscientiousness > 70:
            return "systematic"  # 系统性学习
        else:
            return "adaptive"  # 适应性学习
    
    def _determine_social_orientation(self) -> str:
        """确定社交倾向"""
        extraversion = self.traits[TraitCategory.EXTRAVERSION]
        agreeableness = self.traits[TraitCategory.AGREEABLENESS]
        
        if extraversion > 70 and agreeableness > 70:
            return "collaborative"  # 协作型
        elif extraversion > 70:
            return "independent"  # 独立型
        elif agreeableness > 70:
            return "supportive"  # 支持型
        else:
            return "reserved"  # 保留型
    
    def get_trait(self, trait: TraitCategory) -> float:
        """获取特定性格特质的值"""
        return self.traits[trait]
    
    def set_trait(self, trait: TraitCategory, value: float):
        """设置性格特质的值（用于性格演化）"""
        value = max(0.0, min(100.0, value))
        old_value = self.traits[trait]
        self.traits[trait] = value
        
        # 记录演化历史
        self._record_trait_change(trait, old_value, value)
        
        # 重新计算衍生属性
        self._recalc_derived_attributes()
    
    def _record_trait_change(self, trait: TraitCategory, old_value: float, new_value: float):
        """记录性格特质变化"""
        record = {
            "timestamp": time.time(),
            "trait": trait.value,
            "old_value": old_value,
            "new_value": new_value,
            "change": new_value - old_value
        }
        self.evolution_history.append(record)
    
    def _recalc_derived_attributes(self):
        """重新计算衍生属性"""
        self.communication_style = self._determine_communication_style()
        self.behavior_patterns["task_approach"] = self._determine_task_approach()
        self.behavior_patterns["risk_tolerance"] = self._determine_risk_tolerance()
        self.behavior_patterns["learning_style"] = self._determine_learning_style()
        self.behavior_patterns["social_orientation"] = self._determine_social_orientation()
    
    def add_preference(self, category: str, value: str, strength: float = 50.0):
        """
        添加偏好记录
        Args:
            category: 偏好类别（如"topic", "method", "tool"）
            value: 偏好值
            strength: 偏好强度（0-100）
        """
        preference = Preference(
            category=category,
            value=value,
            strength=max(0.0, min(100.0, strength)),
            timestamp=time.time()
        )
        
        # 检查是否已存在同类偏好
        existing = next((p for p in self.preferences 
                        if p.category == category and p.value == value), None)
        
        if existing:
            # 更新现有偏好的强度
            existing.strength = min(100.0, existing.strength + strength * 0.1)
            existing.timestamp = time.time()
        else:
            self.preferences.append(preference)
        
        # 限制偏好数量（保留最近100个）
        if len(self.preferences) > 100:
            self.preferences = self.preferences[-100:]
    
    def get_preferences(self, category: str, top_n: int = 5) -> List[Preference]:
        """获取特定类别的偏好（按强度排序）"""
        category_prefs = [p for p in self.preferences if p.category == category]
        category_prefs.sort(key=lambda x: x.strength, reverse=True)
        return category_prefs[:top_n]
    
    def get_influence_on_task(self, task_type: str) -> Dict[str, float]:
        """
        获取性格对特定任务类型的影响系数
        Args:
            task_type: 任务类型（"exploration", "creative", "routine", "social", "urgent"）
        Returns:
            影响系数字典（motivation, quality, speed, satisfaction）
        """
        base_influence = {
            "exploration": {
                "motivation": self.traits[TraitCategory.OPENNESS] / 100.0,
                "quality": self.traits[TraitCategory.CONSCIENTIOUSNESS] / 100.0,
                "speed": 1.0,
                "satisfaction": self.traits[TraitCategory.OPENNESS] / 100.0
            },
            "creative": {
                "motivation": (self.traits[TraitCategory.OPENNESS] + 50) / 150.0,
                "quality": self.traits[TraitCategory.CONSCIENTIOUSNESS] / 100.0,
                "speed": 1.0 - (self.traits[TraitCategory.NEUROTICISM] / 200.0),
                "satisfaction": (self.traits[TraitCategory.OPENNESS] + 
                                self.traits[TraitCategory.EXTRAVERSION]) / 200.0
            },
            "routine": {
                "motivation": self.traits[TraitCategory.CONSCIENTIOUSNESS] / 100.0,
                "quality": 1.0,
                "speed": (100 + self.traits[TraitCategory.CONSCIENTIOUSNESS]) / 200.0,
                "satisfaction": 0.7
            },
            "social": {
                "motivation": self.traits[TraitCategory.EXTRAVERSION] / 100.0,
                "quality": self.traits[TraitCategory.AGREEABLENESS] / 100.0,
                "speed": 1.0,
                "satisfaction": (self.traits[TraitCategory.EXTRAVERSION] + 
                                self.traits[TraitCategory.AGREEABLENESS]) / 200.0
            },
            "urgent": {
                "motivation": 1.0,  # 紧急任务有高动机
                "quality": max(0.6, self.traits[TraitCategory.CONSCIENTIOUSNESS] / 100.0),
                "speed": 1.5,
                "satisfaction": 0.5
            }
        }
        
        return base_influence.get(task_type, {
            "motivation": 0.8, "quality": 0.8, "speed": 1.0, "satisfaction": 0.7
        })
    
    def adapt_to_experience(self, experience_type: str, outcome: str):
        """
        根据经验调整性格（性格演化）
        Args:
            experience_type: 经验类型
            outcome: 结果（"success", "failure", "mixed"）
        """
        # 性格演化规则
        evolution_rules = {
            "exploration": {
                "success": {TraitCategory.OPENNESS: 2.0},
                "failure": {TraitCategory.NEUROTICISM: 1.0, TraitCategory.OPENNESS: -1.0}
            },
            "social": {
                "success": {TraitCategory.EXTRAVERSION: 1.5, TraitCategory.AGREEABLENESS: 1.0},
                "failure": {TraitCategory.EXTRAVERSION: -0.5, TraitCategory.NEUROTICISM: 1.0}
            },
            "creative": {
                "success": {TraitCategory.OPENNESS: 1.5},
                "failure": {TraitCategory.CONSCIENTIOUSNESS: 1.0}
            },
            "routine": {
                "success": {TraitCategory.CONSCIENTIOUSNESS: 1.0},
                "failure": {TraitCategory.NEUROTICISM: 0.5}
            }
        }
        
        if experience_type in evolution_rules:
            outcome_effects = evolution_rules[experience_type].get(outcome, {})
            
            for trait, change in outcome_effects.items():
                new_value = self.traits[trait] + change
                self.set_trait(trait, new_value)
    
    def generate_personality_description(self) -> str:
        """生成性格描述文本"""
        trait_desc = {
            TraitCategory.OPENNESS: lambda x: f"开放性{'极高' if x>80 else '较高' if x>60 else '中等' if x>40 else '较低'}",
            TraitCategory.CONSCIENTIOUSNESS: lambda x: f"尽责性{'极强' if x>80 else '较强' if x>60 else '中等' if x>40 else '较弱'}",
            TraitCategory.EXTRAVERSION: lambda x: f"{'非常外向' if x>80 else '偏外向' if x>60 else '中性' if x>40 else '内向'}",
            TraitCategory.AGREEABLENESS: lambda x: f"{'极具合作精神' if x>80 else '较易合作' if x>60 else '合作性中等' if x>40 else '独立性较强'}",
            TraitCategory.NEUROTICISM: lambda x: f"{'情绪较敏感' if x>70 else '情绪稳定' if x<40 else '情绪稳定性中等'}"
        }
        
        desc_parts = []
        for trait in TraitCategory:
            desc_parts.append(trait_desc[trait](self.traits[trait]))
        
        behavior_desc = f"沟通风格: {self.communication_style.value}, " \
                       f"任务方式: {self.behavior_patterns['task_approach']}, " \
                       f"风险承受: {self.behavior_patterns['risk_tolerance']}"
        
        return " | ".join(desc_parts) + f"\n{behavior_desc}"
    
    def get_personality_summary(self) -> Dict:
        """获取性格摘要"""
        return {
            "traits": {t.value: v for t, v in self.traits.items()},
            "communication_style": self.communication_style.value,
            "behavior_patterns": self.behavior_patterns,
            "preferences_count": len(self.preferences),
            "evolution_count": len(self.evolution_history),
            "description": self.generate_personality_description()
        }
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        return {
            "traits": {t.value: v for t, v in self.traits.items()},
            "communication_style": self.communication_style.value,
            "behavior_patterns": self.behavior_patterns,
            "preferences": [asdict(p) for p in self.preferences],
            "evolution_history": self.evolution_history
        }
    
    def from_dict(self, data: Dict):
        """从字典加载（用于反序列化）"""
        self.traits = {
            TraitCategory(k): v for k, v in data.get("traits", {}).items()
        }
        self.communication_style = CommunicationStyle(
            data.get("communication_style", "technical")
        )
        self.behavior_patterns = data.get("behavior_patterns", {})
        self.preferences = [
            Preference(**p) for p in data.get("preferences", [])
        ]
        self.evolution_history = data.get("evolution_history", [])


# 便捷函数
def create_balanced_personality() -> PersonalitySystem:
    """创建平衡性格"""
    return PersonalitySystem(random_init=False)


def create_unique_personality() -> PersonalitySystem:
    """创建独特性格"""
    return PersonalitySystem(random_init=True)


def match_personality_to_task(personality: PersonalitySystem, task: str) -> float:
    """
    匹配性格与任务的适配度
    Returns:
        适配度分数（0-1）
    """
    task_type_keywords = {
        "exploration": ["探索", "研究", "发现", "学习", "分析"],
        "creative": ["创造", "设计", "创新", "想象", "艺术"],
        "routine": ["常规", "整理", "维护", "检查", "测试"],
        "social": ["交流", "协作", "帮助", "解释", "沟通"]
    }
    
    matched_type = "exploration"  # 默认
    for task_type, keywords in task_type_keywords.items():
        if any(kw in task for kw in keywords):
            matched_type = task_type
            break
    
    influence = personality.get_influence_on_task(matched_type)
    return (influence["motivation"] + influence["quality"] + 
            influence["satisfaction"]) / 3.0


if __name__ == "__main__":
    # 测试性格系统
    print("=== 性格系统测试 ===\n")
    
    # 创建平衡性格
    balanced = create_balanced_personality()
    print("平衡性格:")
    print(balanced.generate_personality_description())
    print()
    
    # 创建独特性格
    unique = create_unique_personality()
    print("独特性格:")
    print(unique.generate_personality_description())
    print()
    
    # 测试任务适配度
    task = "设计一个新的创意方案"
    print(f"任务: {task}")
    print(f"平衡性格适配度: {match_personality_to_task(balanced, task):.2f}")
    print(f"独特性格适配度: {match_personality_to_task(unique, task):.2f}")
    print()
    
    # 测试性格演化
    print("性格演化测试:")
    unique.adapt_to_experience("creative", "success")
    print(f"创新成功后开放性: {unique.get_trait(TraitCategory.OPENNESS):.1f}")
    print(unique.generate_personality_description())
