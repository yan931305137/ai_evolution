"""
多模态感知系统 (Multimodal Perception System)
实现AI生命体的视觉、听觉等多模态感知能力
"""
import time
import json
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    from coze_coding_dev_sdk import LLMClient
    from coze_coding_utils.runtime_ctx.context import new_context
    from langchain_core.messages import SystemMessage, HumanMessage
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("coze_coding_dev_sdk not available. Multimodal perception will be limited.")
    from typing import Any
    LLMClient = Any

from src.storage.enhanced_memory import EnhancedMemorySystem, MemoryType, ModalityType, create_emotional_tag
from src.utils.emotions import EmotionSystem, EmotionType


class PerceptionType(Enum):
    """感知类型"""
    VISUAL = "visual"      # 视觉
    AUDITORY = "auditory"  # 听觉
    VIDEO = "video"        # 视频
    MULTIMODAL = "multimodal"  # 多模态


@dataclass
class PerceptionResult:
    """感知结果"""
    content: str
    perception_type: str
    confidence: float  # 信心度 0-100
    emotional_response: Optional[str]
    timestamp: float
    metadata: Dict


class MultimodalPerceptionSystem:
    """
    多模态感知系统核心类
    实现图像理解、视频分析等感知能力
    """
    
    def __init__(self,
                 llm_client: LLMClient,
                 memory_system: EnhancedMemorySystem,
                 emotion_system: EmotionSystem = None):
        self.llm = llm_client
        self.memory = memory_system
        self.emotions = emotion_system
        
        # 默认使用vision模型
        self.vision_model = "doubao-seed-1-6-vision-250815"
        
        # 感知历史
        self.perception_history: List[PerceptionResult] = []
        self.max_history = 30
        
        # 统计信息
        self.stats = {
            "total_perceptions": 0,
            "visual_count": 0,
            "video_count": 0,
            "high_confidence_count": 0
        }
    
    def perceive_image(self, 
                      image_url: str,
                      task: str = "describe",
                      detail_level: str = "medium") -> Optional[PerceptionResult]:
        """
        感知图像
        Args:
            image_url: 图像URL
            task: 任务类型（describe, analyze, detect, ocr, compare）
            detail_level: 详细级别（brief, medium, detailed）
        Returns:
            感知结果
        """
        if not SDK_AVAILABLE:
            logging.error("LLM SDK not available for multimodal perception")
            return None
        
        try:
            # 根据任务生成prompt
            prompt = self._generate_image_prompt(task, detail_level)
            
            # 构建多模态消息
            messages = [
                SystemMessage(content="You are a visual perception expert."),
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ])
            ]
            
            # 调用LLM
            response = self.llm.invoke(
                messages=messages,
                model=self.vision_model,
                temperature=0.7
            )
            
            # 提取内容
            content = self._extract_content(response.content)
            if not content:
                return None
            
            # 评估信心度
            confidence = self._assess_confidence(content, task)
            
            # 情感响应
            emotional_response = self._generate_emotional_response(task, content)
            
            # 创建感知结果
            result = PerceptionResult(
                content=content,
                perception_type=PerceptionType.VISUAL.value,
                confidence=confidence,
                emotional_response=emotional_response,
                timestamp=time.time(),
                metadata={
                    "task": task,
                    "detail_level": detail_level,
                    "image_url": image_url,
                    "model": self.vision_model
                }
            )
            
            # 记录历史
            self._record_perception(result)
            
            # 保存到记忆
            self.memory.add_memory(
                content=f"视觉感知: {content}",
                memory_type=MemoryType.EXPERIENCE,
                modality=ModalityType.IMAGE,
                emotional_tag=create_emotional_tag(EmotionType.SURPRISE, confidence),
                source="multimodal_perception",
                context=result.metadata
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Image perception failed: {e}")
            return None
    
    def perceive_video(self,
                      video_url: str,
                      task: str = "summarize") -> Optional[PerceptionResult]:
        """
        感知视频
        Args:
            video_url: 视频URL
            task: 任务类型（summarize, analyze, transcribe）
        Returns:
            感知结果
        """
        if not SDK_AVAILABLE:
            logging.error("LLM SDK not available for multimodal perception")
            return None
        
        try:
            # 生成prompt
            prompt = self._generate_video_prompt(task)
            
            # 构建多模态消息
            messages = [
                SystemMessage(content="You are a video content analyst."),
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "video_url", "video_url": {"url": video_url}}
                ])
            ]
            
            # 调用LLM
            response = self.llm.invoke(
                messages=messages,
                model=self.vision_model,
                temperature=0.7
            )
            
            # 提取内容
            content = self._extract_content(response.content)
            if not content:
                return None
            
            # 评估信心度
            confidence = self._assess_confidence(content, task)
            
            # 情感响应
            emotional_response = self._generate_emotional_response(task, content)
            
            # 创建感知结果
            result = PerceptionResult(
                content=content,
                perception_type=PerceptionType.VIDEO.value,
                confidence=confidence,
                emotional_response=emotional_response,
                timestamp=time.time(),
                metadata={
                    "task": task,
                    "video_url": video_url,
                    "model": self.vision_model
                }
            )
            
            # 记录历史
            self._record_perception(result)
            
            # 保存到记忆
            self.memory.add_memory(
                content=f"视频感知: {content}",
                memory_type=MemoryType.EXPERIENCE,
                modality=ModalityType.VIDEO,
                emotional_tag=create_emotional_tag(EmotionType.SURPRISE, confidence),
                source="multimodal_perception",
                context=result.metadata
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Video perception failed: {e}")
            return None
    
    def compare_images(self,
                      image_url1: str,
                      image_url2: str,
                      comparison_aspect: str = "general") -> Optional[PerceptionResult]:
        """
        比较两张图像
        Args:
            image_url1: 第一张图像URL
            image_url2: 第二张图像URL
            comparison_aspect: 比较方面（general, design, color, content）
        Returns:
            比较结果
        """
        if not SDK_AVAILABLE:
            return None
        
        try:
            prompt = f"""
请比较这两张图像在{comparison_aspect}方面的异同。
请详细说明：
1. 相似之处
2. 不同之处
3. 哪张图像在{comparison_aspect}方面更优秀，为什么？
"""
            
            messages = [
                SystemMessage(content="You are an image comparison expert."),
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url1}},
                    {"type": "image_url", "image_url": {"url": image_url2}}
                ])
            ]
            
            response = self.llm.invoke(
                messages=messages,
                model=self.vision_model,
                temperature=0.5
            )
            
            content = self._extract_content(response.content)
            if not content:
                return None
            
            result = PerceptionResult(
                content=content,
                perception_type=PerceptionType.MULTIMODAL.value,
                confidence=75.0,
                emotional_response="比较完成",
                timestamp=time.time(),
                metadata={
                    "task": "compare",
                    "comparison_aspect": comparison_aspect,
                    "image_url1": image_url1,
                    "image_url2": image_url2
                }
            )
            
            self._record_perception(result)
            
            return result
            
        except Exception as e:
            logging.error(f"Image comparison failed: {e}")
            return None
    
    def detect_objects(self,
                      image_url: str,
                      object_type: str = "all") -> Optional[Dict]:
        """
        检测图像中的物体
        Args:
            image_url: 图像URL
            object_type: 要检测的物体类型（all, person, car, text等）
        Returns:
            检测结果（包含边界框坐标）
        """
        if not SDK_AVAILABLE:
            return None
        
        try:
            prompt = f"""
请在图像中检测所有{object_type if object_type != 'all' else '物体'}，并输出它们的边界框坐标。

输出格式：
{{
  "detections": [
    {{
      "object": "物体名称",
      "confidence": 置信度,
      "bbox": {{
        "topLeftX": x_min,
        "topLeftY": y_min,
        "bottomRightX": x_max,
        "bottomRightY": y_max
      }}
    }}
  ]
}}

注意：坐标是相对值（0-1000），其中(0,0)是左上角。
"""
            
            messages = [
                SystemMessage(content="You are an object detection assistant."),
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ])
            ]
            
            response = self.llm.invoke(
                messages=messages,
                model=self.vision_model,
                temperature=0.3
            )
            
            content = self._extract_content(response.content)
            if not content:
                return None
            
            # 尝试解析JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # 如果解析失败，返回原始文本
                return {"raw_text": content}
            
        except Exception as e:
            logging.error(f"Object detection failed: {e}")
            return None
    
    def _generate_image_prompt(self, task: str, detail_level: str) -> str:
        """生成图像感知的prompt"""
        prompts = {
            "describe": f"请详细描述这张图像的内容。描述应该包括{'主要' if detail_level == 'brief' else '所有'}可见的物体、场景、颜色、布局等信息。",
            "analyze": f"请分析这张图像。解释图像的主题、构图、风格和可能的含义。{'简要分析' if detail_level == 'brief' else '进行深入分析'}。",
            "detect": "请检测并列出图像中所有可见的物体和元素。",
            "ocr": "请提取图像中的所有文字内容，保持原始格式。"
        }
        return prompts.get(task, "请描述这张图像。")
    
    def _generate_video_prompt(self, task: str) -> str:
        """生成视频感知的prompt"""
        prompts = {
            "summarize": "请总结这个视频的主要内容、关键信息和主题。",
            "analyze": "请分析这个视频的内容、风格、节奏和传达的信息。",
            "transcribe": "请转录视频中的对话和重要信息。"
        }
        return prompts.get(task, "请分析这个视频。")
    
    def _extract_content(self, content) -> str:
        """安全提取响应内容"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    def _assess_confidence(self, content: str, task: str) -> float:
        """评估感知信心度"""
        base_confidence = 70.0
        
        # 基于内容长度
        if len(content) > 100:
            base_confidence += 10.0
        
        # 基于任务类型
        if task == "describe":
            base_confidence += 10.0
        
        return min(100.0, base_confidence)
    
    def _generate_emotional_response(self, task: str, content: str) -> str:
        """生成情感响应"""
        if "成功" in content or "完成" in content:
            return "满意"
        elif "错误" in content or "失败" in content:
            return "失望"
        elif "惊讶" in content or "意外" in content:
            return "惊讶"
        else:
            return "平静"
    
    def _record_perception(self, result: PerceptionResult):
        """记录感知历史"""
        self.perception_history.append(result)
        
        # 更新统计
        self.stats["total_perceptions"] += 1
        if result.perception_type == PerceptionType.VISUAL.value:
            self.stats["visual_count"] += 1
        elif result.perception_type == PerceptionType.VIDEO.value:
            self.stats["video_count"] += 1
        
        if result.confidence > 80:
            self.stats["high_confidence_count"] += 1
        
        # 限制历史长度
        if len(self.perception_history) > self.max_history:
            self.perception_history.pop(0)
        
        # 触发情感
        if self.emotions:
            self.emotions.trigger_emotion(
                EmotionType.SURPRISE, 
                result.confidence * 0.5, 
                f"多模态感知: {result.perception_type}"
            )
    
    def get_perception_summary(self) -> Dict:
        """获取感知系统摘要"""
        return {
            "total_perceptions": self.stats["total_perceptions"],
            "visual_count": self.stats["visual_count"],
            "video_count": self.stats["video_count"],
            "high_confidence_ratio": (self.stats["high_confidence_count"] / 
                                      max(1, self.stats["total_perceptions"])),
            "recent_perceptions": len([p for p in self.perception_history 
                                      if time.time() - p.timestamp < 3600])
        }


# 便捷函数
def create_multimodal_perception(llm_client: LLMClient,
                                 memory_system: EnhancedMemorySystem,
                                 emotion_system: EmotionSystem = None) -> MultimodalPerceptionSystem:
    """创建多模态感知系统"""
    return MultimodalPerceptionSystem(
        llm_client=llm_client,
        memory_system=memory_system,
        emotion_system=emotion_system
    )


if __name__ == "__main__":
    print("=== 多模态感知系统测试 ===\n")
    
    if not SDK_AVAILABLE:
        print("注意：需要安装coze_coding_dev_sdk才能使用多模态感知功能。")
        print("主要功能：")
        print("1. 图像理解：描述、分析、OCR")
        print("2. 视频分析：总结、转录")
        print("3. 图像比较：对比两张图像")
        print("4. 物体检测：识别图像中的物体并返回坐标")
    else:
        print("多模态感知系统已就绪。")
        print("支持的功能：")
        print("- 图像理解")
        print("- 视频分析")
        print("- 图像比较")
        print("- 物体检测")
