"""
决策模块：基于感知输入、注意力筛选的重要信息和记忆检索结果，生成可行决策选项并选择最优决策
"""
from typing import List, Dict, Tuple, Optional

class DecisionModule:
    def __init__(self):
        # 决策参数配置
        self.risk_weight = 0.4  # 风险权重
        self.reward_weight = 0.6  # 收益权重
        self.decision_threshold = 0.5  # 决策通过阈值

    def generate_decision_options(self, important_info: List[Dict], memory_results: List[Dict]) -> List[Dict]:
        """
        基于输入信息生成可行的决策选项
        :param important_info: 注意力模块筛选出的重要信息
        :param memory_results: 记忆检索的相关结果
        :return: 决策选项列表
        """
        options = []
        # 基于历史记忆生成类似场景的决策
        for memory in memory_results:
            if 'decision' in memory['content']:
                options.append({
                    'option_name': f"历史方案_{memory['content']['id']}",
                    'description': memory['content']['decision']['description'],
                    'estimated_reward': memory['content']['decision'].get('reward', 0.5),
                    'estimated_risk': memory['content']['decision'].get('risk', 0.5),
                    'source': 'history_memory'
                })
        # 基于当前信息生成新的决策选项
        current_info_summary = ' '.join([str(chunk['content']) for chunk in important_info[:3]])
        options.append({
            'option_name': '当前场景适配方案',
            'description': f"基于当前信息定制的决策方案: {current_info_summary[:100]}...",
            'estimated_reward': 0.6,
            'estimated_risk': 0.4,
            'source': 'current_info'
        })
        options.append({
            'option_name': '保守方案',
            'description': '低风险低收益的保守决策方案',
            'estimated_reward': 0.4,
            'estimated_risk': 0.2,
            'source': 'default'
        })
        options.append({
            'option_name': '激进方案',
            'description': '高风险高收益的激进决策方案',
            'estimated_reward': 0.8,
            'estimated_risk': 0.7,
            'source': 'default'
        })
        return options

    def calculate_decision_score(self, option: Dict) -> float:
        """
        计算决策选项的综合得分
        :param option: 决策选项
        :return: 综合得分，0-1
        """
        score = (option['estimated_reward'] * self.reward_weight) - (option['estimated_risk'] * self.risk_weight)
        # 归一化到0-1范围
        normalized_score = max(0.0, min(1.0, score + 0.5))
        return normalized_score

    def select_optimal_decision(self, options: List[Dict]) -> Tuple[Optional[Dict], List[Dict]]:
        """
        选择最优决策
        :param options: 决策选项列表
        :return: (最优决策，带得分的所有选项列表)
        """
        if not options:
            return None, []
        # 为每个选项计算得分
        scored_options = []
        for option in options:
            score = self.calculate_decision_score(option)
            scored_options.append({
                **option,
                'score': score
            })
        # 按得分降序排序
        scored_options.sort(key=lambda x: x['score'], reverse=True)
        # 选择得分最高且超过阈值的选项
        optimal_option = scored_options[0] if scored_options[0]['score'] >= self.decision_threshold else None
        return optimal_option, scored_options

    def adjust_decision_weights(self, feedback: float):
        """
        根据决策效果反馈调整权重，实现决策能力优化
        :param feedback: 决策效果反馈，0-1，越高表示效果越好
        """
        if feedback < 0.3:
            # 决策效果差，提高风险权重
            self.risk_weight = min(0.8, self.risk_weight + 0.1)
            self.reward_weight = max(0.2, self.reward_weight - 0.1)
        elif feedback > 0.8:
            # 决策效果好，提高收益权重
            self.risk_weight = max(0.2, self.risk_weight - 0.1)
            self.reward_weight = min(0.8, self.reward_weight + 0.1)
