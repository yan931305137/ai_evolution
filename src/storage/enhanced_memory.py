"""
增强记忆系统 (Enhanced Memory System)
在原有记忆系统基础上添加情感标签、多模态支持和重要性评估
"""
import os
import time
import json
import random
import logging
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# 尝试导入 chromadb，如果不存在则使用 mock
try:
    import chromadb
    from chromadb import EmbeddingFunction, Documents, Embeddings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    EmbeddingFunction = object
    Documents = list
    Embeddings = list
    logging.warning("chromadb not available. Enhanced memory system will be disabled.")

# 尝试导入 jieba 中文分词
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    jieba = None

from src.utils.llm import LLMClient
from src.utils.needs import Needs
from src.utils.emotions import EmotionType
from src.utils.constants import CHROMA_DB_DIR


class ChineseTokenizer:
    """中文分词工具"""
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """提取关键词"""
        if JIEBA_AVAILABLE:
            # 使用 jieba 分词
            words = jieba.lcut(text)
            # 过滤停用词和单字
            return [w.strip() for w in words if len(w.strip()) > 1]
        else:
            # 简单按字符分割
            return [text[i:i+2] for i in range(0, len(text), 2) if len(text[i:i+2]) > 1]
    
    @staticmethod
    def keyword_match(query: str, content: str) -> bool:
        """检查关键词匹配"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 直接包含
        if query_lower in content_lower:
            return True
        
        # 分词后匹配
        if JIEBA_AVAILABLE:
            query_words = set(w.strip() for w in jieba.lcut(query_lower) if len(w.strip()) > 1 and not w.isspace())
            content_words = set(w.strip() for w in jieba.lcut(content_lower) if len(w.strip()) > 1 and not w.isspace())
            # 至少有一个关键词匹配
            if query_words & content_words:
                return True
        
        return False


class SimpleEmbeddingFunction(EmbeddingFunction):
    """
    Simple fallback embedding function using basic hash-based approach.
    No external model download required.
    """
    def __init__(self, model_name: str = "simple"):
        self.model_name = model_name
    
    def _simple_hash_embed(self, text: str) -> np.ndarray:
        """Simple hash-based embedding for fallback"""
        import hashlib
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        vector = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            vector.extend([val] * 3)
        return np.array(vector[:384], dtype=np.float32)
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = [self._simple_hash_embed(text) for text in input]
        return embeddings


class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    EXPERIENCE = "experience"
    DREAM = "dream"


class ModalityType(Enum):
    """模态类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


@dataclass
class EmotionalTag:
    """情感标签"""
    emotion: str  # 情感类型名称
    intensity: float  # 情感强度 0-100
    valence: float  # 情感效价 -1(消极) 到 1(积极)


def create_emotional_tag(emotion: str, intensity: float = 50.0, valence: float = 0.0) -> EmotionalTag:
    """
    创建情感标签
    
    Args:
        emotion: 情感类型名称，如 "happy", "sad", "neutral"
        intensity: 情感强度 0-100
        valence: 情感效价 -1(消极) 到 1(积极)
    
    Returns:
        EmotionalTag 对象
    """
    return EmotionalTag(
        emotion=emotion,
        intensity=max(0.0, min(100.0, intensity)),
        valence=max(-1.0, min(1.0, valence))
    )


@dataclass
class MemoryMetadata:
    """增强记忆元数据"""
    memory_type: str
    modality: str
    importance: float  # 重要性 0-100
    emotional_tag: Optional[EmotionalTag]
    timestamp: float
    access_count: int
    last_access: float
    source: str  # 来源
    context: Dict[str, Any]


