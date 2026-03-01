"""
AI 电脑操作员系统 - 核心控制器
整合视觉感知、输入控制和浏览器操作
实现"看->思考->行动"的AI闭环
"""
import asyncio
import json
import logging
import os
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.utils.llm import LLMClient
from src.tools.computer_use.visual_perception import VisualPerceptionSystem, screenshot_to_llm_format
from src.tools.computer_use.input_controller import InputController
from src.tools.computer_use.browser_controller import BrowserController, SyncBrowserController


@dataclass
class Action:
    """AI执行的动作"""
    action_type: str  # click, type, press, scroll, navigate, wait, finish
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""  # 执行这个动作的原因
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Observation:
    """AI观察到的环境状态"""
    screenshot: Optional[str] = None  # base64 编码
    mouse_position: tuple = (0, 0)
    screen_size: tuple = (1920, 1080)
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Step:
    """执行步骤记录"""
    step_number: int
    observation: Observation
    thought: str
    action: Action
    result: Optional[str] = None


class ComputerUseAgent:
    """
    AI 电脑操作员
    能够看屏幕、操作鼠标键盘、控制浏览器完成复杂任务
    """
    
    def __init__(self, llm: Optional[LLMClient] = None, 
                 max_steps: int = 20,
                 save_history: bool = True,
                 history_dir: str = "workspace/computer_use_history"):
        """
        初始化 AI 电脑操作员
        
        Args:
            llm: LLM 客户端，用于决策
            max_steps: 最大执行步数
            save_history: 是否保存执行历史
            history_dir: 历史记录保存目录
        """
        self.logger = logging.getLogger(__name__)
        self.llm = llm or LLMClient()
        self.max_steps = max_steps
        self.save_history = save_history
        self.history_dir = Path(history_dir)
        
        if save_history:
            self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各模块
        self.visual = VisualPerceptionSystem(save_screenshots=True)
        self.input_controller = InputController()
        self.browser: Optional[SyncBrowserController] = None
        
        # 状态
        self.steps: List[Step] = []
        self.current_step = 0
        self.task_completed = False
        
        self.logger.info("AI 电脑操作员初始化完成")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个AI电脑操作员，能够通过视觉感知屏幕内容，操作鼠标和键盘完成用户任务。

你可以执行以下操作：

1. **鼠标操作**:
   - click: 点击指定坐标 (x, y)
   - double_click: 双击指定坐标 (x, y)
   - right_click: 右键点击 (x, y)
   - move: 移动鼠标到 (x, y)
   - drag: 拖拽从 (start_x, start_y) 到 (end_x, end_y)
   - scroll: 滚动 (amount: 正数向上, 负数向下)

2. **键盘操作**:
   - type: 输入文本 (text)
   - press: 按下特定键 (key: enter, tab, escape 等)
   - hotkey: 组合键 (keys: ["ctrl", "c"])

3. **浏览器操作**:
   - navigate: 打开网页 (url)
   - wait: 等待 (seconds)

4. **任务控制**:
   - finish: 完成任务 (answer: 任务结果)

**重要规则**:
1. 每次只能执行一个操作
2. 操作后要等待系统响应
3. 如果操作失败，尝试替代方案
4. 时刻关注屏幕变化，调整策略
5. 坐标基于屏幕分辨率，当前为 1920x1080

