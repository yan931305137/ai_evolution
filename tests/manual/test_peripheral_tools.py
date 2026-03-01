import sys
import os
import time

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.tools.peripheral_tools import (
    mouse_move, mouse_click, mouse_double_click, mouse_drag, 
    type_text, key_enter, key_tap, key_press, key_release
)
from src.tools.web_tools import open_browser

def test_peripheral_tools():
    print("开始测试外设工具...")
    print("请注意：接下来的操作会移动鼠标和模拟键盘输入，请不要触碰鼠标和键盘。")
    print("测试将在 3 秒后开始...")
    time.sleep(3)  # 给用户准备时间

    # 1. 鼠标测试
    print("1. 测试鼠标移动 (移动到屏幕 500, 500)...")
    try:
        mouse_move(500, 500, duration=1.0)
        print("   鼠标移动成功")
    except Exception as e:
        print(f"   鼠标移动失败: {e}")
    time.sleep(1)
    
    # 2. 键盘测试
    print("2. 测试键盘输入 (将在当前焦点窗口输入 'Hello AI')...")
    try:
        type_text("Hello AI")
        time.sleep(0.5)
        key_enter()
        print("   键盘输入成功")
    except Exception as e:
        print(f"   键盘输入失败: {e}")
    time.sleep(1)
    
    # 3. 浏览器测试
    print("3. 测试打开浏览器 (打开百度)...")
    try:
        result = open_browser("https://www.baidu.com")
        print(f"   {result}")
    except Exception as e:
        print(f"   打开浏览器失败: {e}")
    
    print("\n测试完成！如果看到了鼠标移动、文字输入和浏览器打开，说明功能正常。")

if __name__ == "__main__":
    test_peripheral_tools()