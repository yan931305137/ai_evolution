# AI 电脑操作员系统 (Computer Use Agent)

让AI能够通过视觉（屏幕截图）感知电脑状态，通过鼠标和键盘操作电脑，像人类一样完成复杂任务。

## 🎯 核心能力

```
┌─────────────────────────────────────────────────────┐
│                   用户任务指令                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                ComputerUseAgent                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  视觉感知    │  │  AI决策      │  │  执行控制 │ │
│  │  (截图)      │──│  (LLM)       │──│ (鼠标/键盘│ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│           ▲                                    │    │
│           └────────────────────────────────────┘    │
│                    观察执行结果                      │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyautogui pillow playwright opencv-python-headless
playwright install chromium
```

### 2. 基础使用

```python
from src.tools.computer_use import computer_use

# 让AI自主完成任务
result = computer_use("打开浏览器访问百度，搜索'Python教程'")
print(result)
```

### 3. 高级使用

```python
from src.tools.computer_use import ComputerUseAgent

# 创建Agent
agent = ComputerUseAgent(max_steps=30)

# 定义回调函数观察执行过程
def on_step(step):
    print(f"步骤 {step.step_number}: {step.action.action_type}")
    print(f"原因: {step.action.reason}")

# 执行任务
result = agent.run(
    task="打开Chrome浏览器，访问Gmail，检查是否有新邮件",
    callback=on_step
)
print(f"任务结果: {result}")
```

## 📚 模块说明

### 视觉感知模块 (`visual_perception.py`)

负责屏幕截图和图像分析。

```python
from src.tools.computer_use import VisualPerceptionSystem, capture_screen

# 创建感知系统
visual = VisualPerceptionSystem(save_screenshots=True)

# 截取屏幕
screenshot = visual.capture_screen()

# 转换为base64（发送给LLM）
base64_image = visual.screenshot_to_base64(screenshot)

# 获取屏幕尺寸
width, height = visual.get_screen_size()

# 模板匹配查找元素
region = visual.find_element_by_template("button_template.png")
if region:
    print(f"找到元素在: {region.center}")
```

### 输入控制模块 (`input_controller.py`)

控制鼠标和键盘操作。

```python
from src.tools.computer_use import InputController, MouseButton

# 创建控制器
controller = InputController()

# 鼠标操作
controller.move_mouse(100, 200)           # 移动
controller.click(100, 200)                # 点击
controller.double_click(100, 200)         # 双击
controller.right_click(100, 200)          # 右键
controller.scroll(-500)                   # 向下滚动
controller.drag_to(300, 400)              # 拖拽

# 键盘操作
controller.type_text("Hello World")       # 输入文本
controller.press_key("enter")             # 按键
controller.hotkey("ctrl", "c")            # 组合键

# 便捷操作
controller.copy()   # Ctrl+C
controller.paste()  # Ctrl+V
controller.save()   # Ctrl+S
```

### 浏览器控制模块 (`browser_controller.py`)

控制浏览器进行网页操作。

```python
from src.tools.computer_use import SyncBrowserController

# 同步方式使用
with SyncBrowserController(headless=False) as browser:
    # 导航到网页
    browser.navigate("https://www.baidu.com")
    
    # 输入搜索词
    browser.fill("#kw", "Python教程")
    
    # 点击搜索按钮
    browser.click("#su")
    
    # 等待结果加载
    browser.wait(2)
    
    # 截图
    screenshot_base64 = browser.screenshot()
    
    # 获取页面信息
    print(browser.get_title())
    print(browser.get_url())
    
    # 滚动页面
    browser.scroll_down(500)
    
    # 前进/后退
    browser.go_back()
    browser.go_forward()

# 异步方式
import asyncio
from src.tools.computer_use import BrowserController

async def main():
    browser = BrowserController(headless=False)
    await browser.start()
    
    await browser.navigate("https://www.example.com")
    await browser.click("#button")
    
    await browser.stop()

asyncio.run(main())
```

## 🎮 使用场景示例

### 场景1: 网页自动化

```python
task = """
1. 打开浏览器访问 https://www.baidu.com
2. 在搜索框输入"OpenClaw AI助手"
3. 点击搜索按钮
4. 截图保存搜索结果
5. 关闭浏览器
"""

result = computer_use(task, max_steps=15)
```

### 场景2: 桌面应用操作

```python
task = """
1. 打开计算器应用
2. 计算 1234 * 5678
3. 将结果复制到剪贴板
"""

result = computer_use(task, max_steps=20)
```

### 场景3: 文件管理

```python
task = """
1. 打开文件管理器
2. 导航到桌面
3. 创建一个新文件夹命名为"AI_Projects"
4. 打开该文件夹
"""

result = computer_use(task, max_steps=15)
```

