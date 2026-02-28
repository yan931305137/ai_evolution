"""
注意力模块：负责分配计算资源到重要的输入信息，过滤无关信息，提升信息处理效率
"""
import math
from typing import List, Dict, Tuple

class AttentionModule:
    def __init__(self):
        # 初始化注意力参数
        self.attention_threshold = 0.6  # 注意力阈值，低于该值的信息会被过滤
        self.context_weight = 0.7  # 上下文相关性权重
        self.task_relevance_weight = 0.3  # 任务相关性权重

    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度，用于评估信息相关性
        :param vec1: 向量1
        :param vec2: 向量2
        :return: 余弦相似度值，范围0-1
        """
        if len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def calculate_attention_weights(self, input_chunks: List[Dict], context_vector: List[float], task_vector: List[float]) -> List[Dict]:
        """
        为输入的信息块计算注意力权重
        :param input_chunks: 输入信息块列表，每个块包含content和embedding字段
        :param context_vector: 上下文向量
        :param task_vector: 当前任务向量
        :return: 带注意力权重的信息块列表
        """
        weighted_chunks = []
        for chunk in input_chunks:
            # 计算上下文相关性得分
            context_score = self.calculate_similarity(chunk['embedding'], context_vector)
            # 计算任务相关性得分
            task_score = self.calculate_similarity(chunk['embedding'], task_vector)
            # 加权求和得到最终注意力权重
            attention_weight = (context_score * self.context_weight) + (task_score * self.task_relevance_weight)
            # 归一化到0-1范围
            attention_weight = max(0.0, min(1.0, attention_weight))
            weighted_chunks.append({
                **chunk,
                'attention_weight': attention_weight,
                'is_important': attention_weight >= self.attention_threshold
            })
        return weighted_chunks

    def filter_important_info(self, weighted_chunks: List[Dict]) -> List[Dict]:
        """
        过滤掉注意力权重低于阈值的无关信息，只保留重要信息
        :param weighted_chunks: 带注意力权重的信息块列表
        :return: 重要信息块列表
        """
        important_chunks = [chunk for chunk in weighted_chunks if chunk['is_important']]
        # 按注意力权重降序排序
        important_chunks.sort(key=lambda x: x['attention_weight'], reverse=True)
        return important_chunks

    def get_top_k_info(self, weighted_chunks: List[Dict], k: int = 5) -> List[Dict]:
        """
        获取关注度最高的前K条信息
        :param weighted_chunks: 带注意力权重的信息块列表
        :param k: 要获取的信息条数
        :return: 前K条重要信息
        """
        sorted_chunks = sorted(weighted_chunks, key=lambda x: x['attention_weight'], reverse=True)
        return sorted_chunks[:k]
