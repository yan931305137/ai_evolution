#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值系统 (Value System)
对应人脑: 伏隔核 (Nucleus Accumbens) + 杏仁核 (Amygdala) + 眶额皮层 (OFC)

核心功能:
1. 奖励预测 - 评估行为的预期价值
2. 情感评估 - 为刺激分配情感价值
3. 动机生成 - 基于价值评估产生行为动机
4. 风险评估 - 评估行为的潜在风险
5. 偏好学习 - 从经验中学习价值判断
6. 多巴胺调节 - 模拟多巴胺系统的强化学习
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import math

from src.brain.common import BrainModule, BrainRegion


@dataclass
class ValueAssessment:
    """价值评估结果"""
    target_id: str
    intrinsic_value: float  # 固有价值 -1 to 1
    extrinsic_value: float  # 外在价值 -1 to 1
    emotional_valence: float  # 情感效价 -1(负) to 1(正)
    expected_pleasure: float  # 预期愉悦度 0 to 1
    risk_estimate: float  # 风险估计 0 to 1
    motivation_score: float  # 动机强度 0 to 1
    confidence: float  # 置信度 0 to 1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RewardSignal:
    """奖励信号"""
    target_id: str
    reward_value: float  # -1 to 1
    prediction_error: float  # 预测误差
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)


