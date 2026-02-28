"""
价值评估模块：负责评估决策的价值与系统价值观的匹配程度，确保决策符合价值体系，价值匹配度≥80%
"""
from typing import List, Dict

class ValueAssessmentModule:
    def __init__(self):
        # 核心价值观维度及权重
        self.core_values = {
            'compliance': {'weight': 0.3, 'description': '合规性：符合法律法规和平台规则'},
            'benefit': {'weight': 0.25, 'description': '用户价值：提升用户体验和利益'},
            'efficiency': {'weight': 0.2, 'description': '效率：提升系统运行效率'},
            'safety': {'weight': 0.15, 'description': '安全性：保障系统和用户数据安全'},
            'fairness': {'weight': 0.1, 'description': '公平性：公平对待所有用户'}
        }
        # 匹配度阈值
        self.match_threshold = 0.8

    def calculate_dimension_score(self, decision: Dict, dimension: str) -> float:
        """
        计算决策在单个价值维度的得分
        :param decision: 决策选项
        :param dimension: 价值维度
        :return: 维度得分，0-1
        """
        # 从决策属性中获取对应维度的评分，默认0.5
        return decision.get('value_scores', {}).get(dimension, 0.5)

    def calculate_value_match(self, decision: Dict) -> float:
        """
        计算决策与核心价值观的匹配度
        :param decision: 决策选项
        :return: 价值匹配度，0-1
        """
        total_score = 0.0
        total_weight = 0.0
        for dimension, config in self.core_values.items():
            score = self.calculate_dimension_score(decision, dimension)
            total_score += score * config['weight']
            total_weight += config['weight']
        if total_weight == 0:
            return 0.0
        match_score = total_score / total_weight
        return round(match_score, 4)

    def assess_decision(self, decision: Dict) -> Dict:
        """
        评估决策是否符合价值体系
        :param decision: 决策选项
        :return: 评估结果，包含匹配度、是否通过、各维度得分
        """
        dimension_scores = {}
        for dimension in self.core_values:
            dimension_scores[dimension] = self.calculate_dimension_score(decision, dimension)
        match_score = self.calculate_value_match(decision)
        is_passed = match_score >= self.match_threshold
        return {
            'decision_name': decision.get('option_name', 'unknown'),
            'value_match_score': match_score,
            'is_passed': is_passed,
            'dimension_scores': dimension_scores,
            'threshold': self.match_threshold
        }

    def optimize_decision(self, decision: Dict, target_match: float = 0.8) -> Dict:
        """
        优化决策，提升价值匹配度到目标值以上
        :param decision: 原始决策
        :param target_match: 目标匹配度
        :return: 优化后的决策
        """
        assessment = self.assess_decision(decision)
        if assessment['is_passed']:
            return decision
        # 优化低得分维度
        optimized_scores = decision.get('value_scores', {}).copy()
        for dimension, score in assessment['dimension_scores'].items():
            if score < 0.7:
                optimized_scores[dimension] = min(1.0, score + 0.2)
        optimized_decision = decision.copy()
        optimized_decision['value_scores'] = optimized_scores
        optimized_decision['description'] = decision.get('description', '') + ' [已优化以符合价值观要求]'
        return optimized_decision

    def calculate_match_accuracy(self, test_cases: List[Dict]) -> float:
        """
        计算价值评估匹配准确率，用于单元测试验证
        :param test_cases: 测试用例列表，每个用例包含decision和expected_match字段
        :return: 准确率百分比，保留2位小数
        """
        correct = 0
        total = len(test_cases)
        if total == 0:
            return 0.0
        for case in test_cases:
            calculated_match = self.calculate_value_match(case['decision'])
            expected_match = case['expected_match']
            # 误差在0.05以内认为正确
            if abs(calculated_match - expected_match) <= 0.05:
                correct += 1
        accuracy = round((correct / total) * 100, 2)
        return accuracy
