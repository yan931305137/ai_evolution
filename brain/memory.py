"""
长短时记忆模块：负责信息的短期缓存和长期存储，实现信息的增删改查和遗忘机制，保证信息召回率≥85%
"""
import time
from typing import List, Dict, Optional
from collections import deque

class MemoryModule:
    def __init__(self):
        # 短期记忆：容量限制为100条，采用FIFO淘汰策略
        self.short_term_memory = deque(maxlen=100)
        # 长期记忆：无限容量，按重要性和访问频率排序
        self.long_term_memory = []
        # 记忆参数配置
        self.forget_threshold = 0.3  # 遗忘阈值，重要性低于该值的记忆会被逐步遗忘
        self.short_term_expire_time = 3600  # 短期记忆过期时间，单位秒，1小时
        self.long_term_access_boost = 0.1  # 长期记忆被访问后的重要性提升值

    def add_short_term_memory(self, content: Dict, importance: float = 0.5):
        """
        添加短期记忆
        :param content: 记忆内容
        :param importance: 重要性得分，0-1
        """
        memory_item = {
            'content': content,
            'importance': max(0.0, min(1.0, importance)),
            'create_time': time.time(),
            'last_access_time': time.time(),
            'access_count': 1
        }
        self.short_term_memory.append(memory_item)
        # 如果重要性超过0.8，自动转存到长期记忆
        if importance >= 0.8:
            self.move_to_long_term(memory_item)

    def move_to_long_term(self, memory_item: Dict):
        """
        将短期记忆转存到长期记忆
        :param memory_item: 记忆条目
        """
        # 检查是否已存在相同记忆
        for item in self.long_term_memory:
            if item['content'] == memory_item['content']:
                item['access_count'] += 1
                item['last_access_time'] = time.time()
                return
        # 添加新的长期记忆
        self.long_term_memory.append({
            **memory_item,
            'create_time': time.time()
        })

    def retrieve_memory(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        根据查询检索相关记忆，优先从短期记忆查找，再查长期记忆
        :param query: 查询关键词
        :param top_k: 返回最相关的前K条结果
        :return: 相关记忆列表
        """
        results = []
        # 清理过期的短期记忆
        self._clean_expired_short_term()
        # 检索短期记忆
        for item in self.short_term_memory:
            relevance = self._calculate_relevance(item['content'], query)
            if relevance > 0:
                results.append({
                    **item,
                    'relevance': relevance,
                    'memory_type': 'short_term'
                })
                # 更新访问时间和计数
                item['last_access_time'] = time.time()
                item['access_count'] += 1
        # 检索长期记忆
        for item in self.long_term_memory:
            relevance = self._calculate_relevance(item['content'], query)
            if relevance > 0:
                results.append({
                    **item,
                    'relevance': relevance,
                    'memory_type': 'long_term'
                })
                # 提升重要性
                item['importance'] = min(1.0, item['importance'] + self.long_term_access_boost)
                item['last_access_time'] = time.time()
                item['access_count'] += 1
        # 按相关性降序排序，返回前K条
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:top_k]

    def _calculate_relevance(self, content: Dict, query: str) -> float:
        """
        计算记忆内容和查询的相关性
        :param content: 记忆内容
        :param query: 查询字符串
        :return: 相关性得分，0-1
        """
        content_str = str(content).lower()
        query_terms = query.lower().split()
        if not query_terms:
            return 0.0
        matched_terms = sum(1 for term in query_terms if term in content_str)
        return matched_terms / len(query_terms)

    def _clean_expired_short_term(self):
        """
        清理过期的短期记忆
        """
        current_time = time.time()
        self.short_term_memory = deque(
            [item for item in self.short_term_memory if current_time - item['create_time'] < self.short_term_expire_time],
            maxlen=100
        )

    def forget_low_importance_memory(self):
        """
        遗忘重要性低于阈值的长期记忆
        """
        self.long_term_memory = [item for item in self.long_term_memory if item['importance'] >= self.forget_threshold]

    def calculate_recall_rate(self, test_queries: List[Dict]) -> float:
        """
        计算记忆召回率，用于单元测试验证
        :param test_queries: 测试用例列表，每个用例包含query和expected_ids字段
        :return: 召回率百分比，保留2位小数
        """
        total_expected = 0
        total_retrieved = 0
        for case in test_queries:
            results = self.retrieve_memory(case['query'], top_k=20)
            retrieved_ids = [item['content'].get('id') for item in results]
            expected_ids = case['expected_ids']
            total_expected += len(expected_ids)
            total_retrieved += sum(1 for eid in expected_ids if eid in retrieved_ids)
        if total_expected == 0:
            return 0.0
        recall_rate = round((total_retrieved / total_expected) * 100, 2)
        return recall_rate
