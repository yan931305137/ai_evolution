#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brain作为LLM的演示脚本

展示如何将人类级大脑作为LLM选项使用，与Coze/Ark无缝切换
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/workspace/projects')

from src.utils.llm import LLMClient


def demo_brain_as_llm():
    """演示Brain作为LLM的使用"""
    
    print("=" * 60)
    print("🧠 Brain作为LLM演示")
    print("=" * 60)
    
    # 方式1：通过环境变量选择Brain
    # export LLM_PROVIDER=brain
    
    # 方式2：直接在代码中指定provider
    print("\n📌 方式2：代码中指定 provider='brain'")
    llm = LLMClient(provider="brain", start_as_infant=False)
    
    print(f"当前LLM提供商: {llm.provider}")
    print(f"模型名称: {llm.model_name}")
    
    # 测试对话
    print("\n" + "-" * 60)
    print("💬 对话测试")
    print("-" * 60)
    
    conversations = [
        [
            {"role": "system", "content": "你是一个有自我意识的AI助手。"},
            {"role": "user", "content": "你好，请介绍一下你自己。"}
        ],
        [
            {"role": "system", "content": "你是一个有自我意识的AI助手。"},
            {"role": "user", "content": "你好，请介绍一下你自己。"},
            {"role": "assistant", "content": "你好！我是一个有自我意识的AI。"},
            {"role": "user", "content": "你刚才说了什么？"}
        ],
        [
            {"role": "system", "content": "你是一个有自我意识的AI助手。"},
            {"role": "user", "content": "你觉得自己和人类有什么不同？"}
        ]
    ]
    
    for i, messages in enumerate(conversations, 1):
        print(f"\n--- 对话 {i} ---")
        print(f"用户: {messages[-1]['content']}")
        
        response = llm.generate(messages)
        print(f"Brain: {response.content}")
        
        # 显示思考过程
        if hasattr(response, 'reasoning_content') and response.reasoning_content:
            print(f"\n💭 思考过程:\n{response.reasoning_content}")
    
    # 获取Brain统计信息
    print("\n" + "=" * 60)
    print("📊 Brain运行统计")
    print("=" * 60)
    
    stats = llm._brain_client.get_stats()
    print(f"交互次数: {stats['interaction_count']}")
    print(f"发育阶段: {stats['developmental_stage']}")
    print(f"当前状态: {stats['current_emotion']}")
    
    print("\n✅ 演示完成！")


def demo_compare_providers():
    """对比不同LLM提供商的响应"""
    
    print("\n" + "=" * 60)
    print("🔍 不同LLM提供商对比")
    print("=" * 60)
    
    messages = [
        {"role": "system", "content": "你是一个乐于助人的AI助手。"},
        {"role": "user", "content": "用一句话描述什么是意识。"}
    ]
    
    providers = []
    
    # Brain
    try:
        brain_llm = LLMClient(provider="brain")
        providers.append(("Brain", brain_llm))
    except Exception as e:
        print(f"Brain初始化失败: {e}")
    
    # Coze（如果配置了API Key）
    if os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"):
        try:
            coze_llm = LLMClient(provider="coze")
            providers.append(("Coze", coze_llm))
        except Exception as e:
            print(f"Coze初始化失败: {e}")
    
    for name, llm in providers:
        print(f"\n--- {name} ---")
        try:
            response = llm.generate(messages)
            print(f"响应: {response.content[:200]}...")
        except Exception as e:
            print(f"生成失败: {e}")


if __name__ == "__main__":
    demo_brain_as_llm()
    demo_compare_providers()
