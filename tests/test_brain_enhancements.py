#!/usr/bin/env python3
"""
Brain 增强模块集成测试

验证以下模块是否正常工作：
1. 扩展知识库 (ExtendedKnowledgeBase)
2. 知识图谱 (KnowledgeGraph)
3. 强化学习 (ReinforcementLearningSystem)
4. 增强版大脑 (EnhancedHumanLevelBrain)
"""

import sys
import asyncio

sys.path.insert(0, '/workspace/projects')


def test_extended_knowledge_base():
    """测试扩展知识库"""
    print("\n" + "="*60)
    print("🧪 测试: 扩展知识库 (ExtendedKnowledgeBase)")
    print("="*60)
    
    try:
        from src.brain.extended_knowledge_base import get_knowledge_base
        
        kb = get_knowledge_base()
        stats = kb.get_stats()
        
        print(f"✅ 知识库加载成功")
        print(f"   领域数量: {stats['total_domains']}")
        for domain, info in stats['domains'].items():
            print(f"   - {domain}: {info['count']} 条知识")
        
        # 测试查询
        test_queries = [
            "Python 报错了怎么办",
            "我感觉很焦虑",
            "怎么提高学习效率",
        ]
        
        print("\n📝 查询测试:")
        for query in test_queries:
            response = kb.get_response(query)
            if response:
                print(f"   Q: {query}")
                print(f"   A: {response[:80]}...")
            else:
                print(f"   Q: {query} → 无匹配")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph():
    """测试知识图谱"""
    print("\n" + "="*60)
    print("🧪 测试: 知识图谱 (KnowledgeGraph)")
    print("="*60)
    
    try:
        from src.brain.knowledge_graph import get_knowledge_graph
        
        kg = get_knowledge_graph()
        stats = kg.get_stats()
        
        print(f"✅ 知识图谱加载成功")
        print(f"   实体数量: {stats['entity_count']}")
        print(f"   关系数量: {stats['relation_count']}")
        print(f"   实体类型: {list(stats['entity_types'].keys())}")
        
        # 测试查询
        print("\n📝 查询测试:")
        
        # 测试实体查询
        entity = kg.get_entity_by_name("Python")
        if entity:
            print(f"   实体 [Python]: {entity.type}")
            summary = kg.get_knowledge_summary("Python")
            if summary:
                print(f"   摘要: {summary[:100]}...")
        
        # 测试关系推理
        relation = kg.infer_relation("Python", "Machine Learning")
        if relation:
            print(f"   推理 [Python → Machine Learning]: {relation}")
        
        # 测试相关概念
        related = kg.find_related_concepts("Python", depth=2)
        if related:
            print(f"   相关概念: {', '.join([r[0] for r in related[:3]])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reinforcement_learning():
    """测试强化学习系统"""
    print("\n" + "="*60)
    print("🧪 测试: 强化学习 (ReinforcementLearningSystem)")
    print("="*60)
    
    try:
        from src.brain.reinforcement_learning import (
            get_rl_system, State, Action
        )
        
        rl = get_rl_system()
        
        # 创建智能体
        agent = rl.create_agent("test_task")
        print(f"✅ RL 智能体创建成功")
        
        # 测试策略选择
        context = {
            "input": "测试输入",
            "has_code": False,
            "emotion": "neutral",
            "history_length": 0,
            "domain": "general",
        }
        
        strategies = ["L1_template", "L3_semantic", "L5_llm"]
        selected = rl.select_response_strategy(context, strategies)
        print(f"   选择策略: {selected}")
        
        # 测试学习
        rl.learn_from_feedback(
            task_id="test_task",
            context=context,
            selected_strategy=selected,
            reward=0.8
        )
        print(f"   学习完成: reward=0.8")
        
        # 获取统计
        stats = rl.get_learning_stats("test_task")
        print(f"   学习统计: epsilon={stats.get('epsilon', 'N/A'):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_brain():
    """测试增强版大脑"""
    print("\n" + "="*60)
    print("🧪 测试: 增强版大脑 (EnhancedHumanLevelBrain)")
    print("="*60)
    
    try:
        from src.brain.enhanced_human_level_brain import create_enhanced_brain
        
        # 创建增强大脑
        brain = create_enhanced_brain(
            start_as_infant=False,
            use_persistent_memory=False,
            enable_all_features=True,
        )
        
        print(f"✅ 增强大脑初始化成功")
        print(f"   扩展知识库: {'启用' if brain.enable_extended_knowledge else '禁用'}")
        print(f"   知识图谱: {'启用' if brain.enable_knowledge_graph else '禁用'}")
        print(f"   强化学习: {'启用' if brain.enable_rl else '禁用'}")
        print(f"   自我进化: {'启用' if brain.enable_self_evolution else '禁用'}")
        
        # 测试处理
        print("\n📝 处理测试:")
        
        test_inputs = [
            "你好",
            "Python 报错了",
            "什么是番茄工作法",
        ]
        
        for user_input in test_inputs:
            print(f"\n   输入: {user_input}")
            result = await brain.process_with_enhancement(user_input)
            print(f"   策略: {result['processing_level']}")
            print(f"   来源: {result['knowledge_sources']}")
            print(f"   响应: {result['response'][:60]}...")
        
        # 获取统计
        stats = brain.get_enhanced_stats()
        print(f"\n📊 增强统计:")
        print(f"   总交互数: {stats['processing_stats']['total_interactions']}")
        print(f"   本地命中: {stats['processing_stats']['local_hits']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🔬 Brain 增强模块集成测试".center(60, "="))
    
    results = {
        "扩展知识库": test_extended_knowledge_base(),
        "知识图谱": test_knowledge_graph(),
        "强化学习": test_reinforcement_learning(),
    }
    
    # 异步测试增强大脑
    results["增强大脑"] = asyncio.run(test_enhanced_brain())
    
    # 汇总结果
    print("\n" + "="*60)
    print("📋 测试结果汇总")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Brain 增强模块已就绪。")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
