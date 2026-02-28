#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回答透明度管理模块
功能：实现AI回答的全链路溯源、置信度评估、事实核查路径记录，为可信体系提供核心支撑
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from src.utils.source_evaluator import source_evaluator

logger = logging.getLogger(__name__)

@dataclass
class SourceInfo:
    """信息来源数据结构"""
    source_type: str  # 来源类型：knowledge_base(知识库)/web_search(网页搜索)/memory(历史记忆)/user_input(用户输入)/model_inference(模型推理)
    source_id: str  # 来源唯一标识
    source_content: str  # 来源内容片段
    reliability_score: float  # 来源可靠性评分0-1
    retrieval_time: datetime = None

    def __post_init__(self):
        if self.retrieval_time is None:
            self.retrieval_time = datetime.now()

@dataclass
class FactCheckStep:
    """事实核查步骤数据结构"""
    step_id: str
    step_name: str
    step_description: str
    check_result: str  # pass/fail/pending
    evidence: Optional[str] = None
    check_time: datetime = None

    def __post_init__(self):
        if self.check_time is None:
            self.check_time = datetime.now()

@dataclass
class AnswerTransparencyData:
    """回答全量透明度数据结构"""
    answer_id: str
    query: str
    answer_content: str
    confidence_score: float  # 整体置信度0-1
    sources: List[SourceInfo]
    fact_check_steps: List[FactCheckStep]
    create_time: datetime = None
    update_time: datetime = None

    def __post_init__(self):
        if self.create_time is None:
            self.create_time = datetime.now()
        if self.update_time is None:
            self.update_time = datetime.now()

class AnswerTransparencyManager:
    """回答透明度管理核心类"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        # 透明度数据存储，后续可对接数据库持久化
        self.transparency_data_store: Dict[str, AnswerTransparencyData] = {}
        logger.info("回答透明度管理模块初始化完成")

    def calculate_confidence_score(self, sources: List[SourceInfo], fact_check_steps: List[FactCheckStep]) -> float:
        """
        计算回答整体置信度评分
        规则：
        1. 来源可靠性占比60%
        2. 事实核查通过率占比40%
        """
        if not sources:
            source_score = 0.3  # 无来源时最低基础分
        else:
            source_score = sum(s.reliability_score for s in sources) / len(sources)
        
        if not fact_check_steps:
            check_score = 0.5  # 无核查步骤时中等基础分
        else:
            passed_checks = len([s for s in fact_check_steps if s.check_result == 'pass'])
            check_score = passed_checks / len(fact_check_steps)
        
        total_score = source_score * 0.6 + check_score * 0.4
        return round(total_score, 2)

    def record_answer_data(self, answer_id: str, query: str, answer_content: str, 
                          sources: List[Dict], fact_check_steps: List[Dict]) -> AnswerTransparencyData:
        """
        记录回答的全量透明度数据
        :param answer_id: 回答唯一ID
        :param query: 用户原始问题
        :param answer_content: 生成的回答内容
        :param sources: 信息来源列表，字典格式
        :param fact_check_steps: 事实核查步骤列表，字典格式
        :return: 透明度数据对象
        """
        # 转换来源数据结构
        source_objs = []
        for s in sources:
            # 自动评估来源可靠性
            if 'reliability_score' not in s:
                s['reliability_score'] = source_evaluator.evaluate_reliability(s['source_type'], s.get('source_content', ''))
            source_objs.append(SourceInfo(**s))
        
        # 转换核查步骤数据结构
        check_objs = [FactCheckStep(**step) for step in fact_check_steps]
        
        # 计算置信度
        confidence = self.calculate_confidence_score(source_objs, check_objs)
        
        # 构建透明度数据
        transparency_data = AnswerTransparencyData(
            answer_id=answer_id,
            query=query,
            answer_content=answer_content,
            confidence_score=confidence,
            sources=source_objs,
            fact_check_steps=check_objs
        )
        
        # 存储数据
        self.transparency_data_store[answer_id] = transparency_data
        logger.info(f"回答{answer_id}透明度数据已记录，置信度：{confidence}")
        
        return transparency_data

    def get_transparency_data(self, answer_id: str) -> Optional[Dict]:
        """
        获取指定回答的透明度数据，返回可公开的结构化数据
        :param answer_id: 回答唯一ID
        :return: 透明度公开数据字典
        """
        data = self.transparency_data_store.get(answer_id)
        if not data:
            return None
        
        # 转换为可公开的格式，脱敏处理
        public_data = asdict(data)
        # 转换时间为字符串
        public_data['create_time'] = public_data['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        public_data['update_time'] = public_data['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        for s in public_data['sources']:
            s['retrieval_time'] = s['retrieval_time'].strftime('%Y-%m-%d %H:%M:%S')
        for step in public_data['fact_check_steps']:
            step['check_time'] = step['check_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return public_data

    def generate_transparency_display(self, answer_id: str) -> str:
        """
        生成用户可见的透明度展示内容
        :param answer_id: 回答唯一ID
        :return: 格式化后的透明度展示文本
        """
        data = self.get_transparency_data(answer_id)
        if not data:
            return "\n⚠️ 暂无透明度信息"
        
        display = "\n" + "="*50 + "\n"
        display += "📊 回答透明度说明\n"
        display += "="*50 + "\n"
        display += f"🔍 回答置信度：{data['confidence_score']*100}%\n"
        display += "\n📚 信息来源：\n"
        for idx, source in enumerate(data['sources'], 1):
            type_name = {
                'knowledge_base': '官方知识库',
                'web_search': '权威网页搜索',
                'memory': '历史可信对话',
                'user_input': '用户提供信息',
                'model_inference': '模型逻辑推理'
            }.get(source['source_type'], source['source_type'])
            display += f"{idx}. [{type_name}] 可靠性：{source['reliability_score']*100}%\n"
        
        display += "\n✅ 事实核查路径：\n"
        for idx, step in enumerate(data['fact_check_steps'], 1):
            status = "✅ 通过" if step['check_result'] == 'pass' else "❌ 未通过" if step['check_result'] == 'fail' else "⏳ 待核查"
            display += f"{idx}. {step['step_name']}：{status}\n"
            if step.get('evidence'):
                display += f"   核查依据：{step['evidence']}\n"
        
        display += "="*50 + "\n"
        return display

# 全局单例实例
answer_transparency_manager = AnswerTransparencyManager()
