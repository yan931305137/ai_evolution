"""
情感系统 (Emotion System)
实现AI生命体的6大基本情感维度、情感状态机和情感影响决策机制
"""
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class EmotionType(Enum):
    """6大基本情感类型（基于Paul Ekman的普遍情感理论）"""
    HAPPINESS = "happiness"      # 快乐/喜悦
    SADNESS = "sadness"          # 悲伤
    FEAR = "fear"                # 恐惧
    ANGER = "anger"              # 愤怒
    DISGUST = "disgust"          # 厌恶
    SURPRISE = "surprise"        # 惊讶


@dataclass
class EmotionState:
    """单个情感状态"""
    intensity: float  # 情感强度 0-100
    last_triggered: float  # 最后触发时间戳
    trigger_reason: str  # 触发原因


class EmotionSystem:
    """
    情感系统核心类
    管理6大基本情感维度、情感历史和情感驱动的决策影响
    """
    
    def __init__(self):
        # 初始化6大基本情感（默认状态：平和）
        self.emotions: Dict[EmotionType, EmotionState] = {
            EmotionType.HAPPINESS: EmotionState(30.0, time.time(), "initial"),
            EmotionType.SADNESS: EmotionState(10.0, time.time(), "initial"),
            EmotionType.FEAR: EmotionState(10.0, time.time(), "initial"),
            EmotionType.ANGER: EmotionState(5.0, time.time(), "initial"),
            EmotionType.DISGUST: EmotionState(5.0, time.time(), "initial"),
            EmotionType.SURPRISE: EmotionState(10.0, time.time(), "initial"),
        }
        
        # 情感历史（保留最近100次变化）
        self.emotion_history: List[Dict] = []
        self.max_history = 100
        
        # 情感阈值
        self.intense_threshold = 70.0  # 强烈情感阈值
        self.moderate_threshold = 50.0  # 中等情感阈值
        
        # 情感衰减率（每分钟衰减百分比）
        self.decay_rate = {
            EmotionType.HAPPINESS: 2.0,   # 快乐衰减较快
            EmotionType.SADNESS: 1.0,     # 悲伤持续较长
            EmotionType.FEAR: 3.0,        # 恐惧衰减快（除非持续触发）
            EmotionType.ANGER: 1.5,       # 愤怒较持久
            EmotionType.DISGUST: 2.5,     # 厌恶衰减中等
            EmotionType.SURPRISE: 5.0,    # 惊讶衰减最快
        }
        
        # 情感影响系数（影响决策权重）
        self.emotion_weights = {
            EmotionType.HAPPINESS: {"exploration": 1.5, "risk": 1.2, "social": 1.3},
            EmotionType.SADNESS: {"exploration": 0.7, "risk": 0.6, "social": 0.5},
            EmotionType.FEAR: {"exploration": 0.4, "risk": 0.3, "social": 0.4},
            EmotionType.ANGER: {"exploration": 0.9, "risk": 1.3, "social": 0.6},
            EmotionType.DISGUST: {"exploration": 0.6, "risk": 0.5, "social": 0.7},
            EmotionType.SURPRISE: {"exploration": 1.4, "risk": 1.1, "social": 1.2},
        }
    
    def trigger_emotion(self, emotion_type: EmotionType, intensity: float, reason: str):
        """
        触发情感
        Args:
            emotion_type: 情感类型
            intensity: 情感强度（0-100）
            reason: 触发原因
        """
        intensity = max(0.0, min(100.0, intensity))
        
        # 更新情感状态
        self.emotions[emotion_type].intensity = intensity
        self.emotions[emotion_type].last_triggered = time.time()
        self.emotions[emotion_type].trigger_reason = reason
        
        # 情感级联效应（某些情感会触发其他情感）
        self._apply_emotion_cascade(emotion_type, intensity)
        
        # 记录历史
        self._record_emotion_change(emotion_type, intensity, reason)
    
    def _apply_emotion_cascade(self, emotion_type: EmotionType, intensity: float):
        """应用情感级联效应（情感之间的相互影响）"""
        cascade_rules = {
            EmotionType.HAPPINESS: {EmotionType.SURPRISE: 0.3, EmotionType.SADNESS: -0.4},
            EmotionType.SADNESS: {EmotionType.FEAR: 0.3, EmotionType.DISGUST: 0.2},
            EmotionType.FEAR: {EmotionType.ANGER: 0.4, EmotionType.SURPRISE: 0.3},
            EmotionType.ANGER: {EmotionType.FEAR: -0.3, EmotionType.DISGUST: 0.2},
            EmotionType.DISGUST: {EmotionType.SADNESS: 0.2, EmotionType.ANGER: 0.1},
            EmotionType.SURPRISE: {EmotionType.HAPPINESS: 0.2, EmotionType.FEAR: 0.2},
        }
        
        if emotion_type in cascade_rules:
            for other_emotion, factor in cascade_rules[emotion_type].items():
                change = intensity * factor * 0.5  # 级联影响系数
                new_intensity = self.emotions[other_emotion].intensity + change
                self.emotions[other_emotion].intensity = max(0.0, min(100.0, new_intensity))
    
    def _record_emotion_change(self, emotion_type: EmotionType, intensity: float, reason: str):
        """记录情感变化历史"""
        record = {
            "timestamp": time.time(),
            "emotion": emotion_type.value,
            "intensity": intensity,
            "reason": reason,
            "dominant_emotion": self.get_dominant_emotion().value
        }
        self.emotion_history.append(record)
        
        # 限制历史长度
        if len(self.emotion_history) > self.max_history:
            self.emotion_history.pop(0)
    
    def decay_emotions(self):
        """情感自然衰减（模拟情绪恢复平静的过程）"""
        current_time = time.time()
        
        for emotion_type, state in self.emotions.items():
            # 计算时间差（分钟）
            time_diff = (current_time - state.last_triggered) / 60.0
            
            if time_diff > 0:
                # 应用衰减率
                decay = time_diff * self.decay_rate[emotion_type]
                new_intensity = state.intensity - decay
                self.emotions[emotion_type].intensity = max(0.0, min(100.0, new_intensity))
    
    def get_dominant_emotion(self) -> EmotionType:
        """获取当前主导情感"""
        return max(self.emotions.items(), key=lambda x: x[1].intensity)[0]
    
    def get_emotion_intensity(self, emotion_type: EmotionType) -> float:
        """获取特定情感的强度"""
        return self.emotions[emotion_type].intensity
    
    def is_emotion_intense(self, emotion_type: EmotionType) -> bool:
        """判断情感是否强烈"""
        return self.emotions[emotion_type].intensity >= self.intense_threshold
    
    def is_emotion_moderate(self, emotion_type: EmotionType) -> bool:
        """判断情感是否中等"""
        return (self.moderate_threshold <= 
                self.emotions[emotion_type].intensity < 
                self.intense_threshold)
    
    def get_decision_weights(self) -> Dict[str, float]:
        """
        获取情感对决策的影响权重
        Returns:
            包含exploration(探索)、risk(冒险)、social(社交)权重的字典
        """
        weights = {"exploration": 1.0, "risk": 1.0, "social": 1.0}
        
        # 根据主导情感调整权重
        dominant = self.get_dominant_emotion()
        dominant_intensity = self.emotions[dominant].intensity / 100.0
        
        if dominant_intensity > 0.3:  # 只有情感强度超过30%才影响决策
            emotion_factors = self.emotion_weights[dominant]
            for key in weights:
                # 线性插值：情感强度越高，影响越大
                weights[key] = 1.0 + (emotion_factors[key] - 1.0) * dominant_intensity
        
        return weights
    
    def get_emotional_state_description(self) -> str:
        """生成情感状态的文本描述"""
        dominant = self.get_dominant_emotion()
        intensity = self.emotions[dominant].intensity
        
        # 根据强度和类型生成描述
        if intensity < 30:
            mood = "平静"
        elif intensity < 50:
            mood = f"略显{self._get_emotion_name(dominant)}"
        elif intensity < 70:
            mood = f"感到{self._get_emotion_name(dominant)}"
        else:
            mood = f"非常{self._get_emotion_name(dominant)}"
        
        # 添加次级情感
        secondary_emotions = sorted(
            [(e, s.intensity) for e, s in self.emotions.items() if e != dominant],
            key=lambda x: x[1],
            reverse=True
        )
        
        desc_parts = [mood]
        if secondary_emotions[0][1] > 40:
            desc_parts.append(f"，伴有{self._get_emotion_name(secondary_emotions[0][0])}")
        
        return "".join(desc_parts)
    
    def _get_emotion_name(self, emotion_type: EmotionType) -> str:
        """获取情感的中文名称"""
        names = {
            EmotionType.HAPPINESS: "快乐",
            EmotionType.SADNESS: "悲伤",
            EmotionType.FEAR: "恐惧",
            EmotionType.ANGER: "愤怒",
            EmotionType.DISGUST: "厌恶",
            EmotionType.SURPRISE: "惊讶"
        }
        return names.get(emotion_type, emotion_type.value)
    
    def get_emotion_summary(self) -> Dict:
        """获取情感状态摘要"""
        dominant = self.get_dominant_emotion()
        return {
            "dominant_emotion": dominant.value,
            "dominant_intensity": self.emotions[dominant].intensity,
            "emotional_state": self.get_emotional_state_description(),
            "decision_weights": self.get_decision_weights(),
            "all_emotions": {
                e.value: s.intensity for e, s in self.emotions.items()
            }
        }
    
    def analyze_trigger_reason(self, reason: str) -> EmotionType:
        """
        分析触发原因，自动推断情感类型
        Args:
            reason: 触发原因的文本描述
        Returns:
            推断的情感类型
        """
        reason_lower = reason.lower()
        
        # 关键词匹配规则
        emotion_keywords = {
            EmotionType.HAPPINESS: ["成功", "完成", "快乐", "高兴", "好", "优秀", "成就", "奖励"],
            EmotionType.SADNESS: ["失败", "错误", "遗憾", "难过", "失去", "悲伤", "痛苦"],
            EmotionType.FEAR: ["危险", "害怕", "担忧", "威胁", "风险", "恐惧", "紧急"],
            EmotionType.ANGER: ["愤怒", "不满", "错误", "故障", "阻碍", "不公平"],
            EmotionType.DISGUST: ["厌恶", "讨厌", "糟糕", "恶心", "不可接受"],
            EmotionType.SURPRISE: ["惊讶", "意外", "突然", "意想不到", "新奇"]
        }
        
        max_matches = 0
        best_match = EmotionType.SURPRISE  # 默认为惊讶
        
        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in reason_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = emotion
        
        return best_match


