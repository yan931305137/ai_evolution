"""
User Profiling & Social Modeling System - 用户画像与社交关系建模

增强Brain的社会认知能力，实现：
1. 用户画像构建与更新
2. 社交关系建模与管理
3. 情感纽带追踪
4. 群体动力学分析
"""
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import re


class RelationshipType(Enum):
    """关系类型"""
    STRANGER = "stranger"          # 陌生人
    ACQUAINTANCE = "acquaintance"  # 熟人
    FRIEND = "friend"              # 朋友
    CLOSE_FRIEND = "close_friend"  # 密友
    FAMILY = "family"              # 家人
    COLLEAGUE = "colleague"        # 同事
    MENTOR = "mentor"              # 导师
    MENTEE = "mentee"              # 学生
    ADVERSARY = "adversary"        # 对手（负面）


class InteractionType(Enum):
    """交互类型"""
    CONVERSATION = "conversation"  # 对话
    COLLABORATION = "collaboration" # 协作
    CONFLICT = "conflict"          # 冲突
    SUPPORT = "support"            # 支持
    LEARNING = "learning"          # 学习
    TEACHING = "teaching"          # 教学
    CASUAL = "casual"              # 随意交流
    FORMAL = "formal"              # 正式交流


@dataclass
class PersonalityTrait:
    """人格特质（大五人格模型）"""
    openness: float = 0.5           # 开放性
    conscientiousness: float = 0.5  # 尽责性
    extraversion: float = 0.5       # 外向性
    agreeableness: float = 0.5      # 宜人性
    neuroticism: float = 0.5        # 神经质
    
    def to_dict(self) -> Dict:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism
        }


@dataclass
class Interest:
    """兴趣点"""
    topic: str                      # 主题
    level: float = 0.5              # 兴趣程度 0-1
    discovered_at: datetime = field(default_factory=datetime.now)
    last_mentioned: Optional[datetime] = None
    mention_count: int = 0          # 提及次数


@dataclass
class CommunicationPattern:
    """沟通模式"""
    preferred_style: str = "balanced"  # formal/casual/balanced
    response_time_avg: float = 0.0     # 平均响应时间（秒）
    message_length_avg: float = 0.0    # 平均消息长度
    emoji_usage: float = 0.0           # emoji使用频率
    question_frequency: float = 0.0    # 提问频率
    active_hours: List[int] = field(default_factory=list)  # 活跃时段


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    
    # 人格特质
    personality: PersonalityTrait = field(default_factory=PersonalityTrait)
    
    # 兴趣和偏好
    interests: List[Interest] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # 沟通模式
    communication: CommunicationPattern = field(default_factory=CommunicationPattern)
    
    # 行为标签
    tags: Set[str] = field(default_factory=set)
    
    # 情感历史
    emotional_history: List[Dict] = field(default_factory=list)
    
    # 记忆片段
    shared_memories: List[Dict] = field(default_factory=list)
    
    def update_interaction(self, interaction_data: Dict):
        """更新交互信息"""
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        
        # 更新沟通模式
        if "response_time" in interaction_data:
            self._update_response_time(interaction_data["response_time"])
        
        if "message_length" in interaction_data:
            self._update_message_length(interaction_data["message_length"])
    
    def _update_response_time(self, response_time: float):
        """更新平均响应时间"""
        n = self.interaction_count
        old_avg = self.communication.response_time_avg
        self.communication.response_time_avg = (old_avg * (n - 1) + response_time) / n
    
    def _update_message_length(self, length: int):
        """更新平均消息长度"""
        n = self.interaction_count
        old_avg = self.communication.message_length_avg
        self.communication.message_length_avg = (old_avg * (n - 1) + length) / n
    
    def add_interest(self, topic: str, level: float = 0.5):
        """添加兴趣"""
        existing = next((i for i in self.interests if i.topic == topic), None)
        if existing:
            existing.level = min(1.0, existing.level + 0.1)
            existing.mention_count += 1
            existing.last_mentioned = datetime.now()
        else:
            self.interests.append(Interest(
                topic=topic,
                level=level,
                mention_count=1,
                last_mentioned=datetime.now()
            ))
    
    def get_top_interests(self, n: int = 5) -> List[Interest]:
        """获取主要兴趣"""
        sorted_interests = sorted(
            self.interests,
            key=lambda x: (x.level, x.mention_count),
            reverse=True
        )
        return sorted_interests[:n]
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "interaction_count": self.interaction_count,
            "personality": self.personality.to_dict(),
            "interests": [
                {
                    "topic": i.topic,
                    "level": i.level,
                    "mention_count": i.mention_count
                }
                for i in self.interests
            ],
            "preferences": self.preferences,
            "communication": {
                "preferred_style": self.communication.preferred_style,
                "response_time_avg": self.communication.response_time_avg,
                "message_length_avg": self.communication.message_length_avg,
                "emoji_usage": self.communication.emoji_usage
            },
            "tags": list(self.tags)
        }


