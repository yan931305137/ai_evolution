import pytest
from src.storage.enhanced_memory import EnhancedMemory

# 初始化内存检索实例，用于测试
@pytest.fixture(scope="module")
def retrieval_instance():
 """测试前置：初始化信息检索实例，所有测试用例共享同一个实例"""
 memory = EnhancedMemory()
 # 预先存入测试用的基础数据
 test_docs = [
 "Python是一种广泛使用的解释型编程语言，适合数据分析、人工智能开发等场景",
 "信息检索是指从信息资源集合中查找与用户查询相关的信息的过程",
 "多步骤规划是AI Agent完成复杂任务的核心能力，需要拆解目标逐步执行",
 "代码生成工具可以根据自然语言描述生成对应的可执行代码片段",
 "OpenClaw Brain是具有自主进化能力的类脑AI助手，支持多任务处理",
 "机器学习算法需要大量的标注数据进行训练才能达到较好的效果",
 "向量数据库是专门用于存储和查询高维向量数据的数据库系统",
 "RAG（检索增强生成）技术可以有效提升大模型回答的准确性和时效性",
 "单元测试是软件开发过程中保证代码质量的重要环节",
 "自然语言处理是人工智能的一个重要分支，研究人与计算机的自然语言交互"
 ]
 for idx, doc in enumerate(test_docs):
 memory.add_memory(f"test_doc_{idx}", doc)
 return memory


def test_single_keyword_retrieval(retrieval_instance):
 """测试用例1：单关键词精准检索，验证基础检索能力"""
 result = retrieval_instance.search_memory("Python", top_k=1)
 assert len(result) > 0
 assert "Python" in result[0]["content"]


def test_multi_keyword_retrieval(retrieval_instance):
 """测试用例2：多关键词组合检索，验证多条件匹配能力"""
 result = retrieval_instance.search_memory("大模型 准确性", top_k=1)
 assert len(result) > 0
 assert "RAG" in result[0]["content"]


def test_fuzzy_matching_retrieval(retrieval_instance):
 """测试用例3：模糊匹配检索，验证同义词/相似语义匹配能力"""
 result = retrieval_instance.search_memory("程式语言", top_k=2) # 中文同义词：编程语言
 match_count = sum(1 for item in result if "编程语言" in item["content"])
 assert match_count >= 1


def test_long_text_query_retrieval(retrieval_instance):
 """测试用例4：长文本查询检索，验证长输入的语义理解能力"""
 long_query = "我想了解一种可以让人工智能根据用户给出的自然语言描述自动写出可以运行的程序代码的技术是什么"
 result = retrieval_instance.search_memory(long_query, top_k=1)
 assert len(result) > 0
 assert "代码生成" in result[0]["content"]


def test_empty_query_retrieval(retrieval_instance):
 """测试用例5：空查询检索，验证边界情况的处理能力"""
 result = retrieval_instance.search_memory("", top_k=5)
 # 空查询应该返回空结果或者不报错
 assert isinstance(result, list)


def test_chinese_content_retrieval(retrieval_instance):
 """测试用例6：纯中文内容检索，验证中文语义匹配能力"""
 result = retrieval_instance.search_memory("类脑AI助手", top_k=1)
 assert len(result) > 0
 assert "OpenClaw Brain" in result[0]["content"]


def test_english_content_retrieval(retrieval_instance):
 """测试用例7：纯英文关键词检索，验证英文内容匹配能力"""
 result = retrieval_instance.search_memory("RAG", top_k=1)
 assert len(result) > 0
 assert "检索增强生成" in result[0]["content"]


def test_mixed_keyword_retrieval(retrieval_instance):
 """测试用例8：中英文混合关键词检索，验证混合语义匹配能力"""
 result = retrieval_instance.search_memory("向量数据库 高维向量", top_k=1)
 assert len(result) > 0
 assert "向量数据库" in result[0]["content"]


def test_special_characters_retrieval(retrieval_instance):
 """测试用例9：带特殊字符的查询检索，验证特殊字符处理能力"""
 result = retrieval_instance.search_memory("RAG（检索增强生成）", top_k=1)
 assert len(result) > 0
 assert "RAG（检索增强生成）" in result[0]["content"]


def test_cross_document_retrieval(retrieval_instance):
 """测试用例10：跨文档相关内容检索，验证多结果召回能力"""
 result = retrieval_instance.search_memory("AI 开发", top_k=3)
 assert len(result) >= 2
 # 应该召回至少两个和AI开发相关的文档
 related_count = sum(1 for item in result if any(keyword in item["content"] for keyword in ["Python", "人工智能", "代码生成"]))
 assert related_count >= 2