"""
Computer Use Skill - 让AI能够操作电脑
"""
import logging
from typing import Dict, Any, Optional
from src.tools.computer_use import ComputerUseAgent, computer_use

logger = logging.getLogger(__name__)


class ComputerUseSkill:
    """
    电脑操作技能
    允许AI通过视觉感知屏幕，操作鼠标键盘完成复杂任务
    """
    
    name = "computer_use"
    description = "通过视觉感知屏幕，操作鼠标键盘和浏览器完成复杂任务"
    
    def __init__(self):
        self.agent: Optional[ComputerUseAgent] = None
    
    def execute_task(self, task: str, max_steps: int = 20) -> Dict[str, Any]:
        """
        执行电脑操作任务
        
        Args:
            task: 任务描述，例如：
                - "打开浏览器访问百度，搜索'Python教程'"
                - "打开计算器，计算123*456"
                - "在桌面上创建一个新文件夹"
                - "打开Chrome，访问Gmail并登录"
        
        Returns:
            任务执行结果
        """
        logger.info(f"执行电脑操作任务: {task}")
        
        try:
            result = computer_use(task, max_steps=max_steps)
            return {
                "success": True,
                "result": result,
                "task": task
            }
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    def click(self, x: int, y: int) -> Dict[str, Any]:
        """点击屏幕指定位置"""
        from src.tools.computer_use import click as do_click
        try:
            do_click(x, y)
            return {"success": True, "action": f"点击 ({x}, {y})"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """输入文本"""
        from src.tools.computer_use import type_text as do_type
        try:
            do_type(text)
            return {"success": True, "action": f"输入文本: {text[:30]}..."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def press_key(self, key: str) -> Dict[str, Any]:
        """按下按键"""
        from src.tools.computer_use import press_key as do_press
        try:
            do_press(key)
            return {"success": True, "action": f"按键: {key}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def take_screenshot(self) -> Dict[str, Any]:
        """截取屏幕截图"""
        from src.tools.computer_use import capture_screen
        try:
            screenshot = capture_screen()
            # 保存截图
            import os
            from datetime import datetime
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join("workspace/screenshots", filename)
            os.makedirs("workspace/screenshots", exist_ok=True)
            screenshot.save(filepath)
            return {
                "success": True,
                "filepath": filepath,
                "action": "截图已保存"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_browser(self, url: Optional[str] = None) -> Dict[str, Any]:
        """打开浏览器"""
        try:
            from src.tools.computer_use import SyncBrowserController
            browser = SyncBrowserController(headless=False)
            browser.start()
            if url:
                browser.navigate(url)
            return {
                "success": True,
                "action": f"打开浏览器{'并访问 ' + url if url else ''}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 工具定义（用于 Agent 注册）
COMPUTER_USE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "computer_use_execute_task",
            "description": "让AI通过视觉感知屏幕，操作鼠标键盘和浏览器完成复杂任务。AI会自主决策每一步操作，直到任务完成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "详细的任务描述，说明要AI完成什么操作"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "最大执行步数（默认20步）",
                        "default": 20
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "computer_use_click",
            "description": "在屏幕指定位置点击鼠标",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X坐标"},
                    "y": {"type": "integer", "description": "Y坐标"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "computer_use_type_text",
            "description": "在当前焦点位置输入文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要输入的文本"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "computer_use_press_key",
            "description": "按下键盘按键",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string", 
                        "description": "按键名称，如 enter, tab, escape, ctrl, alt 等"
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "computer_use_take_screenshot",
            "description": "截取当前屏幕截图并保存",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "computer_use_open_browser",
            "description": "打开浏览器，可选访问指定网址",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要访问的网址（可选）",
                        "default": None
                    }
                }
            }
        }
    }
]


# 技能实例
computer_use_skill = ComputerUseSkill()