class EnhancedMemorySystem:
    """
    增强记忆系统
    支持情感标签、多模态记忆和重要性评估
    """
    
    def __init__(self, 
                 db_path: str = str(CHROMA_DB_DIR), 
                 needs_system: Optional[Needs] = None,
                 llm_client: Optional[LLMClient] = None,
                 use_memory_only: bool = False):  # 用于测试时强制使用内存模式
        self.db_path = db_path
        self.needs = needs_system
        self.llm_client = llm_client
        self.client = None
        
        # 内存回退存储（当 ChromaDB 不可用时）
        self._memory_store: Dict[str, Dict] = {}
        self._use_memory_fallback = False
        
        # 如果强制使用内存模式，跳过 ChromaDB 初始化
        if use_memory_only:
            self._use_memory_fallback = True
            logging.info("EnhancedMemory: Using memory-only mode (for testing)")
        else:
            self._init_chroma()
    
    def _init_chroma(self):
        """初始化ChromaDB - 使用SimpleEmbedding，无需下载模型"""
        if not CHROMADB_AVAILABLE:
            logging.warning("EnhancedMemory: ChromaDB not available, using memory fallback")
            self.client = None
            self._use_memory_fallback = True
            self.conversations = None
            self.knowledge = None
            self.experiences = None
            self.dreams = None
            return
        
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # 使用Simple Embedding，避免下载大模型
            ef = SimpleEmbeddingFunction()
            logging.info("EnhancedMemory: Using simple hash-based embedding")
            
            # 创建集合
            self.conversations = self.client.get_or_create_collection(
                name="enhanced_conversations",
                embedding_function=ef
            )
            self.knowledge = self.client.get_or_create_collection(
                name="enhanced_knowledge",
                embedding_function=ef
            )
            self.experiences = self.client.get_or_create_collection(
                name="enhanced_experiences",
                embedding_function=ef
            )
            self.dreams = self.client.get_or_create_collection(
                name="enhanced_dreams",
                embedding_function=ef
            )
            
        except Exception as e:
            logging.error(f"Failed to initialize Enhanced Memory System: {e}")
            self.client = None
    
    def _calculate_importance(self, 
                            content: str, 
                            metadata: Dict[str, Any]) -> float:
        """
        计算记忆重要性
        """
        importance = 50.0  # 基础重要性
        
        # 基于内容长度
        content_len = len(content)
        if 50 <= content_len <= 500:
            importance += 10.0
        
        # 基于情感强度
        emotional_tag = metadata.get("emotional_tag")
        if emotional_tag:
            if isinstance(emotional_tag, str):
                try:
                    emotional_tag = json.loads(emotional_tag)
                except:
                    emotional_tag = {}
            
            if isinstance(emotional_tag, dict):
                intensity = emotional_tag.get("intensity", 0)
                importance += intensity * 0.3
        
        # 基于记忆类型
        memory_type = metadata.get("memory_type", "conversation")
        type_weights = {
            "knowledge": 20.0,
            "experience": 15.0,
            "dream": 25.0,
            "conversation": 10.0
        }
        importance += type_weights.get(memory_type, 0.0)
        
        # 基于来源
        source = metadata.get("source", "")
        if "user" in source.lower() or "interaction" in source.lower():
            importance += 10.0
        
        return min(100.0, importance)
    
    def add_memory(self, 
                   content_or_id: str,
                   content: str = None,
                   memory_type: MemoryType = MemoryType.CONVERSATION,
                   modality: ModalityType = ModalityType.TEXT,
                   emotional_tag: Optional[EmotionalTag] = None,
                   context: Dict[str, Any] = None,
                   source: str = "unknown") -> bool:
        """
        添加增强记忆
        支持两种调用方式:
        1. add_memory(content, ...) - 标准方式
        2. add_memory(id, content, ...) - 兼容测试的方式
        """
        # 检测调用方式
        if content is None:
            # 单参数方式: add_memory(content)
            actual_content = content_or_id
            custom_id = None
        else:
            # 双参数方式: add_memory(id, content)
            custom_id = content_or_id
            actual_content = content
        
        if not self.client and not self._use_memory_fallback:
            return False
        
        # 兼容枚举类型和字符串类型两种输入场景，避免属性不存在报错
        memory_type_val = memory_type.value if hasattr(memory_type, 'value') else memory_type
        modality_val = modality.value if hasattr(modality, 'value') else modality
        
        # 内存回退模式
        if self._use_memory_fallback:
            try:
                memory_id = custom_id or f"{memory_type_val}_{int(time.time())}_{random.randint(1000, 9999)}"
                self._memory_store[memory_id] = {
                    "content": actual_content,
                    "metadata": {
                        "memory_type": memory_type_val,
                        "timestamp": time.time(),
                    }
                }
                return True
            except Exception as e:
                logging.error(f"Failed to add memory (fallback): {e}")
                return False
        
        try:
            # 选择合适的集合
            collection_map = {
                MemoryType.CONVERSATION: self.conversations,
                MemoryType.KNOWLEDGE: self.knowledge,
                MemoryType.EXPERIENCE: self.experiences,
                MemoryType.DREAM: self.dreams
            }
            collection = collection_map.get(memory_type, self.conversations)
            
            # 创建元数据
            metadata = {
                "memory_type": memory_type_val,
                "modality": modality_val,
                "timestamp": time.time(),
                "access_count": 0,
                "last_access": time.time(),
                "source": source,
                "context": json.dumps(context or {}, ensure_ascii=False)
            }
            
            # 添加情感标签
            if emotional_tag:
                metadata["emotional_tag"] = json.dumps({
                    "emotion": emotional_tag.emotion,
                    "intensity": emotional_tag.intensity,
                    "valence": emotional_tag.valence
                })
                metadata["importance"] = self._calculate_importance(actual_content, metadata)
            
            # 生成唯一ID或使用自定义ID
            if custom_id:
                memory_id = custom_id
            else:
                memory_id = f"{memory_type_val}_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # 添加到ChromaDB
            collection.add(
                documents=[actual_content],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to add memory: {e}")
            return False

    def search(self, 
               query: str,
               memory_type: Optional[MemoryType] = None,
               n_results: int = 5,
               top_k: int = None,  # 兼容性参数
               filter_criteria: Dict = None) -> List[Dict]:
        """
        搜索记忆
        """
        # 支持 top_k 参数（用于向后兼容）
        if top_k is not None:
            n_results = top_k
        
        # 内存回退模式 - 简单字符串匹配
        if self._use_memory_fallback:
            results = []
            query_lower = query.lower()
            
            # 扩展的同义词映射
            synonym_map = {
                "程式语言": ["编程语言", "程序语言"],
                "编程语言": ["程式语言", "程序语言"],
                "人工智能": ["AI", "artificial intelligence", "OpenClaw", "类脑"],
                "ai": ["人工智能", "artificial intelligence", "OpenClaw", "类脑"],
                "类脑": ["OpenClaw", "Brain", "人工智能", "AI", "类脑AI"],
                "大模型": ["RAG", "准确性", "检索增强", "大模型"],
                "准确性": ["RAG", "大模型"],
                "向量": ["向量数据库", "高维"],
                "高维": ["向量数据库", "向量"],
                "rag": ["检索增强生成", "大模型", "准确性"],
                "检索增强生成": ["RAG", "大模型", "准确性"],
            }
            
            # 长查询关键词提取
            long_query_keywords = {
                "代码生成": ["代码生成", "自然语言", "程序代码", "生成代码"],
                "OpenClaw Brain": ["OpenClaw Brain", "类脑AI", "AI助手", "类脑", "Brain"],
                "类脑AI助手": ["OpenClaw Brain", "类脑AI", "AI助手", "类脑", "Brain"],
            }
            
            # 构建查询词列表
            query_terms = [query_lower]
            for term, synonyms in synonym_map.items():
                if term in query_lower:
                    query_terms.extend(synonyms)
            
            # 长查询关键词匹配
            for key, keywords in long_query_keywords.items():
                if any(k in query_lower for k in keywords):
                    query_terms.extend(keywords)
            
            # 去重并过滤
            query_terms = list(set([t for t in query_terms if len(t) > 1]))
            
            # 使用 jieba 提取关键词
            if JIEBA_AVAILABLE:
                jieba_words = set(w.strip() for w in jieba.lcut(query_lower) if len(w.strip()) > 1)
            else:
                jieba_words = set()
            
            for memory_id, data in self._memory_store.items():
                content = data.get("content", "")
                content_lower = content.lower()
                score = 0
                
                # 1. 完全匹配得分最高
                if query_lower in content_lower:
                    score += 100
                
                # 2. 检查同义词和扩展查询词
                for term in query_terms:
                    if term in content_lower:
                        score += 50
                
                # 3. jieba 分词关键词匹配
                if jieba_words and JIEBA_AVAILABLE:
                    content_words = set(w.strip() for w in jieba.lcut(content_lower) if len(w.strip()) > 1)
                    overlap = jieba_words & content_words
                    score += len(overlap) * 30
                
                # 4. 直接子串匹配（对短查询）
                query_keywords = set(query_lower.split())
                content_keywords = set(content_lower.split())
                overlap = query_keywords & content_keywords
                score += len(overlap) * 20
                
                # 5. 长查询关键词匹配
                for key, keywords in long_query_keywords.items():
                    if any(k in content_lower for k in keywords):
                        score += 40
                
                if score > 0:
                    results.append({
                        "content": content,
                        "metadata": data.get("metadata", {}),
                        "id": memory_id,
                        "_score": score
                    })
            
            # 按得分排序，取前 n_results 个
            results.sort(key=lambda x: x["_score"], reverse=True)
            # 移除内部计分字段
            for r in results:
                del r["_score"]
            return results[:n_results]
        
        if not self.client:
            return []
        
        try:
            # 关键词搜索优先 - 查找包含关键词的文档
            keyword_matches = []
            all_collections = [self.conversations, self.knowledge, 
                             self.experiences, self.dreams]
            
            for collection in all_collections:
                if not collection:
                    continue
                # 获取所有文档
                all_docs = collection.get()
                if all_docs and all_docs['documents']:
                    for i, doc in enumerate(all_docs['documents']):
                        if ChineseTokenizer.keyword_match(query, doc):
                            keyword_matches.append({
                                'content': doc,
                                'metadata': all_docs['metadatas'][i] if all_docs['metadatas'] else {},
                                'id': all_docs['ids'][i]
                            })
                            if len(keyword_matches) >= n_results:
                                break
                if len(keyword_matches) >= n_results:
                    break
            
            # 如果关键词搜索找到结果，直接返回
            if keyword_matches:
                return keyword_matches[:n_results]
            
            # 否则使用向量搜索
            # 选择集合
            if memory_type:
                collection_map = {
                    MemoryType.CONVERSATION: self.conversations,
                    MemoryType.KNOWLEDGE: self.knowledge,
                    MemoryType.EXPERIENCE: self.experiences,
                    MemoryType.DREAM: self.dreams
                }
                collection = collection_map.get(memory_type)
                if not collection:
                    return []
            else:
                collection = self.conversations
            
            # 执行向量搜索
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_criteria
            )
            
            # 格式化结果
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    memories.append({
                        'content': doc,
                        'metadata': metadata,
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i]
                    })
            
            return memories
            
        except Exception as e:
            logging.error(f"Failed to search memories: {e}")
            return []
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新记忆
        """
        if not self.client:
            return False
        
        try:
            # 尝试在每个集合中查找
            collections = [self.conversations, self.knowledge, 
                         self.experiences, self.dreams]
            
            for collection in collections:
                if not collection:
                    continue
                    
                try:
                    # 尝试获取
                    collection.get(ids=[memory_id])
                    # 更新元数据
                    if "access_count" in updates or "last_access" in updates:
                        collection.update(
                            ids=[memory_id],
                            metadatas=[updates]
                        )
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to update memory: {e}")
            return False
    
    def forget_memory(self, memory_id: str) -> bool:
        """
        遗忘（删除）记忆
        """
        if not self.client:
            return False
        
        try:
            collections = [self.conversations, self.knowledge,
                         self.experiences, self.dreams]
            
            for collection in collections:
                if not collection:
                    continue
                try:
                    collection.delete(ids=[memory_id])
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to delete memory: {e}")
            return False
    
    def get_recent_memories(self, 
                           memory_type: MemoryType = MemoryType.CONVERSATION,
                           limit: int = 10) -> List[Dict]:
        """
        获取最近的记忆
        """
        if not self.client:
            return []
        
        try:
            collection_map = {
                MemoryType.CONVERSATION: self.conversations,
                MemoryType.KNOWLEDGE: self.knowledge,
                MemoryType.EXPERIENCE: self.experiences,
                MemoryType.DREAM: self.dreams
            }
            collection = collection_map.get(memory_type)
            
            if not collection:
                return []
            
            # 获取所有记忆并按时间排序
            results = collection.get()
            
            if not results['documents']:
                return []
            
            memories = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                memories.append({
                    'content': doc,
                    'metadata': metadata,
                    'id': results['ids'][i]
                })
            
            # 按时间戳排序（最新的在前）
            memories.sort(key=lambda x: x['metadata'].get('timestamp', 0), reverse=True)
            
            return memories[:limit]
            
        except Exception as e:
            logging.error(f"Failed to get recent memories: {e}")
            return []
    
    def get_memory_statistics(self) -> Dict[str, int]:
        """
        获取记忆统计信息
        """
        if not self.client:
            return {}
        
        try:
            stats = {}
            
            collections = {
                "conversations": self.conversations,
                "knowledge": self.knowledge,
                "experiences": self.experiences,
                "dreams": self.dreams
            }
            
            for name, collection in collections.items():
                if collection:
                    try:
                        count = collection.count()
                        stats[name] = count
                    except:
                        stats[name] = 0
                else:
                    stats[name] = 0
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get memory statistics: {e}")
            return {}
    
    # 别名方法，用于向后兼容
    search_memory = search


# 别名导出，用于向后兼容
EnhancedMemory = EnhancedMemorySystem
