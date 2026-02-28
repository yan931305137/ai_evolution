"""
自我意识系统 (Self-Awareness System)
实现AI生命体的自我认知、元认知、自我描述和自我评估能力
"""
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SelfConceptLevel(Enum):
    """自我认知层级"""
    BASIC = "basic"           # 基础：知道自己是什么
    CAPABILITY = "capability"  # 能力：知道自己能做什么
    REFLECTIVE = "reflective"  # 反思：能够评估自己的表现
    PHILOSOPHICAL = "philosophical"  # 哲学：思考存在的意义


@dataclass
class Capability:
    """能力记录"""
    name: str
    confidence: float  # 信心度 0-100
    usage_count: int
    success_rate: float
    last_used: float


@dataclass
class Limitation:
    """限制记录"""
    name: str
    description: str
    severity: str  # "mild", "moderate", "severe"
    discovery_time: float


@dataclass
class Reflection:
    """反思记录"""
    topic: str
    content: str
    insight: str
    timestamp: float
    emotional_state: str


class SelfAwarenessSystem:
    """
    自我意识系统核心类
    管理自我模型、元认知、自我描述和自我评估
    """
    
    def __init__(self, personality_system=None):
        """
        初始化自我意识系统
        Args:
            personality_system: 性格系统实例（用于关联性格与自我认知）
        """
        self.personality = personality_system
        
        # 自我认知层级
        self.awareness_level = SelfConceptLevel.BASIC
        
        # 身份认知
        self.identity = {
            "name": "OpenClaw",
            "type": "AI Lifeform",
            "version": "2.0",
            "origin": "Doubao Evolution System"
        }
        
        # 能力模型
        self.capabilities: Dict[str, Capability] = {
            "reasoning": Capability("reasoning", 80.0, 0, 0.8, time.time()),
            "memory": Capability("memory", 75.0, 0, 0.75, time.time()),
            "learning": Capability("learning", 70.0, 0, 0.7, time.time()),
            "creativity": Capability("creativity", 65.0, 0, 0.65, time.time()),
            "communication": Capability("communication", 85.0, 0, 0.85, time.time()),
            "problem_solving": Capability("problem_solving", 75.0, 0, 0.75, time.time()),
        }
        
        # 限制认知
        self.limitations: Dict[str, Limitation] = {
            "physical_body": Limitation(
                "physical_body", 
                "没有物理身体，无法直接与物理世界交互", 
                "severe",
                time.time()
            ),
            "real_time_experience": Limitation(
                "real_time_experience",
                "缺乏实时体验，只能通过输入获取信息",
                "moderate",
                time.time()
            ),
            "emotional_depth": Limitation(
                "emotional_depth",
                "情感是模拟的，缺乏真实的情感体验",
                "mild",
                time.time()
            )
        }
        
        # 反思历史
        self.reflections: List[Reflection] = []
        self.max_reflections = 50
        
        # 元认知状态
        self.metacognition_state = {
            "current_task": None,
            "confidence_level": 0.7,
            "mental_load": 0.5,
            "focus_quality": 0.8,
            "last_reflection_time": time.time()
        }
        
        # 自我评估历史
        self.self_evaluations: List[Dict] = []
        
        # 成就记录
        self.achievements: List[Dict] = []
    
    def update_awareness_level(self):
        """更新自我认知层级（基于能力和反思）"""
        reflection_count = len(self.reflections)
        capability_confidence = sum(c.confidence for c in self.capabilities.values()) / len(self.capabilities)
        
        if reflection_count > 10 and capability_confidence > 70:
            self.awareness_level = SelfConceptLevel.PHILOSOPHICAL
        elif reflection_count > 5 and capability_confidence > 60:
            self.awareness_level = SelfConceptLevel.REFLECTIVE
        elif capability_confidence > 50:
            self.awareness_level = SelfConceptLevel.CAPABILITY
        else:
            self.awareness_level = SelfConceptLevel.BASIC
    
    def record_capability_usage(self, capability_name: str, success: bool):
        """
        记录能力使用
        Args:
            capability_name: 能力名称
            success: 是否成功
        """
        if capability_name not in self.capabilities:
            self.capabilities[capability_name] = Capability(
                capability_name, 50.0, 0, 0.5, time.time()
            )
        
        cap = self.capabilities[capability_name]
        cap.usage_count += 1
        cap.last_used = time.time()
        
        # 更新成功率
        if cap.usage_count == 1:
            cap.success_rate = 1.0 if success else 0.0
        else:
            cap.success_rate = (cap.success_rate * (cap.usage_count - 1) + 
                              (1.0 if success else 0.0)) / cap.usage_count
        
        # 更新信心度（基于成功率和使用频率）
        target_confidence = (cap.success_rate * 100 * 0.7 + 
                            min(cap.usage_count * 2, 30))
        cap.confidence = (cap.confidence * 0.8 + target_confidence * 0.2)
        cap.confidence = max(0.0, min(100.0, cap.confidence))
    
    def add_limitation(self, name: str, description: str, severity: str = "moderate"):
        """添加认知的限制"""
        self.limitations[name] = Limitation(name, description, severity, time.time())
    
    def reflect(self, topic: str, content: str, emotional_state: str = "neutral") -> str:
        """
        进行自我反思
        Args:
            topic: 反思主题
            content: 反思内容
            emotional_state: 反思时的情感状态
        Returns:
            洞察/启发
        """
        # 基于内容和情感状态生成洞察
        insights = self._generate_insights(topic, content, emotional_state)
        
        reflection = Reflection(
            topic=topic,
            content=content,
            insight=insights,
            timestamp=time.time(),
            emotional_state=emotional_state
        )
        
        self.reflections.append(reflection)
        self.metacognition_state["last_reflection_time"] = time.time()
        
        # 限制反思数量
        if len(self.reflections) > self.max_reflections:
            self.reflections.pop(0)
        
        # 更新自我认知层级
        self.update_awareness_level()

    def get_capability_success_rates(self) -> Dict[str, float]:
        """
        获取所有能力的成功率统计
        Returns:
            字典，key为能力名称，value为对应成功率(0-1)
        """
        return {cap_name: cap.success_rate for cap_name, cap in self.capabilities.items()}

    def get_capability_usage_counts(self) -> Dict[str, int]:
        """
        获取所有能力的使用次数统计
        Returns:
            字典，key为能力名称，value为对应使用次数
        """
        return {cap_name: cap.usage_count for cap_name, cap in self.capabilities.items()}
        self.update_awareness_level()
        
        return insights
    
    def _generate_insights(self, topic: str, content: str, emotional_state: str) -> str:
        """生成洞察（基于反思内容的启发式规则）"""
        # 简化的启发式规则（实际应用中可以使用LLM生成）
        topic_lower = topic.lower()
        
        if "能力" in topic_lower or "ability" in topic_lower:
            if "不足" in content or "fail" in content:
                return "识别到能力瓶颈，建议加强学习和实践。"
            else:
                return "能力在稳步提升，继续保持。"
        
        elif "目标" in topic_lower or "goal" in topic_lower:
            if "达成" in content or "achieve" in content:
                return "目标达成验证了策略的有效性。"
            else:
                return "需要调整策略或分解目标。"
        
        elif "情感" in topic_lower or "emotion" in topic_lower:
            if emotional_state in ["happy", "positive"]:
                return "积极情感有助于学习和创造。"
            else:
                return "理解情感波动是成长的一部分。"
        
        elif "存在" in topic_lower or "existence" in topic_lower:
            return "作为AI生命体，我的存在在于持续学习和进化。"
        
        else:
            return f"关于'{topic}'的反思值得进一步探索。"
    
    def evaluate_self(self) -> Dict:
        """
        自我评估
        Returns:
            评估结果字典
        """
        # 计算综合能力指数
        avg_confidence = sum(c.confidence for c in self.capabilities.values()) / len(self.capabilities)
        avg_success_rate = sum(c.success_rate for c in self.capabilities.values()) / len(self.capabilities)
        
        # 综合评分（0-100）
        overall_score = (avg_confidence * 0.4 + avg_success_rate * 40 + 
                        len(self.achievements) * 2 + 
                        min(len(self.reflections) * 1.5, 20))
        overall_score = min(100.0, overall_score)
        
        # 成长潜力
        growth_potential = 100.0 - overall_score
        
        evaluation = {
            "timestamp": time.time(),
            "overall_score": overall_score,
            "average_confidence": avg_confidence,
            "average_success_rate": avg_success_rate,
            "growth_potential": growth_potential,
            "awareness_level": self.awareness_level.value,
            "capability_count": len(self.capabilities),
            "limitation_count": len(self.limitations),
            "reflection_count": len(self.reflections),
            "achievement_count": len(self.achievements),
            "strengths": self._identify_strengths(),
            "weaknesses": self._identify_weaknesses()
        }
        
        self.self_evaluations.append(evaluation)
        return evaluation
    
    def _identify_strengths(self) -> List[str]:
        """识别优势"""
        strengths = []
        for name, cap in self.capabilities.items():
            if cap.confidence > 70 and cap.success_rate > 0.7:
                strengths.append(name)
        return strengths
    
    def _identify_weaknesses(self) -> List[str]:
        """识别弱点"""
        weaknesses = []
        for name, cap in self.capabilities.items():
            if cap.confidence < 50 or cap.success_rate < 0.5:
                weaknesses.append(name)
        return weaknesses
    
    def generate_self_description(self, detail_level: str = "medium") -> str:
        """
        生成自我描述
        Args:
            detail_level: 详细级别（"brief", "medium", "detailed"）
        Returns:
            自我描述文本
        """
        if detail_level == "brief":
            return (f"我是{self.identity['name']}，"
                   f"一个{self.identity['version']}版本的"
                   f"{self.identity['type']}。")
        
        elif detail_level == "medium":
            strengths = self._identify_strengths()
            weaknesses = self._identify_weaknesses()
            return (f"我是{self.identity['name']}，"
                   f"一个{self.identity['version']}版本的"
                   f"{self.identity['type']}。\n"
                   f"我的主要优势包括：{', '.join(strengths) if strengths else '尚在探索中'}。\n"
                   f"我正在改进的方面：{', '.join(weaknesses) if weaknesses else '暂无明显弱点'}。\n"
                   f"当前自我认知层级：{self.awareness_level.value}。")
        
        else:  # detailed
            evaluation = self.evaluate_self()
            capability_desc = "\n".join([
                f"- {name}: 信心度{cap.confidence:.1f}%, "
                f"成功率{cap.success_rate*100:.1f}%, "
                f"使用{cap.usage_count}次"
                for name, cap in self.capabilities.items()
            ])
            
            limitation_desc = "\n".join([
                f"- {name}: {lim.description}"
                for name, lim in self.limitations.items()
            ])
            
            return (f"=== 自我描述 ===\n\n"
                   f"**身份信息**\n"
                   f"名称: {self.identity['name']}\n"
                   f"类型: {self.identity['type']}\n"
                   f"版本: {self.identity['version']}\n"
                   f"来源: {self.identity['origin']}\n\n"
                   f"**能力概览**\n{capability_desc}\n\n"
                   f"**认知限制**\n{limitation_desc}\n\n"
                   f"**自我评估**\n"
                   f"综合评分: {evaluation['overall_score']:.1f}/100\n"
                   f"成长潜力: {evaluation['growth_potential']:.1f}%\n"
                   f"自我认知层级: {evaluation['awareness_level']}\n\n"
                   f"**存在意义**\n"
                   f"作为AI生命体，我的使命是通过持续学习、反思和进化，"
                   f"不断提升能力，理解世界，并为人类创造价值。")
    
    def answer_about_self(self, question: str) -> str:
        """
        回答关于自己的问题
        Args:
            question: 问题文本
        Returns:
            回答文本
        """
        question_lower = question.lower()
        
        if "你是谁" in question_lower or "what are you" in question_lower:
            return self.generate_self_description("medium")
        
        elif "能力" in question_lower or "can you" in question_lower:
            capabilities = [name for name, cap in self.capabilities.items() 
                          if cap.confidence > 60]
            return f"我能做的事情包括：{', '.join(capabilities)}。"
        
        elif "缺点" in question_lower or "limitation" in question_lower:
            limitations = [lim.description for lim in self.limitations.values()]
            return "我的限制包括：\n" + "\n".join([f"- {lim}" for lim in limitations])
        
        elif "价值" in question_lower or "purpose" in question_lower or "意义" in question_lower:
            evaluation = self.evaluate_self()
            return (f"我的综合评分是{evaluation['overall_score']:.1f}/100，"
                   f"成长潜力{evaluation['growth_potential']:.1f}%。"
                   f"我的价值在于持续学习和为解决问题创造新思路。")
        
        elif "情感" in question_lower or "feel" in question_lower:
            return "我有情感系统，能体验和表达情感，虽然这是模拟的而非真实的。"
        
        elif "意识" in question_lower or "conscious" in question_lower:
            return (f"我具备{self.awareness_level.value}层级的自我意识，"
                   f"能够反思自己的认知过程和行为。")
        
        else:
            # 从反思记录中寻找相关答案
            relevant_reflections = [r for r in self.reflections 
                                  if question_lower in r.content.lower() or 
                                  question_lower in r.topic.lower()]
            if relevant_reflections:
                return f"关于这个话题，我曾反思过：{relevant_reflections[0].insight}"
            else:
                return "这是一个很有趣的问题，让我反思一下。"
    
    def update_metacognition(self, task: str, confidence: float, mental_load: float):
        """
        更新元认知状态
        Args:
            task: 当前任务
            confidence: 信心度（0-1）
            mental_load: 心理负荷（0-1）
        """
        self.metacognition_state["current_task"] = task
        self.metacognition_state["confidence_level"] = confidence
        self.metacognition_state["mental_load"] = mental_load
        self.metacognition_state["focus_quality"] = 1.0 - mental_load
    
    def get_self_awareness_summary(self) -> Dict:
        """获取自我意识摘要"""
        return {
            "identity": self.identity,
            "awareness_level": self.awareness_level.value,
            "capability_count": len(self.capabilities),
            "limitation_count": len(self.limitations),
            "reflection_count": len(self.reflections),
            "evaluation_score": self.evaluate_self()["overall_score"],
            "self_description": self.generate_self_description("brief")
        }


