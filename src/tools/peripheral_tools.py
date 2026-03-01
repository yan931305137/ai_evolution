#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外设控制工具模块
功能：实现鼠标、键盘的精准控制，支持各类基础外设操作
"""
import time
from typing import Tuple, Optional
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
from src.utils.logger import setup_logger

logger = setup_logger(name="PeripheralTools")

# 初始化鼠标和键盘控制器
mouse = MouseController()
keyboard = KeyboardController()

# ==================== 鼠标操作函数 ====================
def mouse_move(x: int, y: int, duration: float = 0.0) -> None:
    """
    移动鼠标到指定坐标位置
    :param x: 目标横坐标
    :param y: 目标纵坐标
    :param duration: 移动动画持续时间，默认0即瞬间移动
    """
    if duration <= 0:
        mouse.position = (x, y)
        return
    # 平滑移动实现
    start_x, start_y = mouse.position
    step_num = int(duration * 60) # 60帧每秒
    if step_num == 0:
        mouse.position = (x, y)
        return
    step_x = (x - start_x) / step_num
    step_y = (y - start_y) / step_num
    for i in range(step_num):
        mouse.position = (start_x + step_x * (i + 1), start_y + step_y * (i + 1))
        time.sleep(1/60)
    mouse.position = (x, y)

def mouse_click(button: str = 'left', count: int = 1) -> None:
    """
    鼠标点击操作
    :param button: 点击的按键，支持'left'/'right'/'middle'
    :param count: 点击次数，默认1次
    """
    button_map = {
        'left': Button.left,
        'right': Button.right,
        'middle': Button.middle
    }
    mouse.click(button_map[button.lower()], count)

def mouse_double_click(button: str = 'left') -> None:
    """
    鼠标双击操作
    :param button: 点击的按键，默认左键
    """
    mouse_click(button, count=2)

def mouse_press(button: str = 'left') -> None:
    """
    按住鼠标按键
    :param button: 要按住的按键
    """
    button_map = {
        'left': Button.left,
        'right': Button.right,
        'middle': Button.middle
    }
    mouse.press(button_map[button.lower()])

def mouse_release(button: str = 'left') -> None:
    """
    释放鼠标按键
    :param button: 要释放的按键
    """
    button_map = {
        'left': Button.left,
        'right': Button.right,
        'middle': Button.middle
    }
    mouse.release(button_map[button.lower()])

def mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.2) -> None:
    """
    鼠标拖拽操作：从起点拖拽到终点
    :param start_x: 拖拽起点横坐标
    :param start_y: 拖拽起点纵坐标
    :param end_x: 拖拽终点横坐标
    :param end_y: 拖拽终点纵坐标
    :param duration: 拖拽动画持续时间
    """
    # 移动到起点
    mouse_move(start_x, start_y)
    time.sleep(0.05)
    # 按住左键
    mouse_press('left')
    time.sleep(0.05)
    # 移动到终点
    mouse_move(end_x, end_y, duration)
    time.sleep(0.05)
    # 释放左键
    mouse_release('left')

def select_text(start_x: int, start_y: int, end_x: int, end_y: int) -> None:
    """
    选中文本操作：本质是拖拽鼠标实现文本选中
    :param start_x: 文本起点横坐标
    :param start_y: 文本起点纵坐标
    :param end_x: 文本终点横坐标
    :param end_y: 文本终点纵坐标
    """
    mouse_drag(start_x, start_y, end_x, end_y)

# ==================== 键盘操作函数 ====================
def key_press(key: str) -> None:
    """
    按住指定按键
    :param key: 要按住的按键，支持特殊按键和普通字符
    """
    if hasattr(Key, key.lower()):
        keyboard.press(getattr(Key, key.lower()))
    else:
        keyboard.press(key)

def key_release(key: str) -> None:
    """
    释放指定按键
    :param key: 要释放的按键
    """
    if hasattr(Key, key.lower()):
        keyboard.release(getattr(Key, key.lower()))
    else:
        keyboard.release(key)

def key_tap(key: str, count: int = 1, interval: float = 0.05) -> None:
    """
    敲击指定按键（按下并释放）
    :param key: 要敲击的按键
    :param count: 敲击次数，默认1次
    :param interval: 多次敲击的间隔时间
    """
    for _ in range(count):
        if hasattr(Key, key.lower()):
            keyboard.tap(getattr(Key, key.lower()))
        else:
            keyboard.tap(key)
        time.sleep(interval)

def type_text(text: str, interval: float = 0.02) -> None:
    """
    输入一段文本
    :param text: 要输入的文本内容
    :param interval: 每个字符输入的间隔时间
    """
    keyboard.type(text, interval)

# 常用键盘按键快捷操作
def key_enter(count: int = 1) -> None:
    """按回车键"""
    key_tap('enter', count)

def key_backspace(count: int = 1) -> None:
    """按退格键"""
    key_tap('backspace', count)

def key_tab(count: int = 1) -> None:
    """按Tab键"""
    key_tap('tab', count)

def key_caps_lock() -> None:
    """切换大小写锁定"""
    key_tap('caps_lock')

def key_shift_press() -> None:
    """按住Shift键"""
    key_press('shift')

def key_shift_release() -> None:
    """释放Shift键"""
    key_release('shift')

def key_ctrl_press() -> None:
    """按住Ctrl键"""
    key_press('ctrl')

def key_ctrl_release() -> None:
    """释放Ctrl键"""
    key_release('ctrl')

def key_alt_press() -> None:
    """按住Alt键"""
    key_press('alt')

def key_alt_release() -> None:
    """释放Alt键"""
    key_release('alt')

def key_esc(count: int = 1) -> None:
    """按ESC键"""
    key_tap('esc', count)

def key_space(count: int = 1) -> None:
    """按空格键"""
    key_tap('space', count)

# ==================== 测试函数 ====================
def run_peripheral_test() -> Tuple[bool, Optional[str]]:
    """
    运行外设操作连续10次零失误测试
    :return: (测试是否通过, 错误信息) 
    """
    try:
        test_operations = [
            # 鼠标操作测试
            lambda: mouse_move(100, 100),
            lambda: mouse_click('left'),
            lambda: mouse_double_click('left'),
            lambda: mouse_drag(100,100,200,200),
            # 键盘操作测试
            lambda: type_text('test123'),
            lambda: key_backspace(3),
            lambda: key_enter(),
            lambda: key_caps_lock(),
            lambda: type_text('HELLO'),
            lambda: key_caps_lock()
        ]
        
        # 执行10次操作
        for i, op in enumerate(test_operations, 1):
            op()
            time.sleep(0.1)
            logger.info(f"第{i}次操作执行成功")
        
        return True, "连续10次外设操作全部零失误通过测试"
    except Exception as e:
        return False, f"操作执行失败：{str(e)}"