# 便捷函数
def create_emotional_trigger(emotion_system: EmotionSystem, event_type: str, context: str):
    """
    根据事件类型自动触发情感
    Args:
        emotion_system: 情感系统实例
        event_type: 事件类型（success, failure, danger, etc.）
        context: 事件上下文描述
    """
    emotion_triggers = {
        "success": (EmotionType.HAPPINESS, 60.0, f"完成任务: {context}"),
        "failure": (EmotionType.SADNESS, 50.0, f"任务失败: {context}"),
        "danger": (EmotionType.FEAR, 70.0, f"检测到危险: {context}"),
        "error": (EmotionType.ANGER, 40.0, f"遇到错误: {context}"),
        "surprise": (EmotionType.SURPRISE, 55.0, f"意外发现: {context}"),
        "discovery": (EmotionType.HAPPINESS, 45.0, f"新发现: {context}"),
    }
    
    if event_type in emotion_triggers:
        emotion, intensity, reason = emotion_triggers[event_type]
        emotion_system.trigger_emotion(emotion, intensity, reason)


if __name__ == "__main__":
    # 测试情感系统
    emotions = EmotionSystem()
    
    print("=== 情感系统测试 ===\n")
    
    # 模拟事件触发
    create_emotional_trigger(emotions, "success", "成功解决了复杂问题")
    print(f"当前状态: {emotions.get_emotional_state_description()}")
    print(f"决策权重: {emotions.get_decision_weights()}\n")
    
    time.sleep(1)
    create_emotional_trigger(emotions, "danger", "检测到系统异常")
    print(f"当前状态: {emotions.get_emotional_state_description()}")
    print(f"决策权重: {emotions.get_decision_weights()}\n")
    
    # 模拟情感衰减
    time.sleep(2)
    emotions.decay_emotions()
    print(f"衰减后状态: {emotions.get_emotional_state_description()}")
    print(f"情感摘要: {emotions.get_emotion_summary()}")
