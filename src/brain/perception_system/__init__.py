#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感知系统 - 完整版 (P0-1 修复)

修复内容:
1. 补全图像特征提取方法 (_process_image)
2. 补全音频特征提取方法 (_process_audio)
3. 增强文本和代码特征提取
"""

import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import base64

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
    感知系统 (完整版)
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
            ModalityType.IMAGE: self._process_image,  # 已补全
            ModalityType.AUDIO: self._process_audio,  # 已补全
        }
        
        # 已学习模式
        self.learned_patterns: Dict[str, List[Pattern]] = {}
        
        # 特征提取统计
        self.feature_stats = {
            "processed_count": 0,
            "by_modality": {m.value: 0 for m in ModalityType}
        }
        
    def detect_modality(self, input_data: Any) -> ModalityType:
        """自动检测输入模态类型"""
        if isinstance(input_data, str):
            code_indicators = [
                r'def\s+\w+\s*\(',
                r'function\s+\w+',
                r'class\s+\w+',
                r'import\s+\w+',
                r'#include',
                r'<\?php',
            ]
            
            for pattern in code_indicators:
                if re.search(pattern, input_data, re.IGNORECASE):
                    return ModalityType.CODE
                    
            return ModalityType.TEXT
            
        elif isinstance(input_data, dict):
            return ModalityType.STRUCTURED
            
        elif isinstance(input_data, list):
            return ModalityType.MIXED
            
        elif isinstance(input_data, bytes):
            # 检测是图像还是音频
            header = input_data[:20]
            if self._is_image_header(header):
                return ModalityType.IMAGE
            elif self._is_audio_header(header):
                return ModalityType.AUDIO
            return ModalityType.MIXED
            
        return ModalityType.STRUCTURED
    
    def _is_image_header(self, header: bytes) -> bool:
        """检测是否为图像文件头"""
        image_signatures = [
            b'\xff\xd8\xff',      # JPEG
            b'\x89PNG',           # PNG
            b'GIF87a', b'GIF89a', # GIF
            b'BM',                # BMP
        ]
        # WEBP: RIFF + WEBP (需要更多字节判断)
        if header.startswith(b'RIFF') and len(header) >= 12:
            return header[8:12] == b'WEBP'
        return any(header.startswith(sig) for sig in image_signatures)
    
    def _is_audio_header(self, header: bytes) -> bool:
        """检测是否为音频文件头"""
        audio_signatures = [
            b'ID3',               # MP3
            b'OggS',              # OGG
            b'fLaC',              # FLAC
        ]
        # WAV: RIFF + WAVE (需要更多字节判断)
        if header.startswith(b'RIFF') and len(header) >= 12:
            return header[8:12] == b'WAVE'
        return any(header.startswith(sig) for sig in audio_signatures)
    
    def process_input(self, input_data: Any, 
                     modality_hint: Optional[ModalityType] = None) -> PerceptionInput:
        """处理感知输入"""
        modality = modality_hint or self.detect_modality(input_data)
        
        if modality == ModalityType.MIXED:
            items = input_data if isinstance(input_data, list) else [input_data]
            results = []
            for item in items:
                item_modality = self.detect_modality(item)
                processor = self.processors.get(item_modality, self._process_text)
                results.append(processor(item))
            combined = self._merge_results(results)
            return self._build_perception_input(combined, ModalityType.MIXED)
        else:
            processor = self.processors.get(modality, self._process_text)
            features = processor(input_data)
            return self._build_perception_input(features, modality)
    
    def _process_text(self, text: str) -> FeatureVector:
        """处理文本输入 (增强版)"""
        # 基础统计特征
        features = {
            "length": len(text),
            "word_count": len(text.split()),
            "sentences": text.count('.') + text.count('!') + text.count('?'),
            "has_questions": '?' in text,
            "has_commands": any(cmd in text.lower() for cmd in ['请', '帮忙', '帮我', 'please', 'help']),
            "emotional_markers": self._extract_emotional_markers(text),
            "entities": self._extract_entities(text),
            "topics": self._extract_topics(text),
            "complexity_score": len(set(text.split())) / max(len(text.split()), 1),
            # 新增特征
            "readability_score": self._calculate_readability(text),
            "sentiment_polarity": self._analyze_sentiment(text),
            "key_phrases": self._extract_key_phrases(text),
            "language_detected": self._detect_language_text(text),
        }
        
        self.feature_stats["processed_count"] += 1
        self.feature_stats["by_modality"]["text"] += 1
        
        return FeatureVector(
            modality=ModalityType.TEXT,
            features=features,
            confidence=0.92,
            raw_input_id=self._generate_content_id(text)
        )
    
    def _process_code(self, code: str) -> FeatureVector:
        """处理代码输入 (增强版)"""
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
            "has_errors": self._detect_syntax_issues(code),
            # 新增特征
            "code_quality_score": self._assess_code_quality(code),
            "function_complexity": self._analyze_function_complexity(code),
            "dependencies": self._extract_dependencies(code),
            "documentation_ratio": self._calculate_doc_ratio(code),
        }
        
        self.feature_stats["processed_count"] += 1
        self.feature_stats["by_modality"]["code"] += 1
        
        return FeatureVector(
            modality=ModalityType.CODE,
            features=features,
            confidence=0.88,
            raw_input_id=self._generate_content_id(code)
        )
    
    def _process_structured(self, data: Dict) -> FeatureVector:
        """处理结构化数据"""
        features = {
            "keys": list(data.keys()),
            "depth": self._calculate_depth(data),
            "size": len(str(data)),
            "types": {k: type(v).__name__ for k, v in data.items()},
            "has_nested": any(isinstance(v, (dict, list)) for v in data.values()),
            "schema_summary": self._infer_schema(data),
        }
        
        self.feature_stats["processed_count"] += 1
        self.feature_stats["by_modality"]["structured"] += 1
        
        return FeatureVector(
            modality=ModalityType.STRUCTURED,
            features=features,
            confidence=0.95,
            raw_input_id=self._generate_content_id(str(data))
        )
    
    def _process_image(self, image_data: bytes) -> FeatureVector:
        """
        图像特征提取 (P0-1 修复 - 补全实现)
        
        提取基础图像特征，无需依赖外部CV库
        """
        features = {
            "size_bytes": len(image_data),
            "format": self._detect_image_format(image_data),
            "dimensions": self._estimate_image_dimensions(image_data),
            "color_info": self._extract_color_info(image_data),
            "is_valid": len(image_data) > 100,  # 基础有效性检查
        }
        
        # 尝试提取更详细的特征
        try:
            features.update(self._extract_image_metadata(image_data))
        except Exception:
            pass
        
        self.feature_stats["processed_count"] += 1
        self.feature_stats["by_modality"]["image"] += 1
        
        return FeatureVector(
            modality=ModalityType.IMAGE,
            features=features,
            confidence=0.75,
            raw_input_id=self._generate_content_id(image_data)
        )
    
    def _detect_image_format(self, data: bytes) -> str:
        """检测图像格式"""
        if data.startswith(b'\xff\xd8\xff'):
            return "jpeg"
        elif data.startswith(b'\x89PNG'):
            return "png"
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return "gif"
        elif data.startswith(b'BM'):
            return "bmp"
        elif data.startswith(b'RIFF') and b'WEBP' in data[:20]:
            return "webp"
        return "unknown"
    
    def _estimate_image_dimensions(self, data: bytes) -> Optional[Dict]:
        """估算图像尺寸"""
        try:
            format_type = self._detect_image_format(data)
            
            if format_type == "png":
                # PNG 尺寸在 IHDR chunk 中
                if len(data) >= 24:
                    width = int.from_bytes(data[16:20], 'big')
                    height = int.from_bytes(data[20:24], 'big')
                    return {"width": width, "height": height}
                    
            elif format_type == "jpeg":
                # 简化处理：JPEG 尺寸解析较复杂
                return {"width": None, "height": None, "note": "requires_full_parser"}
                
            elif format_type == "gif":
                if len(data) >= 10:
                    width = int.from_bytes(data[6:8], 'little')
                    height = int.from_bytes(data[8:10], 'little')
                    return {"width": width, "height": height}
                    
        except Exception:
            pass
        return None
    
    def _extract_color_info(self, data: bytes) -> Dict:
        """提取颜色信息"""
        format_type = self._detect_image_format(data)
        color_info = {
            "format": format_type,
            "has_alpha": format_type in ["png"],  # 简化判断
            "is_grayscale": False,
        }
        
        # 尝试检测灰度
        if format_type == "jpeg" and len(data) > 100:
            # JPEG 灰度图像通常较小且缺少颜色分量标记
            color_info["is_grayscale"] = len(data) < 50000
            
        return color_info
    
    def _extract_image_metadata(self, data: bytes) -> Dict:
        """提取图像元数据"""
        return {
            "compression_ratio": None,  # 需要完整解析
            "bit_depth": self._estimate_bit_depth(data),
            "file_size_kb": round(len(data) / 1024, 2),
        }
    
    def _estimate_bit_depth(self, data: bytes) -> Optional[int]:
        """估算位深度"""
        format_type = self._detect_image_format(data)
        if format_type == "png":
            if len(data) >= 25:
                return data[24]  # PNG bit depth 在 IHDR 中
        elif format_type == "gif":
            return 8  # GIF 通常是 8-bit
        return None
    
    def _process_audio(self, audio_data: bytes) -> FeatureVector:
        """
        音频特征提取 (P0-1 修复 - 补全实现)
        
        提取基础音频特征
        """
        features = {
            "size_bytes": len(audio_data),
            "format": self._detect_audio_format(audio_data),
            "duration_estimate": self._estimate_audio_duration(audio_data),
            "bitrate": self._estimate_audio_bitrate(audio_data),
            "is_valid": len(audio_data) > 1000,
        }
        
        # 尝试提取音频头信息
        try:
            features.update(self._extract_audio_metadata(audio_data))
        except Exception:
            pass
        
        self.feature_stats["processed_count"] += 1
        self.feature_stats["by_modality"]["audio"] += 1
        
        return FeatureVector(
            modality=ModalityType.AUDIO,
            features=features,
            confidence=0.70,
            raw_input_id=self._generate_content_id(audio_data)
        )
    
    def _detect_audio_format(self, data: bytes) -> str:
        """检测音频格式"""
        if data.startswith(b'ID3'):
            return "mp3"
        elif data.startswith(b'RIFF') and b'WAVE' in data[:12]:
            return "wav"
        elif data.startswith(b'OggS'):
            return "ogg"
        elif data.startswith(b'fLaC'):
            return "flac"
        elif data.startswith(b'\xff\xfb') or data.startswith(b'\xff\xf3'):
            return "mp3"  # MPEG 同步字
        return "unknown"
    
    def _estimate_audio_duration(self, data: bytes) -> Optional[float]:
        """估算音频时长(秒)"""
        format_type = self._detect_audio_format(data)
        
        if format_type == "wav":
            try:
                # WAV 格式：从头部解析
                if len(data) >= 44:
                    sample_rate = int.from_bytes(data[24:28], 'little')
                    bits_per_sample = int.from_bytes(data[34:36], 'little')
                    num_channels = int.from_bytes(data[22:24], 'little')
                    data_size = int.from_bytes(data[40:44], 'little')
                    
                    if sample_rate > 0 and bits_per_sample > 0 and num_channels > 0:
                        bytes_per_second = sample_rate * num_channels * (bits_per_sample // 8)
                        return round(data_size / bytes_per_second, 2)
            except Exception:
                pass
                
        elif format_type == "mp3":
            # 粗略估算：128kbps MP3 约 16KB/秒
            return round(len(data) / 16000, 2)
            
        return None
    
    def _estimate_audio_bitrate(self, data: bytes) -> Optional[int]:
        """估算音频比特率"""
        format_type = self._detect_audio_format(data)
        duration = self._estimate_audio_duration(data)
        
        if duration and duration > 0:
            bitrate = (len(data) * 8) / duration / 1000  # kbps
            return int(bitrate)
        return None
    
    def _extract_audio_metadata(self, data: bytes) -> Dict:
        """提取音频元数据"""
        return {
            "sample_rate": None,  # 需要完整解析
            "channels": self._estimate_audio_channels(data),
            "file_size_mb": round(len(data) / (1024 * 1024), 2),
        }
    
    def _estimate_audio_channels(self, data: bytes) -> Optional[int]:
        """估算音频声道数"""
        format_type = self._detect_audio_format(data)
        if format_type == "wav" and len(data) >= 24:
            try:
                return int.from_bytes(data[22:24], 'little')
            except Exception:
                pass
        return None
    
    # ==================== 新增特征提取方法 ====================
    
    def _calculate_readability(self, text: str) -> float:
        """计算文本可读性分数 (简化版 Flesch Reading Ease)"""
        sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
        words = len(text.split())
        syllables = sum(self._count_syllables(word) for word in text.split())
        
        if words == 0:
            return 0.0
            
        # 简化公式
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        # 归一化到 0-1 范围
        score = 1.0 - (avg_sentence_length / 50) - (avg_syllables_per_word / 10)
        return max(0.0, min(1.0, score))
    
    def _count_syllables(self, word: str) -> int:
        """估算单词音节数"""
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
                
        if word.endswith('e'):
            count -= 1
        return max(1, count)
    
    def _analyze_sentiment(self, text: str) -> float:
        """分析情感极性 (-1 到 1)"""
        positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'best', '棒', '好', '喜欢']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', '差', '坏', '讨厌']
        
        text_lower = text.lower()
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        return (positive_count - negative_count) / total
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """提取关键短语"""
        # 简单的名词短语提取
        phrases = []
        words = text.split()
        
        for i in range(len(words) - 1):
            # 大写开头+普通词 = 可能的名词短语
            if words[i][0].isupper() and words[i+1][0].islower():
                phrases.append(f"{words[i]} {words[i+1]}")
                
        return phrases[:5]  # 最多返回5个
    
    def _detect_language_text(self, text: str) -> str:
        """检测文本语言"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return "unknown"
            
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "chinese"
        elif chinese_ratio > 0.05:
            return "mixed"
        return "english"
    
    def _assess_code_quality(self, code: str) -> float:
        """评估代码质量分数"""
        score = 1.0
        
        # 检查注释率
        lines = code.split('\n')
        comment_lines = sum(1 for l in lines if l.strip().startswith('#') or '//' in l)
        if len(lines) > 0 and comment_lines / len(lines) < 0.05:
            score -= 0.2
            
        # 检查行长
        long_lines = sum(1 for l in lines if len(l) > 100)
        if len(lines) > 0 and long_lines / len(lines) > 0.2:
            score -= 0.2
            
        # 检查复杂度
        if code.count('if') > 10:
            score -= 0.1
            
        return max(0.0, score)
    
    def _analyze_function_complexity(self, code: str) -> Dict:
        """分析函数复杂度"""
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        complexities = {}
        
        for func in functions[:5]:  # 最多分析5个函数
            # 简单估算：基于函数体内的控制结构数量
            func_pattern = rf'def\s+{func}\s*\([^)]*\):.*?(?=def\s+|\Z)'
            match = re.search(func_pattern, code, re.DOTALL)
            if match:
                func_body = match.group(0)
                complexity = (
                    func_body.count('if') + 
                    func_body.count('for') + 
                    func_body.count('while')
                )
                complexities[func] = complexity
                
        return complexities
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """提取代码依赖"""
        imports = re.findall(r'(?:import|from)\s+(\w+)', code)
        requires = re.findall(r'require\([\'"]([^\'"]+)[\'"]', code)
        return list(set(imports + requires))
    
    def _calculate_doc_ratio(self, code: str) -> float:
        """计算文档比例"""
        lines = code.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        doc_lines = sum(1 for l in lines if '"""' in l or "'''" in l or l.strip().startswith('#'))
        
        if total_lines == 0:
            return 0.0
        return doc_lines / total_lines
    
    def _infer_schema(self, data: Dict) -> Dict:
        """推断数据结构模式"""
        schema = {}
        for key, value in data.items():
            schema[key] = {
                "type": type(value).__name__,
                "nullable": value is None,
            }
            if isinstance(value, (int, float)):
                schema[key]["range"] = "numeric"
            elif isinstance(value, str):
                schema[key]["max_length"] = len(value)
        return schema
    
    def _generate_content_id(self, content: Union[str, bytes]) -> str:
        """生成内容唯一ID (使用 SHA256 替代简单哈希)"""
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
        return hashlib.sha256(content_bytes).hexdigest()[:16]
    
    # ==================== 原有方法保留 ====================
    
    def recognize_patterns(self, perception: PerceptionInput) -> List[Pattern]:
        """模式识别"""
        patterns = []
        content = perception.content
        
        intent_pattern = self._recognize_intent(content)
        if intent_pattern:
            patterns.append(intent_pattern)
            
        entity_pattern = self._recognize_entities(content)
        if entity_pattern:
            patterns.append(entity_pattern)
            
        task_pattern = self._recognize_task_pattern(content)
        if task_pattern:
            patterns.append(task_pattern)
            
        emotion_pattern = self._recognize_emotion(content)
        if emotion_pattern:
            patterns.append(emotion_pattern)
            
        return patterns
    
    def _recognize_intent(self, content: Dict) -> Optional[Pattern]:
        """识别意图模式"""
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
        entities = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        return list(set(entities + quoted))
    
    def _extract_topics(self, text: str) -> List[str]:
        """主题提取"""
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
                "processor_version": "2.0 (P0-fixed)"
            }
        )
    
    def cross_modal_fusion(self, perceptions: List[PerceptionInput]) -> PerceptionInput:
        """跨模态融合"""
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
                
        confidences = [p.confidence for p in perceptions]
        fused_content["confidence"] = sum(confidences) / len(confidences)
        
        return PerceptionInput(
            modality="fused",
            content=fused_content,
            confidence=fused_content["confidence"],
            timestamp=datetime.now(),
            metadata={"source_modalities": len(perceptions)}
        )
    
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
            "learned_patterns": {k: len(v) for k, v in self.learned_patterns.items()},
            "feature_stats": self.feature_stats,
        }
    
    def save_state(self, filepath: str):
        """保存系统状态 (P0-3 修复)"""
        import json
        state = {
            "learned_patterns": {
                k: [
                    {
                        "pattern_type": p.pattern_type,
                        "content": p.content,
                        "confidence": p.confidence,
                        "supporting_evidence": p.supporting_evidence
                    }
                    for p in patterns
                ]
                for k, patterns in self.learned_patterns.items()
            },
            "feature_stats": self.feature_stats,
            "activation_level": self.activation_level,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load_state(self, filepath: str):
        """加载系统状态 (P0-3 修复)"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # 恢复学习到的模式
        self.learned_patterns = {}
        for k, patterns_data in state.get("learned_patterns", {}).items():
            self.learned_patterns[k] = [
                Pattern(
                    pattern_type=p["pattern_type"],
                    content=p["content"],
                    confidence=p["confidence"],
                    supporting_evidence=p["supporting_evidence"]
                )
                for p in patterns_data
            ]
        
        self.feature_stats = state.get("feature_stats", self.feature_stats)
        self.activation_level = state.get("activation_level", self.activation_level)


# 导出
__all__ = ['PerceptionSystem', 'ModalityType', 'FeatureVector', 'Pattern']
