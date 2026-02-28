#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感知系统 (Perception System)
对应人脑: 枕叶 (Occipital Lobe) + 颞叶 (Temporal Lobe) + 丘脑 (Thalamus)

核心功能:
1. 多模态输入处理 - 文本、图像、音频、结构化数据
2. 特征提取 - 从原始输入中提取有意义的特征
3. 模式识别 - 识别输入中的模式和结构
4. 跨模态融合 - 整合不同模态的信息
5. 感知编码 - 将感知信息编码为大脑可用的表示
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.brain.common import BrainModule, BrainRegion, PerceptionInput


class ModalityType(Enum):
    """模态类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    STRUCTURED = "structured"
    CODE = "code"
    MIXED = "mixed"


@dataclass
class FeatureVector:
    """特征向量"""
    modality: ModalityType
    features: Dict[str, Any]
    confidence: float
    raw_input_id: str


@dataclass
class Pattern:
    """识别出的模式"""
    pattern_type: str
    content: Any
    confidence: float
    supporting_evidence: List[str]


class PerceptionSystem(BrainModule):
    """
    感知系统
    模拟枕叶/颞叶的感觉处理功能
    """
    
    def __init__(self, enable_pattern_cache: bool = True):
        super().__init__("PerceptionSystem", BrainRegion.OCCIPITAL_TEMPORAL)
        
        self.enable_pattern_cache = enable_pattern_cache
        self.pattern_cache: Dict[str, Pattern] = {}
        
        # 模态处理器注册表
        self.processors: Dict[ModalityType, callable] = {
            ModalityType.TEXT: self._process_text,
            ModalityType.CODE: self._process_code,
            ModalityType.STRUCTURED: self._process_structured,
            ModalityType.IMAGE: self._process_image_stub,  # 占位
            ModalityType.AUDIO: self._process_audio_stub,  # 占位
        }
        
        # 已学习模式
        self.learned_patterns: Dict[str, List[Pattern]] = {}
        
    def detect_modality(self, input_data: Any) -> ModalityType:
        """
        自动检测输入模态类型
        
        Args:
            input_data: 原始输入
            
        Returns:
            模态类型
        """
        if isinstance(input_data, str):
            # 检查是否为代码
            code_indicators = [
                r'def\s+\w+\s*\(',  # Python函数
                r'function\s+\w+',  # JS函数
                r'class\s+\w+',     # 类定义
                r'import\s+\w+',    # 导入
                r'#include',        # C头文件
                r'<\?php',          # PHP
            ]
            
            for pattern in code_indicators:
                if re.search(pattern, input_data, re.IGNORECASE):
                    return ModalityType.CODE
                    
            return ModalityType.TEXT
            
        elif isinstance(input_data, dict):
            return ModalityType.STRUCTURED
            
        elif isinstance(input_data, list):
            # 列表可能包含多种模态
            return ModalityType.MIXED
            
        elif isinstance(input_data, bytes):
            # 可能是图像/音频二进制
            return ModalityType.MIXED
            
        return ModalityType.STRUCTURED
    
    def process_input(self, input_data: Any, 
                     modality_hint: Optional[ModalityType] = None) -> PerceptionInput:
        """
        处理感知输入
        
        主入口: 接收原始输入，输出结构化感知表示
        
        Args:
            input_data: 原始输入数据
            modality_hint: 模态提示（可选）
            
        Returns:
            PerceptionInput: 结构化感知输入
        """
        # 检测模态
        modality = modality_hint or self.detect_modality(input_data)
        
        # 统一转换为列表处理
        if modality == ModalityType.MIXED:
            items = input_data if isinstance(input_data, list) else [input_data]
            results = []
            for item in items:
                item_modality = self.detect_modality(item)
                processor = self.processors.get(item_modality, self._process_text)
                results.append(processor(item))
            # 合并结果
            combined = self._merge_results(results)
            return self._build_perception_input(combined, ModalityType.MIXED)
        else:
            processor = self.processors.get(modality, self._process_text)
            features = processor(input_data)
            return self._build_perception_input(features, modality)
    
    def _process_text(self, text: str) -> FeatureVector:
        """处理文本输入"""
        features = {
            "length": len(text),
            "word_count": len(text.split()),
            "sentences": text.count('.') + text.count('!') + text.count('?'),
            "has_questions": '?' in text,
            "has_commands": any(cmd in text.lower() for cmd in ['请', '帮忙', '帮我', 'please', 'help']),
            "emotional_markers": self._extract_emotional_markers(text),
            "entities": self._extract_entities(text),
            "topics": self._extract_topics(text),
            "complexity_score": len(set(text.split())) / max(len(text.split()), 1)
        }
        
        confidence = 0.9  # 文本处理置信度较高
        
        return FeatureVector(
            modality=ModalityType.TEXT,
            features=features,
            confidence=confidence,
            raw_input_id=str(hash(text))[:8]
        )
    
    def _process_code(self, code: str) -> FeatureVector:
        """处理代码输入"""
        features = {
            "language": self._detect_language(code),
            "lines": len(code.split('\n')),
            "functions": len(re.findall(r'def\s+\w+|function\s+\w+', code)),
            "classes": len(re.findall(r'class\s+\w+', code)),
            "imports": re.findall(r'(?:import|from|require)\s+(\w+)', code),
            "complexity_indicators": {
                "loops": len(re.findall(r'\b(for|while)\b', code)),
                "conditionals": len(re.findall(r'\b(if|else|elif)\b', code)),
                "comments": len(re.findall(r'#|//|/\*', code))
            },
            "has_errors": self._detect_syntax_issues(code)
        }
        
        return FeatureVector(
            modality=ModalityType.CODE,
            features=features,
            confidence=0.85,
            raw_input_id=str(hash(code))[:8]
        )
    
    def _process_structured(self, data: Dict) -> FeatureVector:
        """处理结构化数据"""
        features = {
            "keys": list(data.keys()),
            "depth": self._calculate_depth(data),
            "size": len(str(data)),
            "types": {k: type(v).__name__ for k, v in data.items()},
            "has_nested": any(isinstance(v, (dict, list)) for v in data.values())
        }
        
        return FeatureVector(
            modality=ModalityType.STRUCTURED,
            features=features,
            confidence=0.95,
            raw_input_id=str(hash(str(data)))[:8]
        )
    
    def _process_image_stub(self, image_data: bytes) -> FeatureVector:
        """图像处理占位 (需要实际的CV库)"""
        return FeatureVector(
            modality=ModalityType.IMAGE,
            features={"size": len(image_data), "stub": True},
            confidence=0.5,
            raw_input_id=str(hash(image_data))[:8]
        )
    
    def _process_audio_stub(self, audio_data: bytes) -> FeatureVector:
        """音频处理占位 (需要实际的ASR库)"""
        return FeatureVector(
            modality=ModalityType.AUDIO,
            features={"size": len(audio_data), "stub": True},
            confidence=0.5,
            raw_input_id=str(hash(audio_data))[:8]
        )
    
    def recognize_patterns(self, perception: PerceptionInput) -> List[Pattern]:
        """
        模式识别
        
        从感知输入中识别已知模式
        
        Args:
            perception: 感知输入
            
        Returns:
            识别出的模式列表
        """
        patterns = []
        
        # 基于内容类型识别模式
        content = perception.content
        
        # 意图模式
        intent_pattern = self._recognize_intent(content)
        if intent_pattern:
            patterns.append(intent_pattern)
            
        # 实体模式
        entity_pattern = self._recognize_entities(content)
        if entity_pattern:
            patterns.append(entity_pattern)
            
        # 任务模式
        task_pattern = self._recognize_task_pattern(content)
        if task_pattern:
            patterns.append(task_pattern)
            
        # 情感模式
        emotion_pattern = self._recognize_emotion(content)
        if emotion_pattern:
            patterns.append(emotion_pattern)
            
        return patterns
    
    def cross_modal_fusion(self, perceptions: List[PerceptionInput]) -> PerceptionInput:
        """
        跨模态融合
        
        整合来自不同模态的信息
        
        Args:
            perceptions: 多模态感知列表
            
        Returns:
            融合后的感知
        """
        # 提取各模态的关键信息
        fused_content = {
            "modalities": [p.modality for p in perceptions],
            "text_summary": None,
            "key_entities": [],
            "confidence": 0.0
        }
        
        for p in perceptions:
            if p.modality == "text":
                fused_content["text_summary"] = p.content.get("text", "")[:200]
            elif p.modality == "structured":
                fused_content["key_entities"].extend(p.content.get("keys", []))
                
        # 计算平均置信度
        confidences = [p.confidence for p in perceptions]
        fused_content["confidence"] = sum(confidences) / len(confidences)
        
        return PerceptionInput(
            modality="fused",
            content=fused_content,
            confidence=fused_content["confidence"],
            timestamp=datetime.now(),
            metadata={"source_modalities": len(perceptions)}
        )
    
    def _build_perception_input(self, features: FeatureVector, 
                               modality: ModalityType) -> PerceptionInput:
        """构建感知输入对象"""
        return PerceptionInput(
            modality=modality.value,
            content=features.features,
            confidence=features.confidence,
            timestamp=datetime.now(),
            metadata={
                "raw_id": features.raw_input_id,
                "processor_version": "1.0"
            }
        )
    
    def _extract_emotional_markers(self, text: str) -> Dict[str, float]:
        """提取情感标记"""
        markers = {
            "urgent": 0.0,
            "frustrated": 0.0,
            "happy": 0.0,
            "confused": 0.0
        }
        
        urgent_words = ['urgent', 'asap', 'immediately', '紧急', '马上', '立即']
        frustrated_words = ['annoying', 'stupid', 'bad', 'terrible', '糟糕', '烦人']
        happy_words = ['great', 'awesome', 'thanks', 'good', '棒', '谢谢']
        confused_words = ['confused', 'don\'t understand', 'unclear', '不明白', '不懂']
        
        text_lower = text.lower()
        for word in urgent_words:
            if word in text_lower:
                markers["urgent"] += 0.3
        for word in frustrated_words:
            if word in text_lower:
                markers["frustrated"] += 0.3
        for word in happy_words:
            if word in text_lower:
                markers["happy"] += 0.3
        for word in confused_words:
            if word in text_lower:
                markers["confused"] += 0.3
                
        return {k: min(1.0, v) for k, v in markers.items()}
    
    def _extract_entities(self, text: str) -> List[str]:
        """简单实体提取"""
        # 大写词可能是专有名词
        entities = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        # 带引号的字符串
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        return list(set(entities + quoted))
    
    def _extract_topics(self, text: str) -> List[str]:
        """主题提取"""
        # 基于关键词匹配
        topic_keywords = {
            "programming": ["code", "function", "class", "bug", "error", "debug"],
            "writing": ["write", "text", "document", "article", "content"],
            "data": ["data", "database", "query", "table", "record"],
            "design": ["design", "ui", "ux", "interface", "layout"]
        }
        
        text_lower = text.lower()
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_topics.append(topic)
                
        return found_topics
    
    def _detect_language(self, code: str) -> str:
        """检测编程语言"""
        if 'def ' in code and ':' in code:
            return "python"
        elif 'function' in code or 'const' in code or 'let' in code:
            return "javascript"
        elif '#include' in code:
            return "c/c++"
        elif '<?php' in code:
            return "php"
        elif 'import' in code and 'class' in code:
            return "java"
        return "unknown"
    
    def _detect_syntax_issues(self, code: str) -> List[str]:
        """简单语法问题检测"""
        issues = []
        # 括号不匹配
        if code.count('(') != code.count(')'):
            issues.append("unbalanced_parentheses")
        if code.count('{') != code.count('}'):
            issues.append("unbalanced_braces")
        if code.count('[') != code.count(']'):
            issues.append("unbalanced_brackets")
        return issues
    
    def _calculate_depth(self, data: Any, current_depth: int = 0) -> int:
        """计算嵌套深度"""
        if not isinstance(data, dict):
            return current_depth
        if not data:
            return current_depth
        max_depth = current_depth
        for v in data.values():
            if isinstance(v, dict):
                max_depth = max(max_depth, self._calculate_depth(v, current_depth + 1))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        max_depth = max(max_depth, self._calculate_depth(item, current_depth + 1))
        return max_depth
    
    def _merge_results(self, results: List[FeatureVector]) -> FeatureVector:
        """合并多模态结果"""
        merged_features = {}
        for r in results:
            merged_features[r.modality.value] = r.features
            
        return FeatureVector(
            modality=ModalityType.MIXED,
            features=merged_features,
            confidence=sum(r.confidence for r in results) / len(results),
            raw_input_id="merged"
        )
    
    def _recognize_intent(self, content: Dict) -> Optional[Pattern]:
        """识别意图模式"""
        # 基于关键词识别意图
        intent_patterns = {
            "create": ["create", "make", "build", "generate", "write", "创建", "生成"],
            "read": ["read", "get", "fetch", "show", "查看", "显示"],
            "update": ["update", "modify", "change", "edit", "修改", "更新"],
            "delete": ["delete", "remove", "clear", "删除", "清除"],
            "analyze": ["analyze", "check", "review", "分析", "检查"]
        }
        
        text = str(content)
        text_lower = text.lower()
        
        for intent, keywords in intent_patterns.items():
            if any(kw in text_lower for kw in keywords):
                return Pattern(
                    pattern_type="intent",
                    content=intent,
                    confidence=0.7,
                    supporting_evidence=[f"keyword: {kw}" for kw in keywords if kw in text_lower]
                )
        return None
    
    def _recognize_entities(self, content: Dict) -> Optional[Pattern]:
        """识别实体模式"""
        entities = content.get("entities", [])
        if entities:
            return Pattern(
                pattern_type="entities",
                content=entities,
                confidence=0.8,
                supporting_evidence=["extracted_entities"]
            )
        return None
    
    def _recognize_task_pattern(self, content: Dict) -> Optional[Pattern]:
        """识别任务模式"""
        # 检查是否有明确的任务结构
        has_goal = any(kw in str(content).lower() for kw in ["goal", "objective", "task", "目标", "任务"])
        has_steps = any(kw in str(content).lower() for kw in ["step", "process", "flow", "步骤"])
        
        if has_goal and has_steps:
            return Pattern(
                pattern_type="task_structure",
                content={"has_goal": True, "has_steps": True},
                confidence=0.75,
                supporting_evidence=["goal_keywords", "step_keywords"]
            )
        return None
    
    def _recognize_emotion(self, content: Dict) -> Optional[Pattern]:
        """识别情感模式"""
        markers = content.get("emotional_markers", {})
        if markers and any(v > 0.3 for v in markers.values()):
            dominant_emotion = max(markers.items(), key=lambda x: x[1])
            return Pattern(
                pattern_type="emotion",
                content={
                    "dominant": dominant_emotion[0],
                    "intensity": dominant_emotion[1],
                    "all_markers": markers
                },
                confidence=dominant_emotion[1],
                supporting_evidence=[f"{k}:{v:.2f}" for k, v in markers.items() if v > 0]
            )
        return None
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """统一处理接口"""
        modality_hint = None
        if context and "modality" in context:
            try:
                modality_hint = ModalityType(context["modality"])
            except ValueError:
                pass
                
        perception = self.process_input(input_data, modality_hint)
        patterns = self.recognize_patterns(perception)
        
        return {
            "modality": perception.modality,
            "features": perception.content,
            "confidence": perception.confidence,
            "patterns": [
                {"type": p.pattern_type, "content": p.content, "confidence": p.confidence}
                for p in patterns
            ],
            "pattern_count": len(patterns)
        }
    
    def get_state(self) -> Dict:
        """获取系统状态"""
        return {
            "activation": self.activation_level,
            "supported_modalities": [m.value for m in self.processors.keys()],
            "learned_patterns": {k: len(v) for k, v in self.learned_patterns.items()}
        }


# 导出
__all__ = ['PerceptionSystem', 'ModalityType', 'FeatureVector', 'Pattern']
