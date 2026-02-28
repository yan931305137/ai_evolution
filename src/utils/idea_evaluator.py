"""
想法评估器 (Idea Evaluator)

评估创造性想法的质量、可行性、价值和风险
为进化闭环提供决策依据
"""
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class EvaluationMetric(Enum):
    """评估指标"""
    NOVELTY = "novelty"           # 新颖性
    FEASIBILITY = "feasibility"   # 可行性
    VALUE = "value"               # 价值
    RISK = "risk"                 # 风险（越低越好）
    ALIGNMENT = "alignment"       # 与目标对齐度
    COMPLEXITY = "complexity"     # 复杂度（越低越好）


@dataclass
class IdeaEvaluation:
    """想法评估结果"""
    idea_id: str
    idea_content: str
    scores: Dict[str, float]  # 各指标得分 0-100
    overall_score: float
    confidence: float  # 评估置信度
    evaluator_notes: List[str]
    recommendation: str  # apply / refine / discard
    estimated_effort: str  # low / medium / high
    estimated_impact: str  # low / medium / high
    risks: List[str]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "idea_id": self.idea_id,
            "idea_content": self.idea_content[:200],
            "scores": self.scores,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "estimated_effort": self.estimated_effort,
            "estimated_impact": self.estimated_impact,
            "timestamp": self.timestamp
        }


