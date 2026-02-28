#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高优先级工具集成验证脚本
"""

import sys
sys.path.insert(0, '.')

from src.tools import Tools

def test_tools_registration():
    """测试三个高优工具是否已正确注册"""
    print("=== 测试高优先级工具注册 ===")
    
    # 检查工具是否存在
    tools_to_check = [
        "autonomous_iteration_pipeline",
        "code_security_verification", 
        "grayscale_test_executor"
    ]
    
    all_exist = True
    for tool_name in tools_to_check:
        if hasattr(Tools, tool_name):
            print(f"✅ 工具 {tool_name} 已正确注册")
        else:
            print(f"❌ 工具 {tool_name} 未注册")
            all_exist = False
    
    # 测试工具描述是否包含三个工具
    tool_descriptions = Tools.get_tool_descriptions()
    for tool_name in tools_to_check:
        if tool_name in tool_descriptions:
            print(f"✅ 工具 {tool_name} 描述已加入提示词")
        else:
            print(f"❌ 工具 {tool_name} 描述未加入提示词")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    success = test_tools_registration()
    if success:
        print("\n🎉 所有高优先级工具集成验证通过")
        sys.exit(0)
    else:
        print("\n⚠️  部分高优先级工具集成未通过")
        sys.exit(1)
