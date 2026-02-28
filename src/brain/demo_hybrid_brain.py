#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
类脑系统 + LLM 混合架构示例

演示类脑系统如何在实时响应时检测知识缺口，
并在后台（闲时）调用LLM补充知识。
"""

import asyncio
import time
from src.brain.orchestrator import get_brain, reset_brain
from src.brain.learning_system import create_simple_llm_client


async def demo():
    """演示类脑 + LLM 混合架构"""
    
    print("=" * 60)
    print("类脑系统 + LLM 后台学习演示")
    print("=" * 60)
    
    # 1. 获取大脑实例
    brain = get_brain()
    brain.debug = True
    
    # 2. 设置LLM客户端（实际使用时替换为真实API）
    llm_client = create_simple_llm_client()
    brain.set_llm_client(llm_client)
    
    # 3. 启动后台学习
    brain.start_background_learning()
    print("\n[系统] 后台学习线程已启动")
    
    # 4. 模拟用户对话（触发知识缺口）
    print("\n" + "-" * 60)
    print("阶段1: 用户对话（实时响应）")
    print("-" * 60)
    
    queries = [
        "你好，请介绍一下自己",
        "什么是Transformer架构？",  # 知识缺口，会触发学习
        "今天天气怎么样？",
        "量子计算的原理是什么？",   # 知识缺口，会触发学习
        "谢谢你的回答",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[对话 {i}] 用户: {query}")
        
        # 类脑系统处理
        response = await brain.process(query, context={
            "conversation_id": "demo_001",
            "goal": "answer_question"
        })
        
        # 显示结果
        print(f"[对话 {i}] 系统: 行动={response.action}, 置信度={response.confidence:.2f}")
        
        # 显示知识缺口检测
        gap_info = response.metadata.get("knowledge_gap", {})
        if gap_info.get("detected"):
            print(f"[对话 {i}] ⚠️ 检测到知识缺口: {gap_info.get('topic', 'Unknown')}")
            print(f"[对话 {i}]    置信度: {gap_info.get('confidence', 0):.2f}")
            print(f"[对话 {i}]    已加入学习队列")
        else:
            print(f"[对话 {i}] ✓ 知识充足，无需学习")
        
        print(f"[对话 {i}] 学习队列大小: {response.metadata.get('learning_queue_size', 0)}")
        
        # 模拟对话间隔
        time.sleep(0.5)
    
    # 5. 等待系统闲置，触发后台学习
    print("\n" + "-" * 60)
    print("阶段2: 等待后台学习（模拟闲置时间）")
    print("-" * 60)
    
    print("\n[系统] 等待系统闲置...")
    time.sleep(6)  # 等待超过idle_threshold(5秒)
    
    # 查看学习状态
    status = brain.get_state_summary()
    learning_status = status.get("learning_system", {})
    
    print(f"\n[学习状态]")
    print(f"  队列大小: {learning_status.get('queue_size', 0)}")
    print(f"  已学习任务: {learning_status.get('learned_count', 0)}")
    print(f"  失败任务: {learning_status.get('failed_count', 0)}")
    print(f"  是否闲置: {learning_status.get('is_idle', False)}")
    
    # 6. 再次询问之前的问题（应该已经学到了）
    print("\n" + "-" * 60)
    print("阶段3: 再次询问（验证学习效果）")
    print("-" * 60)
    
    print("\n[对话] 用户: 什么是Transformer架构？")
    response2 = await brain.process("什么是Transformer架构？", context={
        "conversation_id": "demo_002",
        "goal": "answer_question"
    })
    
    print(f"[对话] 系统: 行动={response2.action}, 置信度={response2.confidence:.2f}")
    
    gap_info2 = response2.metadata.get("knowledge_gap", {})
    if gap_info2.get("detected"):
        print(f"[对话] ⚠️ 仍然有知识缺口")
    else:
        print(f"[对话] ✓ 知识已补充（从记忆中检索）")
    
    # 7. 显示最终状态
    print("\n" + "=" * 60)
    print("最终状态摘要")
    print("=" * 60)
    
    final_status = brain.get_state_summary()
    print(f"\n处理周期: {final_status.get('processing_cycles', 0)}")
    print(f"多巴胺水平: {final_status.get('dopamine_level', 0):.2f}")
    print(f"工作记忆大小: {final_status.get('working_memory_size', 0)}")
    print(f"长期记忆大小: {final_status.get('long_term_memory_size', 0)}")
    
    learning = final_status.get("learning_system", {})
    print(f"\n学习系统:")
    print(f"  总学习数: {learning.get('learned_count', 0)}")
    print(f"  失败数: {learning.get('failed_count', 0)}")
    print(f"  跳过重複: {learning.get('skipped_duplicates', 0)}")
    
    # 8. 停止后台学习
    brain.stop_background_learning()
    print("\n[系统] 后台学习线程已停止")
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


def demo_simple_llm_client():
    """演示如何使用真实的LLM API"""
    print("\n" + "=" * 60)
    print("真实LLM客户端示例")
    print("=" * 60)
    
    # 示例：使用OpenAI API
    example_code = '''
import openai

def create_openai_client(api_key: str):
    client = openai.OpenAI(api_key=api_key)
    
    def llm_client(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个知识提取助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    
    return llm_client

# 使用
brain = get_brain()
brain.set_llm_client(create_openai_client("your-api-key"))
brain.start_background_learning()
'''
    
    print(example_code)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())
    
    # 显示真实API使用示例
    demo_simple_llm_client()