class IdeaEvaluator:
    """
    想法评估器
    
    多维度评估创造性想法，使用规则和启发式方法
    """
    
    # 评估权重配置
    DEFAULT_WEIGHTS = {
        EvaluationMetric.NOVELTY: 0.2,
        EvaluationMetric.FEASIBILITY: 0.25,
        EvaluationMetric.VALUE: 0.3,
        EvaluationMetric.RISK: 0.15,  # 风险得分越高越差，需要反向计算
        EvaluationMetric.ALIGNMENT: 0.1
    }
    
    def __init__(self, weights: Dict[EvaluationMetric, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.evaluation_history: List[IdeaEvaluation] = []
        self.idea_patterns = self._load_idea_patterns()
    
    def _load_idea_patterns(self) -> Dict[str, List[str]]:
        """加载想法模式库，用于评估"""
        return {
            "high_value_indicators": [
                "优化", "提升", "改进", "增强", "加速",
                "自动化", "智能化", "高效", "精准"
            ],
            "risk_indicators": [
                "重构", "重写", "彻底改变", "大规模",
                "复杂", "高难度", "风险", "依赖"
            ],
            "feasibility_indicators": [
                "简单", "快速", "可行", "实现", "配置",
                "调整", "参数", "模块化"
            ],
            "novelty_indicators": [
                "创新", "新颖", "独特", "前所未有",
                "突破", "颠覆", "全新"
            ]
        }
    
    def evaluate(self, idea_content: str, context: Dict = None) -> IdeaEvaluation:
        """
        评估单个想法
        
        Args:
            idea_content: 想法内容
            context: 评估上下文
            
        Returns:
            IdeaEvaluation: 评估结果
        """
        # 生成唯一ID
        idea_id = hashlib.md5(idea_content.encode()).hexdigest()[:8]
        
        # 计算各维度得分
        scores = self._calculate_scores(idea_content, context)
        
        # 计算综合得分
        overall_score = self._calculate_overall_score(scores)
        
        # 确定置信度
        confidence = self._calculate_confidence(idea_content, scores)
        
        # 生成建议
        recommendation = self._generate_recommendation(scores, overall_score)
        
        # 估算投入和影响
        estimated_effort = self._estimate_effort(idea_content, scores)
        estimated_impact = self._estimate_impact(idea_content, scores)
        
        # 识别风险
        risks = self._identify_risks(idea_content)
        
        # 生成评估注释
        notes = self._generate_notes(scores)
        
        evaluation = IdeaEvaluation(
            idea_id=idea_id,
            idea_content=idea_content,
            scores=scores,
            overall_score=overall_score,
            confidence=confidence,
            evaluator_notes=notes,
            recommendation=recommendation,
            estimated_effort=estimated_effort,
            estimated_impact=estimated_impact,
            risks=risks
        )
        
        self.evaluation_history.append(evaluation)
        return evaluation
    
    def _calculate_scores(self, idea: str, context: Dict = None) -> Dict[str, float]:
        """计算各维度得分"""
        idea_lower = idea.lower()
        scores = {}
        
        # 1. 新颖性 (0-100)
        novelty_score = sum(
            15 for indicator in self.idea_patterns["novelty_indicators"]
            if indicator in idea_lower
        )
        scores[EvaluationMetric.NOVELTY.value] = min(100, max(30, novelty_score))
        
        # 2. 可行性 (0-100)
        feasibility_score = 50  # 基础分
        feasibility_score += sum(
            10 for indicator in self.idea_patterns["feasibility_indicators"]
            if indicator in idea_lower
        )
        feasibility_score -= sum(
            15 for indicator in self.idea_patterns["risk_indicators"]
            if indicator in idea_lower
        )
        scores[EvaluationMetric.FEASIBILITY.value] = min(100, max(20, feasibility_score))
        
        # 3. 价值 (0-100)
        value_score = 40  # 基础分
        value_score += sum(
            12 for indicator in self.idea_patterns["high_value_indicators"]
            if indicator in idea_lower
        )
        # 量化指标加分
        if any(char.isdigit() for char in idea):
            value_score += 20  # 有具体数字说明有量化目标
        scores[EvaluationMetric.VALUE.value] = min(100, max(30, value_score))
        
        # 4. 风险 (0-100，越高越差) - 反向计算
        risk_score = 30  # 基础分
        risk_score += sum(
            20 for indicator in self.idea_patterns["risk_indicators"]
            if indicator in idea_lower
        )
        # 长度过长增加风险
        if len(idea) > 500:
            risk_score += 10
        scores[EvaluationMetric.RISK.value] = min(100, max(10, risk_score))
        
        # 5. 对齐度 (0-100)
        alignment_score = 60  # 基础分
        if context and "goals" in context:
            for goal in context["goals"]:
                if any(kw in idea_lower for kw in goal.lower().split()):
                    alignment_score += 20
        scores[EvaluationMetric.ALIGNMENT.value] = min(100, alignment_score)
        
        # 6. 复杂度 (0-100，越低越好)
        complexity_score = 40
        if "简单" in idea or "快速" in idea:
            complexity_score -= 20
        if "复杂" in idea or "困难" in idea:
            complexity_score += 25
        scores[EvaluationMetric.COMPLEXITY.value] = min(100, max(10, complexity_score))
        
        return scores
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """计算综合得分"""
        weighted_sum = 0
        total_weight = 0
        
        for metric, weight in self.weights.items():
            score = scores.get(metric.value, 50)
            # 风险需要反向计算
            if metric == EvaluationMetric.RISK:
                score = 100 - score
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 50
    
    def _calculate_confidence(self, idea: str, scores: Dict[str, float]) -> float:
        """计算评估置信度"""
        # 基于信息量和得分分布计算
        base_confidence = 0.6
        
        # 想法越具体，置信度越高
        if len(idea) > 100:
            base_confidence += 0.1
        if any(char.isdigit() for char in idea):
            base_confidence += 0.1
        
        # 得分差异越小，置信度越高
        score_values = list(scores.values())
        if score_values:
            variance = sum((s - 50) ** 2 for s in score_values) / len(score_values)
            if variance < 200:
                base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _generate_recommendation(self, scores: Dict[str, float], overall: float) -> str:
        """生成应用建议"""
        feasibility = scores.get(EvaluationMetric.FEASIBILITY.value, 50)
        risk = scores.get(EvaluationMetric.RISK.value, 50)
        
        if overall >= 70 and feasibility >= 60 and risk <= 50:
            return "apply"
        elif overall >= 50 and feasibility >= 40:
            return "refine"
        else:
            return "discard"
    
    def _estimate_effort(self, idea: str, scores: Dict[str, float]) -> str:
        """估算投入成本"""
        complexity = scores.get(EvaluationMetric.COMPLEXITY.value, 50)
        feasibility = scores.get(EvaluationMetric.FEASIBILITY.value, 50)
        
        if complexity < 40 and feasibility > 70:
            return "low"
        elif complexity > 70 or feasibility < 40:
            return "high"
        else:
            return "medium"
    
    def _estimate_impact(self, idea: str, scores: Dict[str, float]) -> str:
        """估算预期影响"""
        value = scores.get(EvaluationMetric.VALUE.value, 50)
        novelty = scores.get(EvaluationMetric.NOVELTY.value, 50)
        
        if value > 75 or (value > 60 and novelty > 70):
            return "high"
        elif value < 40:
            return "low"
        else:
            return "medium"
    
    def _identify_risks(self, idea: str) -> List[str]:
        """识别潜在风险"""
        risks = []
        idea_lower = idea.lower()
        
        if "重构" in idea or "重写" in idea:
            risks.append("可能破坏现有功能")
        if "依赖" in idea:
            risks.append("增加外部依赖风险")
        if "大规模" in idea or "彻底改变" in idea:
            risks.append("变更范围过大，难以测试")
        if len(idea) < 50:
            risks.append("想法不够具体，实施细节不明")
        
        return risks if risks else ["未发现明显风险"]
    
    def _generate_notes(self, scores: Dict[str, float]) -> List[str]:
        """生成评估注释"""
        notes = []
        
        for metric in EvaluationMetric:
            score = scores.get(metric.value, 50)
            if score >= 70:
                notes.append(f"✅ {metric.value}: 优秀 ({score:.0f})")
            elif score < 40:
                notes.append(f"⚠️  {metric.value}: 需关注 ({score:.0f})")
        
        return notes
    
    def batch_evaluate(self, ideas: List[str], context: Dict = None) -> List[IdeaEvaluation]:
        """批量评估想法"""
        return [self.evaluate(idea, context) for idea in ideas]
    
    def get_top_ideas(self, n: int = 5) -> List[IdeaEvaluation]:
        """获取评分最高的N个想法"""
        sorted_ideas = sorted(
            self.evaluation_history,
            key=lambda x: x.overall_score,
            reverse=True
        )
        return sorted_ideas[:n]
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """获取评估统计"""
        if not self.evaluation_history:
            return {"total": 0}
        
        scores = [e.overall_score for e in self.evaluation_history]
        recommendations = [e.recommendation for e in self.evaluation_history]
        
        return {
            "total": len(self.evaluation_history),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "recommendation_distribution": {
                "apply": recommendations.count("apply"),
                "refine": recommendations.count("refine"),
                "discard": recommendations.count("discard")
            }
        }


# 便捷函数
def quick_evaluate(idea: str) -> IdeaEvaluation:
    """快速评估单个想法"""
    evaluator = IdeaEvaluator()
    return evaluator.evaluate(idea)


if __name__ == "__main__":
    # 测试
    evaluator = IdeaEvaluator()
    
    test_ideas = [
        "优化文档处理算法，提升检索效率30%",
        "实现一个复杂的神经网络系统，彻底改变整个架构",
        "添加一个简单的配置选项，允许用户自定义主题颜色"
    ]
    
    print("🧪 想法评估测试\n")
    for idea in test_ideas:
        result = evaluator.evaluate(idea)
        print(f"想法: {idea}")
        print(f"综合得分: {result.overall_score:.1f} (置信度: {result.confidence:.0%})")
        print(f"建议: {result.recommendation}")
        print(f"投入: {result.estimated_effort} | 影响: {result.estimated_impact}")
        print(f"风险: {', '.join(result.risks)}")
        print("-" * 60)
