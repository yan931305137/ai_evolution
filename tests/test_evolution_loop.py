"""
测试进化闭环系统 (Test Evolution Feedback Loop)
"""
import sys
import time
sys.path.insert(0, '.')

from src.utils.creativity import CreativeIdea
from src.utils.evolution_feedback_loop import EvolutionFeedbackLoop


def test_evolution_config():
    """测试进化配置"""
    print("\n" + "="*60)
    print("🧪 测试1: 进化目标配置")
    print("="*60)
    
    loop = EvolutionFeedbackLoop()
    loop.goal_manager.print_config()
    
    progress = loop.goal_manager.get_evolution_progress()
    print(f"\n总体进度: {progress['overall_progress']:.1f}%")
    
    return True


def test_idea_evaluation():
    """测试想法评估"""
    print("\n" + "="*60)
    print("🧪 测试2: 想法评估")
    print("="*60)
    
    test_ideas = [
        "优化文档处理算法，提升检索效率30%",
        "实现一个复杂的神经网络系统，彻底改变整个架构",
        "添加一个简单的配置选项，允许用户自定义主题颜色"
    ]
    
    loop = EvolutionFeedbackLoop()
    
    for idea_text in test_ideas:
        result = loop.evaluator.evaluate(idea_text)
        print(f"\n💡 {idea_text}")
        print(f"   综合得分: {result.overall_score:.1f}")
        print(f"   建议: {result.recommendation}")
        print(f"   投入: {result.estimated_effort} | 影响: {result.estimated_impact}")
    
    return True


def test_full_cycle():
    """测试完整周期"""
    print("\n" + "="*60)
    print("🧪 测试3: 完整进化周期")
    print("="*60)
    
    # 创建一些测试想法
    ideas = [
        CreativeIdea(
            idea="优化文档处理算法，提升检索效率30%", 
            method="combinatorial",
            source_concepts=["文档处理", "算法优化"],
            novelty_score=60.0,
            feasibility_score=80.0,
            value_score=85.0,
            timestamp=time.time(),
            emotional_context="积极"
        ),
        CreativeIdea(
            idea="实现缓存机制减少重复计算", 
            method="divergent",
            source_concepts=["缓存", "性能优化"],
            novelty_score=50.0,
            feasibility_score=90.0,
            value_score=75.0,
            timestamp=time.time(),
            emotional_context="专注"
        ),
        CreativeIdea(
            idea="添加用户个性化配置选项", 
            method="divergent",
            source_concepts=["配置", "个性化"],
            novelty_score=40.0,
            feasibility_score=95.0,
            value_score=70.0,
            timestamp=time.time(),
            emotional_context="好奇"
        ),
    ]
    
    loop = EvolutionFeedbackLoop()
    results = loop.run_full_cycle(ideas)
    
    print("\n" + "="*60)
    print("周期完成!")
    
    # 显示统计
    stats = loop.get_full_report()
    print(f"\n进化统计:")
    print(f"  创造: {stats['evolution_stats']['total_ideas_created']}")
    print(f"  评估: {stats['evolution_stats']['total_ideas_evaluated']}")
    print(f"  应用: {stats['evolution_stats']['total_ideas_applied']}")
    
    return True


def test_cli_commands():
    """测试CLI命令"""
    print("\n" + "="*60)
    print("🧪 测试4: CLI命令")
    print("="*60)
    
    from click.testing import CliRunner
    from src.utils.evolution_commands import show_status, evaluate_idea
    
    runner = CliRunner()
    
    # 测试状态命令
    result = runner.invoke(show_status)
    print("\n状态命令输出:")
    print(result.output)
    
    # 测试评估命令
    result = runner.invoke(evaluate_idea, ["优化文档处理算法，提升检索效率30%"])
    print("\n评估命令输出:")
    print(result.output)
    
    return True


def main():
    """主测试函数"""
    print("\n" + "🚀"*30)
    print("进化闭环系统测试")
    print("🚀"*30)
    
    tests = [
        ("进化配置", test_evolution_config),
        ("想法评估", test_idea_evaluation),
        ("完整周期", test_full_cycle),
        ("CLI命令", test_cli_commands),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {name} 测试通过")
                passed += 1
            else:
                print(f"\n❌ {name} 测试失败")
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
