"""
Enhanced Hybrid Brain 对比测试

展示增强版Hybrid相比于基础Hybrid的优势
"""
import time
from src.utils.enhanced_hybrid_brain import EnhancedHybridBrain


def test_scenarios():
    """测试场景"""
    return [
        # L1: 模板匹配场景
        {"name": "问候", "messages": [{"role": "user", "content": "你好！"}]},
        {"name": "感谢", "messages": [{"role": "user", "content": "谢谢你！"}]},
        {"name": "告别", "messages": [{"role": "user", "content": "再见！"}]},
        
        # L3: 语义检索场景
        {"name": "重复问题", "messages": [{"role": "user", "content": "你是做什么的？"}]},
        
        # L4: 本地推理场景
        {"name": "知识查询", "messages": [{"role": "user", "content": "什么是OpenClaw？"}]},
        {"name": "追问", "messages": [
            {"role": "user", "content": "Brain能学习吗？"},
            {"role": "assistant", "content": "是的，Brain有学习能力。"},
            {"role": "user", "content": "为什么？"}
        ]},
        
        # L5: LLM场景
        {"name": "复杂问题", "messages": [{"role": "user", "content": "帮我分析一下AI的未来发展趋势，从技术、伦理、社会三个维度。"}]},
    ]


def run_comparison():
    """运行对比测试"""
    print("=" * 60)
    print("🧠⚡ Enhanced Hybrid Brain 能力展示")
    print("=" * 60)
    
    # 初始化
    print("\n[初始化] 创建Enhanced Hybrid Brain...")
    try:
        client = EnhancedHybridBrain(start_as_infant=False)
        print("✅ 初始化成功\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试场景
    scenarios = test_scenarios()
    
    print(f"[测试] 共 {len(scenarios)} 个场景\n")
    print("-" * 60)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n场景 {i}/{len(scenarios)}: {scenario['name']}")
        print(f"输入: {scenario['messages'][-1]['content'][:50]}...")
        
        try:
            start = time.time()
            response = client.generate(scenario['messages'])
            elapsed = (time.time() - start) * 1000
            
            # 显示结果
            brain_state = response.brain_state or {}
            level = brain_state.get('processing_level', 'unknown')
            latency = brain_state.get('latency_ms', 0)
            
            level_emoji = {
                'template': '📝',
                'semantic': '🔍',
                'inference': '🧠',
                'llm': '🤖'
            }.get(level, '❓')
            
            print(f"处理级别: {level_emoji} {level.upper()}")
            print(f"响应延迟: {latency:.0f}ms")
            print(f"回复预览: {response.content[:60]}...")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 打印统计
    print("\n" + "=" * 60)
    client.print_stats()


def demonstrate_savings():
    """展示成本节省"""
    print("\n" + "=" * 60)
    print("💰 成本节省分析")
    print("=" * 60)
    
    # 假设数据
    total_requests = 1000
    
    # 基础Hybrid：全部走LLM
    base_cost = total_requests * 0.002  # 假设每次$0.002
    base_latency = total_requests * 800  # 假设每次800ms
    
    # Enhanced Hybrid：70%本地处理
    local_ratio = 0.70
    llm_requests = int(total_requests * (1 - local_ratio))
    enhanced_cost = llm_requests * 0.002
    
    # 本地延迟平均20ms，LLM延迟800ms
    avg_local_latency = 20
    avg_llm_latency = 800
    enhanced_latency = (
        total_requests * local_ratio * avg_local_latency +
        llm_requests * avg_llm_latency
    )
    
    print(f"\n假设场景: {total_requests} 次对话")
    print(f"\n基础Hybrid模式:")
    print(f"  LLM调用: {total_requests} 次")
    print(f"  预估成本: ${base_cost:.2f}")
    print(f"  总延迟: {base_latency/1000:.1f}秒")
    
    print(f"\nEnhanced Hybrid模式 (70%本地):")
    print(f"  LLM调用: {llm_requests} 次 (-{total_requests-llm_requests})")
    print(f"  本地处理: {int(total_requests*local_ratio)} 次")
    print(f"  预估成本: ${enhanced_cost:.2f}")
    print(f"  总延迟: {enhanced_latency/1000:.1f}秒")
    
    print(f"\n节省效果:")
    print(f"  💵 成本节省: ${base_cost - enhanced_cost:.2f} ({(1-enhanced_cost/base_cost)*100:.0f}%)")
    print(f"  ⚡ 延迟降低: {(1-enhanced_latency/base_latency)*100:.0f}%")
    print(f"  🌍 API调用减少: {total_requests - llm_requests} 次")


def show_architecture():
    """展示架构"""
    print("\n" + "=" * 60)
    print("🏗️ Enhanced Hybrid 架构")
    print("=" * 60)
    
    arch = """
    用户输入
       │
       ▼
    ┌─────────────────────────────────────────────────────┐
    │                 Intent Router (意图路由)             │
    │         本地识别意图，无需API调用                     │
    └─────────────────────────────────────────────────────┘
       │
       ▼
    ┌─────────────────────────────────────────────────────┐
    │              LLM Call Decider (决策器)               │
    │    智能决策使用哪种处理级别                           │
    └─────────────────────────────────────────────────────┘
       │
       ├── L1: 模板匹配 (<1ms) ──> Template Engine
       │
       ├── L3: 语义检索 (<10ms) ──> Semantic Retriever  
       │
       ├── L4: 本地推理 (<50ms) ──> Inference Engine
       │
       └── L5: LLM生成 (>500ms) ──> HybridBrainClient
       │
       ▼
    响应输出
    
    统计:
    - L1-L4: 本地处理，零API成本，毫秒级响应
    - L5: 仅在必要时调用LLM
    """
    print(arch)


if __name__ == "__main__":
    # 展示架构
    show_architecture()
    
    # 运行对比测试
    try:
        run_comparison()
    except Exception as e:
        print(f"\n测试需要完整环境: {e}")
        print("（这是正常的，展示代码结构即可）")
    
    # 展示成本节省
    demonstrate_savings()
    
    print("\n" + "=" * 60)
    print("✅ 展示完成")
    print("=" * 60)
