#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高优先级工具是否可以正常调用
"""

import sys
sys.path.insert(0, '.')

from src.tools import Tools

def test_tool_callability():
    """测试三个高优工具是否可以被execute_tool正常调用"""
    print("=== 测试高优先级工具可调用性 ===")
    
    tools_to_test = [
        ("code_security_verification", {"file_path": "test.py", "code_content": "print('hello world')"}),
        ("grayscale_test_executor", {"module_path": "src/tools/__init__.py"}),
        ("autonomous_iteration_pipeline", {"target_module_path": "src/tools/__init__.py", "modified_code_content": "print('test')"})
    ]
    
    all_callable = True
    for tool_name, params in tools_to_test:
        try:
            result = Tools.execute_tool(tool_name, **params)
            print(f"✅ 工具 {tool_name} 可正常调用，返回结果: {result[:100]}...")
        except Exception as e:
            print(f"❌ 工具 {tool_name} 调用失败: {str(e)}")
            all_callable = False
    
    return all_callable

if __name__ == "__main__":
    success = test_tool_callability()
    if success:
        print("\n🎉 所有高优先级工具均可正常调用")
        sys.exit(0)
    else:
        print("\n⚠️  部分高优先级工具无法调用")
        sys.exit(1)
