"""
记忆数据工厂

生成各种测试用的记忆数据
"""

import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class MemoryFactory:
    """记忆数据工厂"""
    
    # 预定义的测试记忆模板
    CONVERSATION_TEMPLATES = [
        "用户问：{question}，我回答：{answer}",
        "用户说：{statement}",
        "我们讨论了关于{topic}的内容",
        "用户请求我帮忙{task}",
    ]
    
    KNOWLEDGE_TEMPLATES = [
        "{topic}是一种{category}，主要用于{purpose}",
        "{topic}的核心概念包括{concepts}",
        "使用{topic}时需要注意{notes}",
    ]
    
    EXPERIENCE_TEMPLATES = [
        "成功完成了{task}，使用了{method}",
        "在{context}中遇到了{problem}，通过{solution}解决",
        "学会了{skill}，感觉{feeling}",
    ]
    
    TOPICS = [
        "Python编程", "机器学习", "深度学习", "自然语言处理",
        "数据可视化", "API设计", "代码重构", "测试驱动开发",
        "Git版本控制", "Docker容器化", "CI/CD", "微服务架构"
    ]
    
    EMOTIONS = ["happy", "neutral", "concerned", "excited", "calm"]
    
    @classmethod
    def create_conversation(
        cls,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        topic: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建对话记忆
        
        Args:
            question: 用户问题
            answer: AI回答
            topic: 主题
            **kwargs: 其他元数据
        
        Returns:
            记忆数据字典
        """
        question = question or f"关于{random.choice(cls.TOPICS)}的问题"
        answer = answer or "这是一个测试回答"
        topic = topic or random.choice(cls.TOPICS)
        
        content = random.choice(cls.CONVERSATION_TEMPLATES).format(
            question=question,
            answer=answer,
            statement=question,
            topic=topic,
            task=kwargs.get('task', '完成某项任务')
        )
        
        return {
            "content": content,
            "type": "conversation",
            "importance": kwargs.get('importance', random.uniform(0.5, 0.9)),
            "emotional_tag": kwargs.get('emotion', random.choice(cls.EMOTIONS)),
            "metadata": {
                "source": kwargs.get('source', 'user'),
                "timestamp": kwargs.get('timestamp', time.time()),
                "topic": topic,
                **kwargs.get('extra_meta', {})
            }
        }
    
    @classmethod
    def create_knowledge(
        cls,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建知识记忆"""
        topic = topic or random.choice(cls.TOPICS)
        category = category or "技术知识"
        
        content = random.choice(cls.KNOWLEDGE_TEMPLATES).format(
            topic=topic,
            category=category,
            purpose=kwargs.get('purpose', '解决实际问题'),
            concepts=kwargs.get('concepts', '核心概念A, 核心概念B'),
            notes=kwargs.get('notes', '注意事项')
        )
        
        return {
            "content": content,
            "type": "knowledge",
            "importance": kwargs.get('importance', random.uniform(0.6, 0.95)),
            "emotional_tag": "neutral",
            "metadata": {
                "source": kwargs.get('source', 'learning'),
                "timestamp": kwargs.get('timestamp', time.time()),
                "topic": topic,
                "category": category,
                **kwargs.get('extra_meta', {})
            }
        }
    
    @classmethod
    def create_experience(
        cls,
        task: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建经验记忆"""
        task = task or f"完成{random.choice(cls.TOPICS)}相关任务"
        
        content = random.choice(cls.EXPERIENCE_TEMPLATES).format(
            task=task,
            method=kwargs.get('method', '最佳实践方法'),
            context=kwargs.get('context', '项目开发'),
            problem=kwargs.get('problem', '技术难题'),
            solution=kwargs.get('solution', '创新解决方案'),
            skill=kwargs.get('skill', '新技能'),
            feeling=kwargs.get('feeling', '收获很大')
        )
        
        return {
            "content": content,
            "type": "experience",
            "importance": kwargs.get('importance', random.uniform(0.7, 1.0)),
            "emotional_tag": kwargs.get('emotion', 'accomplished'),
            "metadata": {
                "source": kwargs.get('source', 'experience'),
                "timestamp": kwargs.get('timestamp', time.time()),
                "outcome": kwargs.get('outcome', 'success'),
                **kwargs.get('extra_meta', {})
            }
        }
    
    @classmethod
    def create_batch(
        cls,
        count: int = 10,
        memory_type: str = "mixed",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量创建记忆
        
        Args:
            count: 数量
            memory_type: 类型 (conversation/knowledge/experience/mixed)
            **kwargs: 传递给具体创建方法的参数
        
        Returns:
            记忆数据列表
        """
        memories = []
        creators = {
            "conversation": cls.create_conversation,
            "knowledge": cls.create_knowledge,
            "experience": cls.create_experience,
        }
        
        for i in range(count):
            if memory_type == "mixed":
                creator = random.choice(list(creators.values()))
            else:
                creator = creators.get(memory_type, cls.create_conversation)
            
            memory = creator(**kwargs)
            memory['id'] = f"test_memory_{i}"
            memories.append(memory)
        
        return memories
    
    @classmethod
    def create_time_series(
        cls,
        count: int = 10,
        days_span: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        创建时间序列记忆
        
        Args:
            count: 记忆数量
            days_span: 时间跨度（天）
            **kwargs: 其他参数
        
        Returns:
            按时间排序的记忆列表
        """
        memories = []
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_span)
        
        for i in range(count):
            # 在时间范围内随机选择时间点
            random_days = random.randint(0, days_span)
            random_hours = random.randint(0, 23)
            timestamp = (start_time + timedelta(days=random_days, hours=random_hours)).timestamp()
            
            memory = cls.create_conversation(
                timestamp=timestamp,
                **kwargs
            )
            memory['id'] = f"time_series_{i}"
            memories.append(memory)
        
        # 按时间排序
        memories.sort(key=lambda x: x['metadata']['timestamp'])
        return memories
