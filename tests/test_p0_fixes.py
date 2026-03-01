#!/usr/bin/env python3
"""
P0 问题修复验证测试

验证以下修复:
1. P0-1: 感知系统核心特征提取方法补全
2. P0-2: 记忆系统ID生成逻辑优化
3. P0-3: 各系统核心参数持久化机制
4. P0-4: 学习系统知识正确性校验
5. P0-5: 记忆系统长文本检索适配
"""

import sys
import os

sys.path.insert(0, '/workspace/projects')


def test_p0_1_perception_system():
    """测试 P0-1: 感知系统特征提取"""
    print("\n" + "="*60)
    print("🧪 测试 P0-1: 感知系统核心特征提取")
    print("="*60)
    
    try:
        from src.brain.perception_system import PerceptionSystem, ModalityType
        
        ps = PerceptionSystem()
        
        # 测试文本处理
        text = "This is a test sentence about Python programming."
        result = ps.process(text)
        assert "features" in result
        assert result["modality"] == "text"
        print("✅ 文本特征提取正常")
        
        # 测试代码处理
        code = """
def hello():
    print("Hello World")
"""
        result = ps.process(code)
        assert result["modality"] == "code"
        assert "language" in result["features"]
        print("✅ 代码特征提取正常")
        
        # 测试图像处理（模拟）
        # JPEG 文件头
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        result = ps.process(jpeg_header)
        assert result["modality"] == "image"
        assert result["features"]["format"] == "jpeg"
        print("✅ 图像特征提取正常")
        
        # 测试音频处理（模拟）
        # WAV 文件头
        wav_header = b'RIFF\x00\x00\x00\x00WAVE'
        result = ps.process(wav_header)
        assert result["modality"] == "audio"
        assert result["features"]["format"] == "wav"
        print("✅ 音频特征提取正常")
        
        # 测试新增特征
        text = "这是一个关于Python编程的测试文本，用于验证新特征。"
        result = ps.process(text)
        features = result["features"]
        assert "readability_score" in features
        assert "sentiment_polarity" in features
        assert "language_detected" in features
        print("✅ 新增文本特征正常")
        
        # 测试状态持久化
        ps.save_state("/tmp/perception_state.json")
        assert os.path.exists("/tmp/perception_state.json")
        print("✅ 感知系统状态保存正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_p0_2_memory_id_generation():
    """测试 P0-2: 记忆系统ID生成优化"""
    print("\n" + "="*60)
    print("🧪 测试 P0-2: 记忆系统ID生成(UUID+时间戳)")
    print("="*60)
    
    try:
        from src.brain.memory_system import MemorySystem
        import re
        
        ms = MemorySystem()
        
        # 测试ID生成格式
        id1 = ms._generate_memory_id("test")
        id2 = ms._generate_memory_id("test")
        
        # 验证格式: test_{uuid}_{timestamp}
        pattern = r'^test_[0-9a-f]{16}_\d{17}$'
        assert re.match(pattern, id1), f"ID格式错误: {id1}"
        assert re.match(pattern, id2), f"ID格式错误: {id2}"
        print(f"✅ ID格式正确: {id1}")
        
        # 验证唯一性
        assert id1 != id2, "生成的ID应该唯一"
        print("✅ ID唯一性验证通过")
        
        # 测试编码后ID格式
        memory_id = ms.encode("测试内容", memory_type="long_term")
        assert re.match(r'^long_term_[0-9a-f]{16}_\d{17}$', memory_id)
        print(f"✅ 编码ID格式正确: {memory_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_p0_3_memory_persistence():
    """测试 P0-3: 记忆系统持久化"""
    print("\n" + "="*60)
    print("🧪 测试 P0-3: 记忆系统状态持久化")
    print("="*60)
    
    try:
        from src.brain.memory_system import MemorySystem
        
        ms1 = MemorySystem()
        
        # 添加一些记忆
        id1 = ms1.encode("记忆内容1", memory_type="long_term", importance=0.8)
        id2 = ms1.encode("记忆内容2", memory_type="semantic", tags=["test"])
        
        # 保存状态
        state_file = "/tmp/memory_state.json"
        ms1.save_state(state_file)
        print(f"✅ 状态已保存: {state_file}")
        
        # 创建新实例并加载
        ms2 = MemorySystem()
        ms2.load_state(state_file)
        print("✅ 状态已加载")
        
        # 验证记忆恢复
        assert len(ms2.long_term_memory) == 2
        assert id1 in ms2.long_term_memory
        assert ms2.long_term_memory[id1].content == "记忆内容1"
        assert ms2.long_term_memory[id1].importance == 0.8
        print("✅ 长期记忆恢复正确")
        
        # 验证统计信息
        stats = ms2.get_memory_stats()
        assert stats["long_term"] == 2
        print("✅ 统计信息正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_p0_4_knowledge_validation():
    """测试 P0-4: 学习系统知识验证"""
    print("\n" + "="*60)
    print("🧪 测试 P0-4: 学习系统知识正确性校验")
    print("="*60)
    
    try:
        from src.brain.learning_system import KnowledgeLearningSystem, ValidatedKnowledge
        from src.brain.memory_system import MemorySystem
        
        memory = MemorySystem()
        
        # 模拟 LLM 客户端
        def mock_llm(prompt):
            return """[核心概念]
- Python: 一种高级编程语言，由Guido van Rossum于1991年创建
- Function: 可重用的代码块，接受输入参数并返回结果
- Programming Paradigm: 编程范式，如面向对象、函数式编程

[关键事实]
- Python 使用缩进表示代码块结构，这是与其他语言的主要区别
- Python 函数使用 def 关键字定义，支持默认参数和可变参数
- Python 支持多种编程范式，包括面向对象、函数式和过程式编程
- 根据 2024 年 Stack Overflow 调查，Python 是最受欢迎的编程语言之一

[相关概念]
Programming, Software Development, Data Science, Machine Learning

[应用场景]
Web开发使用 Django/Flask，数据分析使用 Pandas，人工智能使用 TensorFlow/PyTorch
"""
        
        # 创建学习系统（启用验证）
        kls = KnowledgeLearningSystem(
            memory_system=memory,
            llm_client=mock_llm,
            enable_validation=True,
            validation_confidence_threshold=0.7
        )
        
        # 测试知识验证
        from src.brain.learning_system import LearningTask
        
        task = LearningTask(
            query="什么是Python函数",
            context={},
            priority=5
        )
        
        # 执行学习
        result = kls.learn_now(task)
        print(f"✅ 学习执行结果: {result}")
        
        # 获取状态
        status = kls.get_learning_status()
        assert "validated_count" in status
        assert "rejected_count" in status
        assert "pending_review_count" in status
        assert status["validation_enabled"] == True
        print(f"✅ 验证状态: validated={status['validated_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_p0_5_long_text_retrieval():
    """测试 P0-5: 记忆系统长文本检索"""
    print("\n" + "="*60)
    print("🧪 测试 P0-5: 记忆系统长文本检索适配")
    print("="*60)
    
    try:
        from src.brain.memory_system import MemorySystem
        
        ms = MemorySystem()
        
        # 添加记忆
        ms.encode(
            "Python是一种高级编程语言，支持多种编程范式。",
            memory_type="long_term",
            tags=["python", "programming"]
        )
        ms.encode(
            "机器学习是人工智能的一个分支，使用统计方法让计算机从数据中学习。",
            memory_type="long_term",
            tags=["ml", "ai"]
        )
        
        # 测试长文本查询（超过100字符）
        long_query = """
我想了解Python编程语言相关的知识，特别是关于它在人工智能和机器学习领域的应用。
Python有许多强大的库，如TensorFlow、PyTorch、scikit-learn等，这些库使得Python
成为数据科学和机器学习的首选语言。请提供相关的详细信息。
"""
        assert len(long_query) > 100, "查询应该超过100字符"
        
        results = ms.retrieve(long_query, top_k=5)
        print(f"✅ 长文本查询成功，返回 {len(results)} 条结果")
        
        # 验证相关性
        if results:
            for mid, score in results:
                print(f"   - {mid[:20]}...: 相关性={score:.3f}")
        
        # 测试文本分段
        segments = ms._segment_long_text(long_query, max_segment_len=50)
        print(f"✅ 长文本分段: 分为 {len(segments)} 段")
        
        # 测试短文本查询（向后兼容）
        short_results = ms.retrieve("Python", top_k=3)
        print(f"✅ 短文本查询正常，返回 {len(short_results)} 条结果")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有 P0 测试"""
    print("\n" + "🔬 P0 问题修复验证测试".center(60, "="))
    
    results = {
        "P0-1 感知系统特征提取": test_p0_1_perception_system(),
        "P0-2 记忆系统ID生成优化": test_p0_2_memory_id_generation(),
        "P0-3 记忆系统持久化": test_p0_3_memory_persistence(),
        "P0-4 学习系统知识验证": test_p0_4_knowledge_validation(),
        "P0-5 长文本检索适配": test_p0_5_long_text_retrieval(),
    }
    
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
        print("\n🎉 所有 P0 问题修复验证通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