@dataclass
class Relationship:
    """社交关系"""
    user_id: str
    relationship_type: RelationshipType = RelationshipType.STRANGER
    trust_level: float = 0.0            # 信任度 0-1
    intimacy_level: float = 0.0         # 亲密度 0-1
    reciprocity_score: float = 0.0      # 互惠度（平衡性）
    
    # 交互统计
    positive_interactions: int = 0
    negative_interactions: int = 0
    total_interactions: int = 0
    
    # 关系历史
    relationship_history: List[Dict] = field(default_factory=list)
    
    # 共享经历
    shared_experiences: List[Dict] = field(default_factory=list)
    
    # 情感纽带
    emotional_bonds: Dict[str, float] = field(default_factory=dict)  # 情感类型 -> 强度
    
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_after_interaction(
        self,
        interaction_type: InteractionType,
        emotional_impact: float,
        satisfaction: float
    ):
        """交互后更新关系"""
        self.total_interactions += 1
        
        if emotional_impact > 0:
            self.positive_interactions += 1
        elif emotional_impact < 0:
            self.negative_interactions += 1
        
        # 更新信任度
        trust_change = satisfaction * 0.1 if satisfaction > 0 else satisfaction * 0.2
        self.trust_level = max(0.0, min(1.0, self.trust_level + trust_change))
        
        # 更新亲密度
        if interaction_type in [InteractionType.SUPPORT, InteractionType.COLLABORATION]:
            self.intimacy_level = min(1.0, self.intimacy_level + 0.05)
        
        # 更新关系类型
        self._update_relationship_type()
        
        self.last_updated = datetime.now()
        
        # 记录历史
        self.relationship_history.append({
            "interaction_type": interaction_type.value,
            "emotional_impact": emotional_impact,
            "satisfaction": satisfaction,
            "timestamp": datetime.now().isoformat()
        })
    
    def _update_relationship_type(self):
        """根据指标更新关系类型"""
        if self.trust_level > 0.8 and self.intimacy_level > 0.8:
            self.relationship_type = RelationshipType.CLOSE_FRIEND
        elif self.trust_level > 0.6 and self.intimacy_level > 0.5:
            self.relationship_type = RelationshipType.FRIEND
        elif self.trust_level > 0.3 and self.total_interactions > 5:
            self.relationship_type = RelationshipType.ACQUAINTANCE
        elif self.negative_interactions > self.positive_interactions * 2:
            self.relationship_type = RelationshipType.ADVERSARY
    
    def add_emotional_bond(self, bond_type: str, strength: float):
        """添加情感纽带"""
        current = self.emotional_bonds.get(bond_type, 0.0)
        self.emotional_bonds[bond_type] = min(1.0, current + strength)
    
    def get_relationship_quality(self) -> float:
        """获取关系质量分数"""
        if self.total_interactions == 0:
            return 0.0
        
        positive_ratio = self.positive_interactions / self.total_interactions
        return (positive_ratio * 0.4 + 
                self.trust_level * 0.3 + 
                self.intimacy_level * 0.3)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "relationship_type": self.relationship_type.value,
            "trust_level": self.trust_level,
            "intimacy_level": self.intimacy_level,
            "reciprocity_score": self.reciprocity_score,
            "total_interactions": self.total_interactions,
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "emotional_bonds": self.emotional_bonds,
            "relationship_quality": self.get_relationship_quality(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


class UserProfileManager:
    """
    用户画像管理器
    
    管理所有用户的画像和社交关系
    """
    
    def __init__(self, brain_reference=None):
        self.brain = brain_reference
        self.profiles: Dict[str, UserProfile] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # 群体分析
        self.user_groups: Dict[str, List[str]] = defaultdict(list)  # 标签 -> 用户列表
        
        # 交互日志
        self.interaction_log: List[Dict] = []
    
    def get_or_create_profile(self, user_id: str, name: Optional[str] = None) -> UserProfile:
        """获取或创建用户画像"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(
                user_id=user_id,
                name=name
            )
        return self.profiles[user_id]
    
    def get_or_create_relationship(self, user_id: str) -> Relationship:
        """获取或创建关系"""
        if user_id not in self.relationships:
            self.relationships[user_id] = Relationship(user_id=user_id)
        return self.relationships[user_id]
    
    def record_interaction(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        emotional_context: Optional[Dict] = None
    ):
        """
        记录交互并更新画像
        
        Args:
            user_id: 用户ID
            user_message: 用户消息
            ai_response: AI回复
            emotional_context: 情感上下文
        """
        # 获取用户画像和关系
        profile = self.get_or_create_profile(user_id)
        relationship = self.get_or_create_relationship(user_id)
        
        # 更新基本信息
        profile.update_interaction({
            "message_length": len(user_message),
            "response_time": emotional_context.get("response_time", 0) if emotional_context else 0
        })
        
        # 分析用户消息提取信息
        self._analyze_message(profile, user_message)
        
        # 更新关系
        emotional_impact = emotional_context.get("emotional_impact", 0) if emotional_context else 0
        satisfaction = emotional_context.get("satisfaction", 0.5) if emotional_context else 0.5
        
        relationship.update_after_interaction(
            interaction_type=InteractionType.CONVERSATION,
            emotional_impact=emotional_impact,
            satisfaction=satisfaction
        )
        
        # 记录交互日志
        self.interaction_log.append({
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message_preview": user_message[:100],
            "emotional_context": emotional_context
        })
    
    def _analyze_message(self, profile: UserProfile, message: str):
        """分析用户消息提取信息"""
        # 提取兴趣（简单实现）
        interest_keywords = {
            "编程": ["代码", "程序", "开发", "bug", "python", "java", "javascript"],
            "阅读": ["书", "阅读", "小说", "作者", "文学"],
            "音乐": ["音乐", "歌曲", "歌手", "专辑", "听歌"],
            "运动": ["跑步", "健身", "运动", "篮球", "足球", "游泳"],
            "游戏": ["游戏", "玩", "通关", "游戏机制", "电竞"],
            "旅行": ["旅行", "旅游", "景点", "酒店", "机票"],
            "美食": ["吃", "美食", "餐厅", "做饭", "菜"],
            "科技": ["科技", "AI", "人工智能", "技术", "产品"]
        }
        
        message_lower = message.lower()
        for interest, keywords in interest_keywords.items():
            if any(kw in message_lower for kw in keywords):
                profile.add_interest(interest, level=0.3)
        
        # 检测沟通风格
        if "?" in message or "？" in message:
            profile.communication.question_frequency += 1
        
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]', message))
        if emoji_count > 0:
            profile.communication.emoji_usage = min(1.0, profile.communication.emoji_usage + 0.05)
        
        # 添加标签
        if len(message) > 200:
            profile.tags.add("verbose")
        if "?" in message:
            profile.tags.add("inquisitive")
        if any(kw in message_lower for kw in ["谢谢", "感谢", "thx"]):
            profile.tags.add("polite")
    
    def get_user_summary(self, user_id: str) -> Optional[Dict]:
        """获取用户摘要"""
        profile = self.profiles.get(user_id)
        relationship = self.relationships.get(user_id)
        
        if not profile:
            return None
        
        return {
            "profile": profile.to_dict(),
            "relationship": relationship.to_dict() if relationship else None,
            "known_since": profile.created_at.isoformat(),
            "relationship_quality": relationship.get_relationship_quality() if relationship else 0.0
        }
    
    def get_closest_users(self, n: int = 5) -> List[Tuple[str, float]]:
        """获取关系最密切的用户"""
        scored_users = [
            (user_id, rel.get_relationship_quality())
            for user_id, rel in self.relationships.items()
        ]
        scored_users.sort(key=lambda x: x[1], reverse=True)
        return scored_users[:n]
    
    def get_users_by_interest(self, interest: str) -> List[str]:
        """获取有特定兴趣的用户"""
        matching_users = []
        for user_id, profile in self.profiles.items():
            if any(i.topic == interest for i in profile.interests):
                matching_users.append(user_id)
        return matching_users
    
    def analyze_user_groups(self) -> Dict[str, List[str]]:
        """分析用户群体"""
        groups = defaultdict(list)
        
        for user_id, profile in self.profiles.items():
            # 按主要兴趣分组
            top_interests = profile.get_top_interests(3)
            for interest in top_interests:
                if interest.level > 0.5:
                    groups[f"interest_{interest.topic}"].append(user_id)
            
            # 按沟通风格分组
            if profile.communication.emoji_usage > 0.3:
                groups["style_expressive"].append(user_id)
            elif profile.communication.question_frequency > profile.interaction_count * 0.5:
                groups["style_inquisitive"].append(user_id)
        
        return dict(groups)
    
    def generate_personalized_prompt(self, user_id: str) -> str:
        """生成个性化提示"""
        profile = self.profiles.get(user_id)
        relationship = self.relationships.get(user_id)
        
        if not profile:
            return ""
        
        parts = []
        
        # 关系信息
        if relationship:
            rel_type = relationship.relationship_type.value
            parts.append(f"用户关系: {rel_type}")
            parts.append(f"信任度: {relationship.trust_level:.1%}")
        
        # 兴趣信息
        top_interests = profile.get_top_interests(3)
        if top_interests:
            interest_str = ", ".join([i.topic for i in top_interests])
            parts.append(f"用户兴趣: {interest_str}")
        
        # 沟通风格
        style = profile.communication.preferred_style
        parts.append(f"沟通风格: {style}")
        
        return " | ".join(parts)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_users = len(self.profiles)
        total_interactions = sum(p.interaction_count for p in self.profiles.values())
        
        avg_interactions = total_interactions / total_users if total_users > 0 else 0
        
        relationship_distribution = defaultdict(int)
        for rel in self.relationships.values():
            relationship_distribution[rel.relationship_type.value] += 1
        
        return {
            "total_users": total_users,
            "total_interactions": total_interactions,
            "avg_interactions_per_user": avg_interactions,
            "relationship_distribution": dict(relationship_distribution),
            "recent_interactions": len([l for l in self.interaction_log 
                                       if datetime.fromisoformat(l["timestamp"]) > datetime.now() - timedelta(days=7)])
        }
    
    def export_data(self) -> Dict:
        """导出所有数据"""
        return {
            "profiles": {uid: p.to_dict() for uid, p in self.profiles.items()},
            "relationships": {uid: r.to_dict() for uid, r in self.relationships.items()},
            "statistics": self.get_statistics(),
            "export_time": datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict):
        """导入数据"""
        # 简化实现，实际应该做更完整的数据验证和恢复
        for uid, profile_data in data.get("profiles", {}).items():
            profile = UserProfile(user_id=uid)
            # 恢复数据...
            self.profiles[uid] = profile


# 便捷函数
def create_user_profile_manager(brain=None) -> UserProfileManager:
    """创建用户画像管理器"""
    return UserProfileManager(brain_reference=brain)
