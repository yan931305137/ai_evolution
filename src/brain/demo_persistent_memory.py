#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brain持久化记忆演示

展示Brain如何记住之前的对话，并在重启后恢复记忆。
"""
import sys
import asyncio
sys.path.insert(0, '/workspace/projects')

from src.brain.human_level_brain import HumanLevelBrain


async def demo_persistent_memory():
    """演示持久化记忆功能"""
    
    print("=" * 60)
    print("🧠 Brain持久化记忆演示")
    print("=" * 60)
    
    # 场景1：首次启动Brain，创建一些记忆
    print("\n📌 场景1：首次启动Brain，学习新知识")
    print("-" * 60)
    
    brain = HumanLevelBrain(
        start_as_infant=False,  # 使用成年大脑
        use_persistent_memory=True,  # 启用持久化记忆
        memory_storage_path="data/chroma_db/brain_memory_demo"
    )
    
    # 模拟学习经历
    learning_experiences = [
        {
            "cognitive": "用户告诉我他喜欢科幻电影，特别是《星际穿越》",
            "energy": 0.8,
            "event": {"relevance_to_self": 0.7, "expected_outcome": 0.6}
        },
        {
            "cognitive": "用户说他住在上海，工作在浦东新区",
            "energy": 0.7,
            "event": {"relevance_to_self": 0.8, "expected_outcome": 0.5}
        },
        {
            "cognitive": "用户提到他的宠物狗叫'豆豆'，今年3岁了",
            "energy": 0.9,
            "event": {"relevance_to_self": 0.6, "expected_outcome": 0.7}
        }
    ]
    
    print("\n📝 学习新信息...")
    for i, exp in enumerate(learning_experiences, 1):
        print(f"  {i}. {exp['cognitive']}")
        result = await brain.experience(exp)
        
        # 将重要信息编码为长期记忆
        brain.memory.encode(
            content=exp["cognitive"],
            memory_type="long_term",
            importance=0.8,
            tags=["user_preference", "personal_info"]
        )
    
    # 查看记忆统计
    print("\n📊 当前记忆统计:")
    stats = brain.get_memory_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 手动触发持久化
    brain.persist_memories()
    
    # 场景2：模拟Brain重启，检查记忆是否恢复
    print("\n" + "=" * 60)
    print("🔄 场景2：Brain重启，检查记忆恢复")
    print("=" * 60)
    
    # 删除brain引用，模拟重启
    del brain
    print("\n💤 Brain已'关闭'（删除实例）")
    
    # 重新创建Brain实例（应该是全新的实例，但记忆应该恢复）
    print("\n🌅 Brain重新启动...")
    brain2 = HumanLevelBrain(
        start_as_infant=False,
        use_persistent_memory=True,
        memory_storage_path="data/chroma_db/brain_memory_demo"
    )
    
    # 查看恢复后的记忆统计
    print("\n📊 恢复后的记忆统计:")
    stats2 = brain2.get_memory_stats()
    for key, value in stats2.items():
        print(f"   {key}: {value}")
    
    # 场景3：检索记忆
    print("\n" + "=" * 60)
    print("🔍 场景3：基于语义检索记忆")
    print("=" * 60)
    
    queries = [
        "用户喜欢什么电影？",
        "用户住在哪里？",
        "用户的宠物是什么？",
        "用户的工作地点"
    ]
    
    for query in queries:
        print(f"\n❓ 查询: {query}")
        memories = brain2.recall_memories(query, top_k=2)
        
        if memories:
            print("   💡 回忆:")
            for mem in memories:
                print(f"      - {mem['content'][:60]}... (相似度: {mem['similarity']:.2f})")
        else:
            print("   😕 没有找到相关记忆")
    
    # 场景4：继续学习新信息
    print("\n" + "=" * 60)
    print("📚 场景4：继续学习新信息")
    print("=" * 60)
    
    new_experience = {
        "cognitive": "用户说他最喜欢的科幻作家是刘慈欣",
        "energy": 0.8,
        "event": {"relevance_to_self": 0.75, "expected_outcome": 0.6}
    }
    
    print(f"\n学习新信息: {new_experience['cognitive']}")
    await brain2.experience(new_experience)
    brain2.memory.encode(
        content=new_experience["cognitive"],
        memory_type="long_term",
        importance=0.85,
        tags=["user_preference", "hobby", "literature"]
    )
    
    # 再次查询，看看是否能关联到之前的记忆
    print("\n❓ 查询: 用户喜欢什么类型的书？")
    memories = brain2.recall_memories("用户喜欢的作家和书籍", top_k=3)
    if memories:
        print("   💡 回忆:")
        for mem in memories:
            print(f"      - {mem['content'][:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print("=" * 60)
    print("\n💡 关键发现:")
    print("   1. Brain可以记住用户信息（喜好、地址、宠物等）")
    print("   2. 重启后记忆自动恢复")
    print("   3. 支持基于语义的模糊检索")
    print("   4. 新旧记忆可以关联")
    
    # 清理演示数据（可选）
    # brain2.memory.clear_persisted_memory()
    # print("\n🗑️  演示数据已清理")


if __name__ == "__main__":
    asyncio.run(demo_persistent_memory())
