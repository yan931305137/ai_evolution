import os
import tempfile
import pytest
from src.storage.memory import MemorySystem

# 测试使用内存模式，避免污染生产数据
@pytest.fixture
def memory_system():
    ms = MemorySystem(db_path=":memory:")
    yield ms
    # 测试结束后自动清理
    if ms.client:
        del ms.client

class TestMemorySystem:
    def test_initialization(self, memory_system):
        '''测试内存系统初始化是否正常'''
        assert memory_system.client is not None
        assert memory_system.conversations is not None
        assert memory_system.knowledge is not None
    
    def test_add_and_retrieve_conversation(self, memory_system):
        '''测试对话记忆的存储和检索功能'''
        # 存储测试数据
        test_content = "用户询问如何优化系统性能，回答建议使用缓存和异步处理"
        memory_system.conversations.add(
            documents=[test_content],
            metadatas=[{"role": "user", "timestamp": "2026-02-27", "importance": 0.8}],
            ids=["test_conv_001"]
        )
        
        # 检索测试
        results = memory_system.conversations.query(
            query_texts=["如何优化系统性能"],
            n_results=1
        )
        
        assert len(results['documents'][0]) > 0
        assert "优化系统性能" in results['documents'][0][0]
    
    def test_add_and_retrieve_knowledge(self, memory_system):
        '''测试知识库记忆的存储和检索功能'''
        # 存储测试数据
        test_content = "Python代码优化技巧：1. 使用生成器减少内存占用；2. 避免不必要的循环；3. 使用内置函数提升性能"
        memory_system.knowledge.add(
            documents=[test_content],
            metadatas=[{"source": "python_optimization_guide", "importance": 0.9}],
            ids=["test_know_001"]
        )
        
        # 检索测试
        results = memory_system.knowledge.query(
            query_texts=["Python代码优化方法"],
            n_results=1
        )
        
        assert len(results['documents'][0]) > 0
        assert "Python代码优化技巧" in results['documents'][0][0]
    
    def test_merge_duplicate_memories(self, memory_system):
        '''测试重复记忆合并功能是否正常工作'''
        # 添加两条高度相似的记忆
        content1 = "系统优化的方法包括缓存、异步、数据库索引优化"
        content2 = "系统优化的方法包括缓存、异步、数据库索引优化"
        
        memory_system.conversations.add(
            documents=[content1, content2],
            metadatas=[{"importance": 0.7}, {"importance": 0.6}],
            ids=["test_dup_001", "test_dup_002"]
        )
        
        initial_count = memory_system.conversations.count()
        assert initial_count == 2
        
        # 执行合并
        memory_system.merge_duplicate_memories(similarity_threshold=0.95, max_process_count=10)
        
        final_count = memory_system.conversations.count()
        assert final_count == 1
    
    def test_clean_expired_memories(self, memory_system):
        '''测试过期记忆清理功能'''
        # 添加一条已过期的记忆
        expired_content = "这是一条已过期的测试记忆"
        memory_system.conversations.add(
            documents=[expired_content],
            metadatas=[{"expire_time": "2020-01-01T00:00:00", "importance": 0.5}],
            ids=["test_expired_001"]
        )
        
        initial_count = memory_system.conversations.count()
        assert initial_count == 1
        
        # 执行清理
        memory_system.clean_expired_memories()
        
        final_count = memory_system.conversations.count()
        assert final_count == 0