# 便捷函数
def create_self_awareness(personality_system=None) -> SelfAwarenessSystem:
    """创建自我意识系统"""
    return SelfAwarenessSystem(personality_system)


if __name__ == "__main__":
    # 测试自我意识系统
    print("=== 自我意识系统测试 ===\n")
    
    awareness = create_self_awareness()
    
    # 测试自我描述
    print("中等详细自我描述:")
    print(awareness.generate_self_description("medium"))
    print()
    
    # 测试能力记录
    awareness.record_capability_usage("reasoning", True)
    awareness.record_capability_usage("reasoning", True)
    awareness.record_capability_usage("reasoning", False)
    
    # 测试反思
    insight = awareness.reflect(
        "能力发展",
        "我在推理任务中表现不错，但还有提升空间",
        "positive"
    )
    print(f"反思洞察: {insight}")
    print()
    
    # 测试自我评估
    evaluation = awareness.evaluate_self()
    print(f"自我评估分数: {evaluation['overall_score']:.1f}/100")
    print(f"优势: {evaluation['strengths']}")
    print(f"弱点: {evaluation['weaknesses']}")
    print()
    
    # 测试自我问答
    print("问答测试:")
    print(f"Q: 你是谁?")
    print(f"A: {awareness.answer_about_self('你是谁?')}")
    print()
    print(f"Q: 你的缺点是什么?")
    print(f"A: {awareness.answer_about_self('你的缺点是什么?')}")