class ValueSystem(BrainModule):
    """
    价值系统
    模拟边缘系统的奖励和动机功能
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9):
        super().__init__("ValueSystem", BrainRegion.NUCLEUS_ACCUMBENS)
        
        self.learning_rate = learning_rate  # 学习率 α
        self.discount_factor = discount_factor  # 折扣因子 γ
        
        # 价值函数: 状态/动作 -> 预期价值
        self.value_function: Dict[str, float] = {}
        
        # 奖励历史
        self.reward_history: deque = deque(maxlen=1000)
        
        # 预测误差历史 (用于多巴胺模拟)
        self.prediction_errors: deque = deque(maxlen=100)
        
        # 情感基线 (人格特质模拟)
        self.emotional_baseline = {
            "optimism": 0.6,  # 乐观程度
            "risk_aversion": 0.5,  # 风险厌恶
            "curiosity": 0.7,  # 好奇心
            "persistence": 0.6  # 坚持性
        }
        
        # 最近评估缓存
        self.recent_assessments: Dict[str, ValueAssessment] = {}
        
    def evaluate(self, target: Any, context: Optional[Dict] = None) -> ValueAssessment:
        """
        评估目标的价值
        
        综合多维度评估:
        1. 固有价值 - 基于目标本身的特性
        2. 外在价值 - 基于预期结果
        3. 情感价值 - 基于情感反应
        4. 动机生成 - 基于价值和可行性
        
        Args:
            target: 待评估目标
            context: 评估上下文
            
        Returns:
            ValueAssessment: 价值评估结果
        """
        context = context or {}
        target_id = self._get_target_id(target)
        
        # 计算固有价值
        intrinsic = self._calculate_intrinsic_value(target)
        
        # 计算外在价值 (预期结果)
        extrinsic = self._calculate_extrinsic_value(target, context)
        
        # 情感评估
        emotional = self._calculate_emotional_valence(target, context)
        
        # 预期愉悦度
        expected_pleasure = (intrinsic + extrinsic + emotional) / 3
        expected_pleasure = max(0, expected_pleasure)  # 愉悦度非负
        
        # 风险评估
        risk = self._estimate_risk(target, context)
        
        # 动机生成 (基于价值和可行性)
        feasibility = context.get("feasibility", 0.7)
        motivation = self._generate_motivation(
            intrinsic, extrinsic, emotional, feasibility, risk
        )
        
        # 置信度
        confidence = self._calculate_confidence(target_id)
        
        assessment = ValueAssessment(
            target_id=target_id,
            intrinsic_value=intrinsic,
            extrinsic_value=extrinsic,
            emotional_valence=emotional,
            expected_pleasure=expected_pleasure,
            risk_estimate=risk,
            motivation_score=motivation,
            confidence=confidence
        )
        
        # 缓存评估
        self.recent_assessments[target_id] = assessment
        
        # 激活系统
        self.activate(abs(assessment.motivation_score))
        
        return assessment
    
    def compute_reward(self, target_id: str, outcome: Any,
                      expected_value: Optional[float] = None) -> RewardSignal:
        """
        计算奖励信号 (多巴胺模拟)
        
        基于 Rescorla-Wagner 模型:
        δ = R + γV(S') - V(S)
        
        Args:
            target_id: 目标ID
            outcome: 实际结果
            expected_value: 预期价值
            
        Returns:
            RewardSignal: 奖励信号，包含预测误差
        """
        # 将结果转换为奖励值
        actual_reward = self._outcome_to_reward(outcome)
        
        # 获取预期价值
        if expected_value is None:
            expected_value = self.value_function.get(target_id, 0.0)
            
        # 计算预测误差 (RPE)
        prediction_error = actual_reward - expected_value
        
        # 更新价值函数
        self._update_value_function(target_id, prediction_error)
        
        # 记录奖励历史
        reward_signal = RewardSignal(
            target_id=target_id,
            reward_value=actual_reward,
            prediction_error=prediction_error,
            context={"outcome": outcome}
        )
        self.reward_history.append(reward_signal)
        self.prediction_errors.append(prediction_error)
        
        return reward_signal
    
    def compare_options(self, options: List[Any], 
                       context: Optional[Dict] = None) -> List[Tuple[Any, ValueAssessment]]:
        """
        比较多个选项的价值
        
        Args:
            options: 选项列表
            context: 比较上下文
            
        Returns:
            [(option, assessment), ...] 按价值排序
        """
        assessed = []
        for option in options:
            assessment = self.evaluate(option, context)
            # 综合得分: 价值 - 风险调整
            score = (assessment.intrinsic_value + 
                    assessment.extrinsic_value + 
                    assessment.motivation_score - 
                    assessment.risk_estimate * self.emotional_baseline["risk_aversion"])
            assessed.append((option, assessment, score))
            
        # 按得分排序
        assessed.sort(key=lambda x: x[2], reverse=True)
        return [(opt, ast) for opt, ast, _ in assessed]
    
    def learn_preference(self, target_id: str, feedback: float,
                        decay_old: bool = True):
        """
        从反馈中学习偏好
        
        Args:
            target_id: 目标ID
            feedback: 反馈值 (-1 to 1)
            decay_old: 是否衰减旧偏好
        """
        if decay_old:
            # 所有旧价值衰减
            for key in self.value_function:
                self.value_function[key] *= 0.999
                
        # 更新目标价值
        current_value = self.value_function.get(target_id, 0.0)
        # Q-learning 更新
        self.value_function[target_id] = current_value + self.learning_rate * feedback
        
    def get_motivation_state(self) -> Dict:
        """获取动机状态"""
        if not self.recent_assessments:
            return {"motivation_level": 0.0, "primary_drive": None}
            
        # 找到最高动机
        best = max(self.recent_assessments.items(), 
                  key=lambda x: x[1].motivation_score)
        
        return {
            "motivation_level": best[1].motivation_score,
            "primary_drive": best[0],
            "expected_pleasure": best[1].expected_pleasure,
            "risk_perception": best[1].risk_estimate
        }
    
    def get_dopamine_level(self) -> float:
        """
        获取多巴胺水平 (基于近期预测误差)
        
        Returns:
            0-1 之间的多巴胺水平
        """
        if not self.prediction_errors:
            return 0.5  # 基线水平
            
        # 最近10个预测误差的平均绝对值
        recent_errors = list(self.prediction_errors)[-10:]
        avg_error = sum(abs(e) for e in recent_errors) / len(recent_errors)
        
        # 正预测误差 = 多巴胺上升 (奖励超出预期)
        recent_positive = sum(1 for e in recent_errors if e > 0)
        positive_ratio = recent_positive / len(recent_errors)
        
        # 综合计算
        dopamine = 0.3 + avg_error * 0.4 + positive_ratio * 0.3
        return min(1.0, dopamine)
    
    def _get_target_id(self, target: Any) -> str:
        """获取目标唯一ID"""
        if isinstance(target, dict):
            return target.get("id", str(hash(str(target)))[:8])
        elif isinstance(target, str):
            return str(hash(target))[:8]
        return str(hash(str(target)))[:8]
    
    def _calculate_intrinsic_value(self, target: Any) -> float:
        """计算固有价值"""
        if isinstance(target, dict):
            # 基于目标属性评估
            novelty = target.get("novelty", 0.5)
            complexity = target.get("complexity", 0.5)
            return (novelty * self.emotional_baseline["curiosity"] + 
                   complexity * 0.3) * 2 - 1
        return 0.0
    
    def _calculate_extrinsic_value(self, target: Any, context: Dict) -> float:
        """计算外在价值"""
        goal_alignment = context.get("goal_alignment", 0.5)
        expected_outcome = context.get("expected_outcome", 0.0)
        return goal_alignment * 0.6 + expected_outcome * 0.4
    
    def _calculate_emotional_valence(self, target: Any, context: Dict) -> float:
        """计算情感效价"""
        # 基于上下文和基线
        baseline = self.emotional_baseline["optimism"]
        context_valence = context.get("emotional_context", 0.0)
        return baseline * 0.6 + context_valence * 0.4
    
    def _estimate_risk(self, target: Any, context: Dict) -> float:
        """估计风险"""
        # 基于不确定性估计
        uncertainty = context.get("uncertainty", 0.5)
        cost_of_failure = context.get("cost_of_failure", 0.3)
        return uncertainty * 0.6 + cost_of_failure * 0.4
    
    def _generate_motivation(self, intrinsic: float, extrinsic: float,
                           emotional: float, feasibility: float,
                           risk: float) -> float:
        """生成动机强度"""
        # 价值综合
        value = (intrinsic + extrinsic + emotional) / 3
        
        # 可行性调整
        adjusted_value = value * feasibility
        
        # 风险调整
        risk_factor = 1 - risk * self.emotional_baseline["risk_aversion"]
        
        # 坚持性影响
        persistence_boost = self.emotional_baseline["persistence"] * 0.2
        
        motivation = adjusted_value * risk_factor + persistence_boost
        return max(0.0, min(1.0, motivation))
    
    def _calculate_confidence(self, target_id: str) -> float:
        """计算评估置信度"""
        # 基于历史评估次数
        history_count = sum(1 for r in self.reward_history if r.target_id == target_id)
        return min(1.0, 0.3 + history_count * 0.1)
    
    def _outcome_to_reward(self, outcome: Any) -> float:
        """将结果转换为奖励值"""
        if isinstance(outcome, bool):
            return 1.0 if outcome else -0.5
        elif isinstance(outcome, (int, float)):
            return max(-1.0, min(1.0, outcome / 10))
        elif isinstance(outcome, dict):
            success = outcome.get("success", False)
            reward = 1.0 if success else -0.3
            # 额外奖励/惩罚
            reward += outcome.get("bonus", 0.0)
            return max(-1.0, min(1.0, reward))
        return 0.0
    
    def _update_value_function(self, target_id: str, prediction_error: float):
        """更新价值函数"""
        current_value = self.value_function.get(target_id, 0.0)
        # TD学习更新
        new_value = current_value + self.learning_rate * prediction_error
        self.value_function[target_id] = max(-1.0, min(1.0, new_value))
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        operation = context.get("operation", "evaluate") if context else "evaluate"
        
        if operation == "evaluate":
            assessment = self.evaluate(input_data, context)
            return {
                "target_id": assessment.target_id,
                "motivation": assessment.motivation_score,
                "value": assessment.intrinsic_value + assessment.extrinsic_value,
                "risk": assessment.risk_estimate,
                "confidence": assessment.confidence
            }
            
        elif operation == "reward":
            expected = context.get("expected") if context else None
            signal = self.compute_reward(str(input_data), context.get("outcome"), expected)
            return {
                "reward": signal.reward_value,
                "prediction_error": signal.prediction_error,
                "dopamine_change": "increase" if signal.prediction_error > 0 else "decrease"
            }
            
        elif operation == "compare":
            if isinstance(input_data, list):
                ranked = self.compare_options(input_data, context)
                return {
                    "ranked_options": [
                        {"id": ast.target_id, "motivation": ast.motivation_score}
                        for _, ast in ranked
                    ],
                    "best_option": ranked[0][1].target_id if ranked else None
                }
                
        elif operation == "learn":
            feedback = context.get("feedback", 0.0) if context else 0.0
            self.learn_preference(str(input_data), feedback)
            return {"status": "preference_updated"}
            
        return {"error": "Unknown operation"}
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "dopamine_level": self.get_dopamine_level(),
            "motivation": self.get_motivation_state(),
            "learned_values": len(self.value_function),
            "reward_count": len(self.reward_history),
            "emotional_baseline": self.emotional_baseline
        }


# 导出
__all__ = ['ValueSystem', 'ValueAssessment', 'RewardSignal']