**响应格式** (JSON):
{
    "thought": "详细描述当前观察和思考过程",
    "action": "操作类型",
    "params": {
        // 操作参数
    },
    "reason": "为什么选择这个操作"
}"""
    
    def _observe(self) -> Observation:
        """观察当前环境状态"""
        # 截图
        screenshot = self.visual.capture_screen()
        screenshot_b64 = self.visual.screenshot_to_base64(screenshot)
        
        # 获取鼠标位置
        mouse_pos = self.input_controller.get_mouse_position()
        
        # 获取屏幕尺寸
        screen_size = self.visual.get_screen_size()
        
        # 如果浏览器已打开，获取网页信息
        current_url = None
        page_title = None
        if self.browser:
            try:
                current_url = asyncio.run(self.browser._async_controller.get_url())
                page_title = asyncio.run(self.browser._async_controller.get_title())
            except:
                pass
        
        return Observation(
            screenshot=screenshot_b64,
            mouse_position=mouse_pos,
            screen_size=screen_size,
            current_url=current_url,
            page_title=page_title
        )
    
    def _think_and_act(self, task: str, observation: Observation, 
                       previous_steps: List[Step]) -> Action:
        """
        AI 思考并决定下一步操作
        
        Args:
            task: 目标任务
            observation: 当前观察
            previous_steps: 历史步骤
            
        Returns:
            要执行的动作
        """
        # 构建消息
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"任务: {task}\n\n请根据当前屏幕截图决定下一步操作。"}
        ]
        
        # 添加历史步骤
        for step in previous_steps[-5:]:  # 只保留最近5步
            messages.append({
                "role": "assistant", 
                "content": json.dumps({
                    "thought": step.thought,
                    "action": step.action.action_type,
                    "params": step.action.params,
                    "reason": step.action.reason
                }, ensure_ascii=False)
            })
        
        # 添加当前观察
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"当前屏幕截图：鼠标位置 {observation.mouse_position}, 屏幕尺寸 {observation.screen_size}"},
                screenshot_to_llm_format(self.visual.last_screenshot)
            ]
        })
        
        # 调用 LLM
        try:
            response = self.llm.generate(messages)
            
            # 解析 JSON 响应
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                return Action(
                    action_type=result.get("action", "wait"),
                    params=result.get("params", {}),
                    reason=result.get("reason", "")
                )
            else:
                self.logger.warning("LLM 响应无法解析，默认等待")
                return Action(action_type="wait", params={"seconds": 1})
                
        except Exception as e:
            self.logger.error(f"LLM 调用失败: {e}")
            return Action(action_type="wait", params={"seconds": 1})
    
    def _execute_action(self, action: Action) -> str:
        """
        执行动作
        
        Args:
            action: 要执行的动作
            
        Returns:
            执行结果
        """
        try:
            if action.action_type == "click":
                x = action.params.get("x")
                y = action.params.get("y")
                self.input_controller.click(x, y)
                return f"点击 ({x}, {y})"
            
            elif action.action_type == "double_click":
                x = action.params.get("x")
                y = action.params.get("y")
                self.input_controller.double_click(x, y)
                return f"双击 ({x}, {y})"
            
            elif action.action_type == "right_click":
                x = action.params.get("x")
                y = action.params.get("y")
                self.input_controller.right_click(x, y)
                return f"右键点击 ({x}, {y})"
            
            elif action.action_type == "move":
                x = action.params.get("x")
                y = action.params.get("y")
                self.input_controller.move_mouse(x, y)
                return f"鼠标移动到 ({x}, {y})"
            
            elif action.action_type == "drag":
                start_x = action.params.get("start_x")
                start_y = action.params.get("start_y")
                end_x = action.params.get("end_x")
                end_y = action.params.get("end_y")
                self.input_controller.move_mouse(start_x, start_y)
                self.input_controller.drag_to(end_x, end_y)
                return f"拖拽从 ({start_x}, {start_y}) 到 ({end_x}, {end_y})"
            
            elif action.action_type == "scroll":
                amount = action.params.get("amount", 500)
                self.input_controller.scroll(amount)
                return f"滚动 {amount}"
            
            elif action.action_type == "type":
                text = action.params.get("text", "")
                self.input_controller.type_text(text)
                return f"输入文本: {text[:30]}..."
            
            elif action.action_type == "press":
                key = action.params.get("key", "")
                self.input_controller.press_key(key)
                return f"按键: {key}"
            
            elif action.action_type == "hotkey":
                keys = action.params.get("keys", [])
                self.input_controller.hotkey(*keys)
                return f"组合键: {'+'.join(keys)}"
            
            elif action.action_type == "navigate":
                url = action.params.get("url", "")
                if not self.browser:
                    self.browser = SyncBrowserController(headless=False)
                    self.browser.start()
                self.browser.navigate(url)
                return f"导航到: {url}"
            
            elif action.action_type == "wait":
                seconds = action.params.get("seconds", 1)
                self.input_controller.wait(seconds)
                return f"等待 {seconds} 秒"
            
            elif action.action_type == "finish":
                self.task_completed = True
                return f"任务完成: {action.params.get('answer', '')}"
            
            else:
                return f"未知操作: {action.action_type}"
                
        except Exception as e:
            self.logger.error(f"执行动作失败: {e}")
            return f"执行失败: {str(e)}"
    
    def run(self, task: str, callback: Optional[Callable[[Step], None]] = None) -> str:
        """
        执行任务
        
        Args:
            task: 任务描述
            callback: 每步执行的回调函数
            
        Returns:
            任务结果
        """
        self.logger.info(f"开始任务: {task}")
        self.steps = []
        self.current_step = 0
        self.task_completed = False
        
        try:
            while self.current_step < self.max_steps and not self.task_completed:
                self.current_step += 1
                self.logger.info(f"步骤 {self.current_step}/{self.max_steps}")
                
                # 1. 观察环境
                observation = self._observe()
                
                # 2. AI 思考并决策
                action = self._think_and_act(task, observation, self.steps)
                
                # 3. 执行动作
                result = self._execute_action(action)
                
                # 4. 记录步骤
                step = Step(
                    step_number=self.current_step,
                    observation=observation,
                    thought=action.reason,
                    action=action,
                    result=result
                )
                self.steps.append(step)
                
                # 回调
                if callback:
                    callback(step)
                
                # 短暂等待系统响应
                if not self.task_completed:
                    self.input_controller.wait(0.5)
            
            # 保存历史
            if self.save_history:
                self._save_history(task)
            
            # 返回结果
            if self.task_completed:
                last_step = self.steps[-1]
                return last_step.action.params.get("answer", "任务完成")
            else:
                return "达到最大步数限制，任务未完成"
                
        finally:
            # 清理资源
            if self.browser:
                self.browser.stop()
                self.browser = None
    
    def _save_history(self, task: str) -> None:
        """保存执行历史"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"computer_use_{timestamp}.json"
        filepath = self.history_dir / filename
        
        history = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "total_steps": len(self.steps),
            "completed": self.task_completed,
            "steps": [
                {
                    "step": step.step_number,
                    "thought": step.thought,
                    "action": {
                        "type": step.action.action_type,
                        "params": step.action.params,
                        "reason": step.action.reason
                    },
                    "result": step.result
                }
                for step in self.steps
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"执行历史已保存: {filepath}")


# 便捷函数
def computer_use(task: str, max_steps: int = 20, llm: Optional[LLMClient] = None) -> str:
    """
    快速使用 AI 电脑操作员
    
    Args:
        task: 任务描述
        max_steps: 最大执行步数
        llm: LLM 客户端
        
    Returns:
        任务结果
    """
    agent = ComputerUseAgent(llm=llm, max_steps=max_steps)
    return agent.run(task)


# 示例使用
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    logger = setup_logger()
    
    # 示例任务
    task = "打开浏览器，访问百度搜索'OpenClaw'，然后截图保存结果"
    result = computer_use(task, max_steps=10)
    logger.info(f"任务结果: {result}")
