"""
AI 电脑操作员系统 - 视觉感知模块
通过屏幕截图让AI"看见"电脑状态
"""
import base64
import io
import logging
import os
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None


@dataclass
class ScreenRegion:
    """屏幕区域定义"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class VisualElement:
    """视觉元素（UI组件、按钮、文本等）"""
    element_type: str  # button, text, input, image, icon, etc.
    region: ScreenRegion
    text: Optional[str] = None
    confidence: float = 1.0
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class VisualPerceptionSystem:
    """
    视觉感知系统
    负责截图、图像分析、UI元素检测
    """
    
    def __init__(self, save_screenshots: bool = False, screenshot_dir: str = "workspace/screenshots"):
        self.logger = logging.getLogger(__name__)
        self.save_screenshots = save_screenshots
        self.screenshot_dir = Path(screenshot_dir)
        self.last_screenshot: Optional[Image.Image] = None
        self.last_screenshot_path: Optional[str] = None
        
        if save_screenshots:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查依赖
        if not PIL_AVAILABLE:
            self.logger.error("PIL 未安装，视觉感知功能受限")
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV 未安装，高级图像分析功能受限")
    
    def capture_screen(self, region: Optional[ScreenRegion] = None) -> Image.Image:
        """
        截取屏幕
        
        Args:
            region: 指定区域，None则截取全屏
            
        Returns:
            PIL Image 对象
        """
        if not PIL_AVAILABLE:
            raise ImportError("需要安装 Pillow: pip install Pillow")
        
        try:
            import pyautogui
            
            if region:
                screenshot = pyautogui.screenshot(region=(region.x, region.y, region.width, region.height))
            else:
                screenshot = pyautogui.screenshot()
            
            self.last_screenshot = screenshot
            
            # 保存截图（如果启用）
            if self.save_screenshots:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = self.screenshot_dir / filename
                screenshot.save(filepath)
                self.last_screenshot_path = str(filepath)
                self.logger.debug(f"截图已保存: {filepath}")
            
            return screenshot
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            raise
    
    def screenshot_to_base64(self, screenshot: Optional[Image.Image] = None) -> str:
        """
        将截图转换为 base64（用于发送给LLM）
        
        Args:
            screenshot: PIL Image，None则使用最后一张截图
            
        Returns:
            base64 编码的字符串
        """
        img = screenshot or self.last_screenshot
        if img is None:
            img = self.capture_screen()
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def find_element_by_template(self, template_path: str, confidence: float = 0.8) -> Optional[ScreenRegion]:
        """
        通过模板匹配查找屏幕上的元素
        
        Args:
            template_path: 模板图片路径
            confidence: 匹配置信度阈值
            
        Returns:
            匹配区域，未找到返回 None
        """
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV 未安装，无法使用模板匹配")
            return None
        
        try:
            # 截取屏幕
            screenshot = self.capture_screen()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 读取模板
            template = cv2.imread(template_path)
            if template is None:
                self.logger.error(f"无法加载模板: {template_path}")
                return None
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                h, w = template.shape[:2]
                return ScreenRegion(
                    x=max_loc[0],
                    y=max_loc[1],
                    width=w,
                    height=h
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None
    
    def find_element_by_text(self, text: str) -> Optional[ScreenRegion]:
        """
        通过文字查找屏幕上的元素（需要OCR支持）
        
        Args:
            text: 要查找的文字
            
        Returns:
            文字区域，未找到返回 None
        """
        # 这里可以使用OCR库如 pytesseract 或 EasyOCR
        # 简化实现，实际使用时需要集成OCR
        self.logger.warning("文字查找需要OCR支持，建议使用 pytesseract")
        return None
    
    def analyze_screen_layout(self, screenshot: Optional[Image.Image] = None) -> List[VisualElement]:
        """
        分析屏幕布局，检测UI元素
        
        Args:
            screenshot: PIL Image，None则使用最后一张截图
            
        Returns:
            检测到的UI元素列表
        """
        elements = []
        img = screenshot or self.last_screenshot
        
        if img is None:
            img = self.capture_screen()
        
        # 简化的UI元素检测逻辑
        # 实际实现可以使用计算机视觉模型或UI检测库
        
        return elements
    
    def draw_annotations(self, screenshot: Optional[Image.Image] = None, 
                        elements: List[VisualElement] = None,
                        actions: List[Dict] = None) -> Image.Image:
        """
        在截图上绘制标注（用于调试和可视化）
        
        Args:
            screenshot: 原图
            elements: 要标注的元素
            actions: 要标注的操作
            
        Returns:
            带标注的图像
        """
        img = screenshot or self.last_screenshot
        if img is None:
            img = self.capture_screen()
        
        annotated = img.copy()
        draw = ImageDraw.Draw(annotated)
        
        # 绘制元素框
        if elements:
            for i, elem in enumerate(elements):
                bbox = elem.region.bbox
                draw.rectangle(bbox, outline="red", width=2)
                if elem.text:
                    draw.text((bbox[0], bbox[1] - 10), f"{i}: {elem.text}", fill="red")
        
        # 绘制操作标记
        if actions:
            for action in actions:
                if "x" in action and "y" in action:
                    x, y = action["x"], action["y"]
                    draw.ellipse([x-5, y-5, x+5, y+5], fill="blue")
                    if "label" in action:
                        draw.text((x+10, y), action["label"], fill="blue")
        
        return annotated
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕分辨率"""
        try:
            import pyautogui
            return pyautogui.size()
        except Exception as e:
            self.logger.error(f"获取屏幕尺寸失败: {e}")
            return (1920, 1080)  # 默认值
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        try:
            import pyautogui
            return pyautogui.position()
        except Exception as e:
            self.logger.error(f"获取鼠标位置失败: {e}")
            return (0, 0)


# 便捷函数
def capture_screen(region: Optional[ScreenRegion] = None) -> Image.Image:
    """快速截图"""
    perception = VisualPerceptionSystem(save_screenshots=False)
    return perception.capture_screen(region)


def screenshot_to_llm_format(screenshot: Image.Image) -> Dict[str, str]:
    """
    将截图转换为LLM可用的格式
    
    Returns:
        OpenAI/Claude 格式的图像消息
    """
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    base64_image = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/png;base64,{base64_image}"
        }
    }
