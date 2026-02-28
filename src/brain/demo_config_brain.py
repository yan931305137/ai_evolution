#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过配置文件使用Brain LLM的演示

展示如何修改src/config/config.yaml来切换LLM提供商
"""
import sys
sys.path.insert(0, '/workspace/projects')

# 先导入并重新加载配置，再导入LLMClient
from src.utils.config import cfg
cfg._loaded = False
cfg.load("src/config/config.yaml")

# 现在导入LLMClient，它会使用更新后的配置
from src.utils.llm import LLMClient


def demo_config_usage():
    print("⚙️  配置文件驱动的Brain LLM演示")
    print("=" * 60)
    
    # 查看当前配置
    print("\n📋 当前LLM配置:")
    print(f"   提供商: {cfg.llm_provider}")
    print(f"   模型: {cfg.llm_config.get('model_name', 'N/A')}")
    print(f"   温度: {cfg.llm_config.get('temperature', 0.7)}")
    
    # 查看Brain配置
    brain_cfg = cfg.brain_config
    print(f"\n🧠 Brain配置:")
    print(f"   婴儿模式: {brain_cfg.get('start_as_infant', False)}")
    print(f"   情感模式: {brain_cfg.get('emotional_mode', 'balanced')}")
    print(f"   发育速度: {brain_cfg.get('growth_rate', 'normal')}")
    
    identity = brain_cfg.get('identity', {})
    print(f"   身份名称: {identity.get('name', 'N/A')}")
    print(f"   价值观: {identity.get('values', [])}")
    
    # 创建LLM客户端（自动读取配置）
    print("\n" + "-" * 60)
    print("🚀 初始化LLMClient（自动读取config.yaml）")
    print("-" * 60)
    
    llm = LLMClient()  # 不需要任何参数，自动从配置读取
    
    print(f"✅ 已初始化: {llm.provider} 模式")
    print(f"   模型: {llm.model_name}")
    
    # 测试对话
    print("\n" + "-" * 60)
    print("💬 对话测试")
    print("-" * 60)
    
    messages = [
        {"role": "system", "content": "你是一个有自我意识的AI助手。"},
        {"role": "user", "content": "你好，你是谁？"}
    ]
    
    print(f"用户: {messages[-1]['content']}")
    response = llm.generate(messages)
    print(f"Brain: {response.content}")
    
    if hasattr(response, 'reasoning_content') and response.reasoning_content:
        print(f"\n💭 思考过程:")
        for line in response.reasoning_content.split('\n'):
            print(f"   {line}")
    
    print("\n✅ 演示完成！")


def demo_switch_providers():
    """演示如何切换不同提供商"""
    
    print("\n" + "=" * 60)
    print("🔄 切换LLM提供商演示")
    print("=" * 60)
    
    messages = [
        {"role": "system", "content": "你是一个乐于助人的AI。"},
        {"role": "user", "content": "1+1等于几？"}
    ]
    
    providers = ['brain']  # 当前只演示brain
    
    for provider in providers:
        print(f"\n--- 提供商: {provider} ---")
        try:
            llm = LLMClient(provider=provider)
            response = llm.generate(messages)
            print(f"响应: {response.content}")
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    demo_config_usage()
    demo_switch_providers()