### 场景4: 复杂多步骤任务

```python
from src.tools.computer_use import ComputerUseAgent

agent = ComputerUseAgent(max_steps=50)

task = """
帮我完成以下任务：
1. 打开Chrome浏览器
2. 访问Gmail (mail.google.com)
3. 如果有新邮件，打开第一封未读邮件
4. 总结邮件内容
5. 回复邮件说"已收到，谢谢"
6. 截图保存操作过程
"""

# 使用回调观察每一步
steps_log = []
def log_step(step):
    steps_log.append({
        "step": step.step_number,
        "action": step.action.action_type,
        "reason": step.action.reason,
        "result": step.result
    })
    print(f"[{step.step_number}] {step.action.action_type}: {step.action.reason}")

result = agent.run(task, callback=log_step)
print(f"\n最终任务结果: {result}")
print(f"\n总共执行了 {len(steps_log)} 步")
```

## ⚠️ 安全注意事项

1. **故障保护**: 鼠标快速移动到屏幕左上角会中止程序（pyautogui.FAILSAFE）
2. **权限控制**: 需要屏幕录制和辅助功能权限
3. **敏感操作**: 避免让AI处理密码、支付等敏感信息
4. **监督运行**: 建议在可见模式下运行，观察AI行为

## 🔧 故障排查

### 问题1: `ImportError: No module named 'pyautogui'`

```bash
pip install pyautogui
```

### 问题2: `Display connection error` (Linux无显示器)

```bash
# 安装虚拟显示器
sudo apt-get install xvfb

# 使用xvfb-run运行
xvfb-run -a python your_script.py
```

### 问题3: 浏览器无法启动

```bash
# 安装playwright浏览器
playwright install chromium
playwright install firefox
```

### 问题4: Mac 权限问题

在 **系统设置 > 隐私与安全性 > 辅助功能** 中，给终端/Python添加权限。

## 🏗️ 架构设计

```
┌────────────────────────────────────────────────────────────┐
│                     ComputerUseAgent                       │
├────────────────────────────────────────────────────────────┤
│  循环: 观察(Observation) -> 思考(Thought) -> 行动(Action)   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────┐      ┌──────────────────┐          │
│  │ VisualPerception │      │   LLM Decision   │          │
│  │   System         │─────▶│     Engine       │          │
│  │                  │      │                  │          │
│  │ - capture_screen │      │ - analyze image  │          │
│  │ - template_match │      │ - plan action    │          │
│  │ - OCR (optional) │      │ - generate code  │          │
│  └──────────────────┘      └──────────────────┘          │
│           ▲                           │                    │
│           │                           ▼                    │
│  ┌────────┴──────────────────────────────────────┐        │
│  │              Action Execution                  │        │
│  ├────────────────────────────────────────────────┤        │
│  │  InputController  │  BrowserController         │        │
│  │  - mouse_move     │  - navigate                │        │
│  │  - click          │  - fill_form               │        │
│  │  - type_text      │  - click_element           │        │
│  │  - hotkey         │  - screenshot              │        │
│  └────────────────────────────────────────────────┘        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 📊 性能优化

### 截图优化

```python
# 只截取特定区域，减少数据传输
region = ScreenRegion(x=0, y=0, width=800, height=600)
screenshot = visual.capture_screen(region)
```

### LLM调用优化

```python
# 限制历史步骤数，减少token消耗
agent = ComputerUseAgent(max_steps=20)  # 只保留最近20步
```

### 浏览器优化

```python
# 无头模式运行（不显示窗口），速度更快
browser = SyncBrowserController(headless=True)
```

## 🔮 扩展开发

### 自定义视觉检测

```python
from src.tools.computer_use import VisualPerceptionSystem

class CustomVisualSystem(VisualPerceptionSystem):
    def detect_buttons(self, screenshot):
        # 使用YOLO或其他模型检测按钮
        pass
    
    def read_text(self, screenshot):
        # 集成OCR读取屏幕文字
        pass
```

### 自定义AI决策

```python
from src.tools.computer_use import ComputerUseAgent

class CustomAgent(ComputerUseAgent):
    def _get_system_prompt(self):
        # 自定义系统提示词
        return "你的自定义提示词..."
    
    def _think_and_act(self, task, observation, previous_steps):
        # 自定义决策逻辑
        pass
```

## 📝 更新日志

### v1.0.0 (2026-03-01)
- ✅ 基础视觉感知（截图）
- ✅ 鼠标和键盘控制
- ✅ 浏览器自动化（Playwright）
- ✅ AI决策循环（Observation-Thought-Action）
- ✅ 历史记录保存
- ✅ OpenClaw Agent集成
