"""
AI 电脑操作员系统 - 输入控制模块
鼠标和键盘操作控制
"""
import logging
import time
from typing import Optional, Tuple, List, Union
from dataclasses import dataclass
from enum import Enum

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None


class MouseButton(Enum):
    """鼠标按钮"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class KeyModifier(Enum):
    """键盘修饰键"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    COMMAND = "command"  # Mac
    WIN = "win"  # Windows


@dataclass
class MouseAction:
    """鼠标动作定义"""
    action_type: str  # move, click, double_click, drag, scroll
    x: Optional[int] = None
    y: Optional[int] = None
    button: MouseButton = MouseButton.LEFT
    duration: float = 0.5  # 移动动画时长
    clicks: int = 1
    scroll_amount: int = 0


@dataclass
class KeyboardAction:
    """键盘动作定义"""
    action_type: str  # press, type, hotkey
    key: Optional[str] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None  # 组合键
    interval: float = 0.01  # 打字间隔


class InputController:
    """
    输入控制器
    控制鼠标和键盘操作
    """
    
    def __init__(self, fail_safe: bool = True, pause: float = 0.1):
        """
        初始化输入控制器
        
        Args:
            fail_safe: 启用故障保护（鼠标移动到屏幕角落中止）
            pause: 操作之间的默认暂停时间
        """
        self.logger = logging.getLogger(__name__)
        
        if not PYAUTOGUI_AVAILABLE:
            raise ImportError("需要安装 pyautogui: pip install pyautogui")
        
        # 配置 pyautogui
        pyautogui.FAILSAFE = fail_safe  # 鼠标移到屏幕左上角中止
        pyautogui.PAUSE = pause
        
        self.logger.info("输入控制器初始化完成")
    
    # ==================== 鼠标控制 ====================
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> None:
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动动画时长（秒）
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self.logger.debug(f"鼠标移动到: ({x}, {y})")
        except Exception as e:
            self.logger.error(f"鼠标移动失败: {e}")
            raise
    
    def move_mouse_relative(self, x_offset: int, y_offset: int, duration: float = 0.5) -> None:
        """
        相对移动鼠标
        
        Args:
            x_offset: X方向偏移
            y_offset: Y方向偏移
            duration: 移动动画时长
        """
        try:
            pyautogui.moveRel(x_offset, y_offset, duration=duration)
            self.logger.debug(f"鼠标相对移动: ({x_offset}, {y_offset})")
        except Exception as e:
            self.logger.error(f"鼠标相对移动失败: {e}")
            raise
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: MouseButton = MouseButton.LEFT, clicks: int = 1) -> None:
        """
        鼠标点击
        
        Args:
            x: 点击位置X，None则在当前位置点击
            y: 点击位置Y，None则在当前位置点击
            button: 鼠标按钮
            clicks: 点击次数
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button.value, clicks=clicks)
                self.logger.debug(f"鼠标点击: ({x}, {y}), 按钮={button.value}, 次数={clicks}")
            else:
                pyautogui.click(button=button.value, clicks=clicks)
                self.logger.debug(f"鼠标点击当前位置, 按钮={button.value}, 次数={clicks}")
        except Exception as e:
            self.logger.error(f"鼠标点击失败: {e}")
            raise
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """双击"""
        self.click(x, y, clicks=2)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """右键点击"""
        self.click(x, y, button=MouseButton.RIGHT)
    
    def drag_to(self, x: int, y: int, duration: float = 0.5, 
                button: MouseButton = MouseButton.LEFT) -> None:
        """
        拖拽到指定位置
        
        Args:
            x: 目标X
            y: 目标Y
            duration: 拖拽时长
            button: 拖拽使用的按钮
        """
        try:
            pyautogui.dragTo(x, y, duration=duration, button=button.value)
            self.logger.debug(f"拖拽到: ({x}, {y})")
        except Exception as e:
            self.logger.error(f"拖拽失败: {e}")
            raise
    
    def drag_relative(self, x_offset: int, y_offset: int, duration: float = 0.5,
                      button: MouseButton = MouseButton.LEFT) -> None:
        """相对拖拽"""
        try:
            pyautogui.dragRel(x_offset, y_offset, duration=duration, button=button.value)
            self.logger.debug(f"相对拖拽: ({x_offset}, {y_offset})")
        except Exception as e:
            self.logger.error(f"相对拖拽失败: {e}")
            raise
    
    def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """
        滚动鼠标滚轮
        
        Args:
            amount: 滚动量（正数向上，负数向下）
            x: 滚动位置X
            y: 滚动位置Y
        """
        try:
            if x is not None and y is not None:
                pyautogui.scroll(amount, x, y)
            else:
                pyautogui.scroll(amount)
            self.logger.debug(f"滚动: {amount}")
        except Exception as e:
            self.logger.error(f"滚动失败: {e}")
            raise
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        return pyautogui.position()
    
    # ==================== 键盘控制 ====================
    
    def press_key(self, key: str) -> None:
        """
        按下并释放单个按键
        
        Args:
            key: 按键名称（如 'enter', 'tab', 'esc'）
        """
        try:
            pyautogui.press(key)
            self.logger.debug(f"按键: {key}")
        except Exception as e:
            self.logger.error(f"按键失败: {e}")
            raise
    
    def type_text(self, text: str, interval: float = 0.01) -> None:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间隔（模拟人类打字）
        """
        try:
            pyautogui.typewrite(text, interval=interval)
            self.logger.debug(f"输入文本: {text[:20]}...")
        except Exception as e:
            self.logger.error(f"输入文本失败: {e}")
            raise
    
    def hotkey(self, *keys: str) -> None:
        """
        按下组合键
        
        Args:
            *keys: 组合键列表（如 'ctrl', 'c'）
        
        Example:
            hotkey('ctrl', 'c')  # 复制
            hotkey('ctrl', 'alt', 'delete')  # 任务管理器
        """
        try:
            pyautogui.hotkey(*keys)
            self.logger.debug(f"组合键: {'+'.join(keys)}")
        except Exception as e:
            self.logger.error(f"组合键失败: {e}")
            raise
    
    def hold_key(self, key: str):
        """
        上下文管理器：按住某个键
        
        Example:
            with hold_key('shift'):
                click(100, 100)  # Shift+点击
        """
        return pyautogui.hold(key)
    
    def press_sequence(self, keys: List[str], interval: float = 0.1) -> None:
        """
        按顺序按下多个键
        
        Args:
            keys: 按键列表
            interval: 按键间隔
        """
        try:
            for key in keys:
                self.press_key(key)
                time.sleep(interval)
        except Exception as e:
            self.logger.error(f"按键序列失败: {e}")
            raise
    
    # ==================== 便捷操作 ====================
    
    def click_element(self, element_region) -> None:
        """
        点击屏幕上的元素
        
        Args:
            element_region: VisualElement 或 ScreenRegion 对象
        """
        if hasattr(element_region, 'region'):
            region = element_region.region
        else:
            region = element_region
        
        center_x, center_y = region.center
        self.click(center_x, center_y)
    
    def select_all(self) -> None:
        """全选 (Ctrl+A)"""
        self.hotkey('ctrl', 'a')
    
    def copy(self) -> None:
        """复制 (Ctrl+C)"""
        self.hotkey('ctrl', 'c')
    
    def paste(self) -> None:
        """粘贴 (Ctrl+V)"""
        self.hotkey('ctrl', 'v')
    
    def cut(self) -> None:
        """剪切 (Ctrl+X)"""
        self.hotkey('ctrl', 'x')
    
    def undo(self) -> None:
        """撤销 (Ctrl+Z)"""
        self.hotkey('ctrl', 'z')
    
    def save(self) -> None:
        """保存 (Ctrl+S)"""
        self.hotkey('ctrl', 's')
    
    def press_escape(self) -> None:
        """按 ESC 键"""
        self.press_key('esc')
    
    def press_enter(self) -> None:
        """按 Enter 键"""
        self.press_key('enter')
    
    def press_tab(self) -> None:
        """按 Tab 键"""
        self.press_key('tab')
    
    def wait(self, seconds: float) -> None:
        """等待指定时间"""
        time.sleep(seconds)


# 便捷函数
def click(x: int, y: int, button: str = "left") -> None:
    """快速点击"""
    controller = InputController()
    controller.click(x, y, MouseButton(button))


def type_text(text: str) -> None:
    """快速输入文本"""
    controller = InputController()
    controller.type_text(text)


def press_key(key: str) -> None:
    """快速按键"""
    controller = InputController()
    controller.press_key(key)


def hotkey(*keys: str) -> None:
    """快速组合键"""
    controller = InputController()
    controller.hotkey(*keys)
