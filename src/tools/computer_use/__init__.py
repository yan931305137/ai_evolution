"""
AI 电脑操作员系统 (Computer Use Agent)
让AI能够通过视觉感知屏幕，操作鼠标键盘完成复杂任务

快速开始:
    from src.tools.computer_use import ComputerUseAgent, computer_use
    
    # 简单使用
    result = computer_use("打开浏览器访问百度，搜索'Python教程'")
    
    # 高级使用
    agent = ComputerUseAgent()
    result = agent.run("完成复杂任务...")
"""

from src.tools.computer_use.visual_perception import (
    VisualPerceptionSystem,
    ScreenRegion,
    VisualElement,
    capture_screen,
    screenshot_to_llm_format
)

from src.tools.computer_use.input_controller import (
    InputController,
    MouseButton,
    KeyModifier,
    MouseAction,
    KeyboardAction,
    click,
    type_text,
    press_key,
    hotkey
)

from src.tools.computer_use.browser_controller import (
    BrowserController,
    SyncBrowserController
)

from src.tools.computer_use.agent import (
    ComputerUseAgent,
    Action,
    Observation,
    Step,
    computer_use
)

__all__ = [
    # 视觉感知
    'VisualPerceptionSystem',
    'ScreenRegion',
    'VisualElement',
    'capture_screen',
    'screenshot_to_llm_format',
    
    # 输入控制
    'InputController',
    'MouseButton',
    'KeyModifier',
    'MouseAction',
    'KeyboardAction',
    'click',
    'type_text',
    'press_key',
    'hotkey',
    
    # 浏览器控制
    'BrowserController',
    'SyncBrowserController',
    
    # AI Agent
    'ComputerUseAgent',
    'Action',
    'Observation',
    'Step',
    'computer_use'
]

__version__ = "1.0.0"
