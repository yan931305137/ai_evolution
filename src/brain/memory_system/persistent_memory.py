#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化记忆系统 - 基于ChromaDB的长期记忆存储

让Brain的记忆能够跨越会话持久保存，就像人类的长时记忆一样。
"""
import json
import hashlib
import numpy as np
import logging
from typing import Any, Dict, List, Optional, Tuple, Tuple
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(name="PersistentMemory")

# 导入现有的记忆系统
from src.brain.memory_system import MemorySystem, MemoryEntry
from src.brain.common import MemoryType

# 尝试导入ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("⚠️  ChromaDB不可用，持久化记忆将使用JSON文件存储")


class PersistentMemorySystem(MemorySystem):
    """
    持久化记忆系统
    
    在原有MemorySystem基础上，添加ChromaDB持久化存储能力。
    支持：
    - 长期记忆的持久化存储
    - 基于语义相似度的记忆检索
    - 自动保存/加载
    """
    
    def __init__(
        self,
        capacity: int = 10000,
        persist_directory: str = "data/chroma_db/brain_memory",
        collection_name: str = "brain_long_term_memory",
        auto_persist: bool = True
    ):
        """
        初始化持久化记忆系统
        
        Args:
            capacity: 内存中缓存的最大记忆数
            persist_directory: ChromaDB持久化目录
            collection_name: 集合名称
            auto_persist: 是否自动持久化（每次编码后自动保存）
        """
        super().__init__(capacity=capacity)
        
        # 确保路径是绝对路径，且基于项目根目录，而非相对路径
        # 如果是相对路径，转换为基于项目根目录的绝对路径
        path_obj = Path(persist_directory)
        if not path_obj.is_absolute():
            # 获取项目根目录 (假设 src 是项目根目录下的子目录)
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.persist_directory = root_dir / persist_directory
        else:
            self.persist_directory = path_obj
            
        self.collection_name = collection_name
        self.auto_persist = auto_persist
        
        # 初始化ChromaDB或JSON存储
        self.chroma_client = None
        self.collection = None
        self.json_storage_path = self.persist_directory / f"{collection_name}.json"
        self._init_storage()
        
        # 加载已有记忆
        self._load_memories()
        
    def _init_storage(self):
        """初始化存储（ChromaDB优先，否则用JSON）"""
        if CHROMA_AVAILABLE:
            try:
                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self.chroma_client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self.persist_directory),
                    anonymized_telemetry=False
                ))
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Brain's long-term memory storage"}
                )
                logger.info(f"✅ 持久化记忆系统已初始化（ChromaDB）")
                return
            except Exception as e:
                logger.warning(f"⚠️  ChromaDB初始化失败: {e}，将使用JSON存储")
        
        # Fallback到JSON存储
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 持久化记忆系统已初始化（JSON文件）")
        logger.info(f"   存储路径: {self.json_storage_path}")
    
    def _load_memories(self):
        """加载已有记忆（支持ChromaDB和JSON两种格式）"""
        if self.collection is not None:
            self._load_from_chroma()
        else:
            self._load_from_json()
    
    def _load_from_json(self):
        """从JSON文件加载记忆"""
        if not self.json_storage_path.exists():
            logger.info("📭 没有历史记忆（JSON存储）")
            return
        
        try:
            with open(self.json_storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memories_data = data.get("memories", [])
            logger.info(f"📚 正在从JSON加载 {len(memories_data)} 条历史记忆...")
            
            for mem_data in memories_data:
                memory_id, memory = self._dict_to_memory(mem_data)
                self.long_term_memory[memory_id] = memory
            
            logger.info(f"✅ 已从JSON恢复 {len(memories_data)} 条记忆")
            
        except Exception as e:
            logger.error(f"⚠️  从JSON加载记忆失败: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示（简单版本）
        
        实际应用中可以使用更复杂的embedding模型
        """
        # 简单的词袋模型作为fallback
        words = text.lower().split()
        # 创建一个简单的哈希向量
        vector = np.zeros(128)
        for word in words:
            hash_val = hashlib.md5(word.encode()).hexdigest()
            for i in range(128):
                if hash_val[i % 32] in '0123456789':
                    vector[i] += 1
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()
    
    def _memory_to_document(self, memory: MemoryEntry) -> Dict:
        """将MemoryEntry转换为ChromaDB文档格式"""
        return {
            "id": memory.memory_id,
            "content": str(memory.content),
            "metadata": {
                "memory_id": memory.memory_id,
                "memory_type": memory.memory_type.value if hasattr(memory.memory_type, 'value') else str(memory.memory_type),
                "created_at": memory.created_at.isoformat() if isinstance(memory.created_at, datetime) else str(memory.created_at),
                "importance": memory.importance,
                "access_count": memory.access_count,
                "relevance_score": memory.relevance_score,
                "tags": json.dumps(memory.tags) if memory.tags else "[]",
                "emotional_valence": memory.emotional_valence,
                "associations": json.dumps(memory.associations) if memory.associations else "[]"
            },
            "embedding": self._get_embedding(str(memory.content))
        }
    
    def _document_to_memory(self, doc: Dict) -> Tuple[str, MemoryEntry]:
        """将ChromaDB文档转换回MemoryEntry"""
        metadata = doc.get("metadata", {})
        
        # 解析时间
        created_at_str = metadata.get("created_at", datetime.now().isoformat())
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except:
            created_at = datetime.now()
        
        # 解析tags
        try:
            tags = json.loads(metadata.get("tags", "[]"))
        except:
            tags = []
        
        # 解析associations
        try:
            associations = json.loads(metadata.get("associations", "[]"))
        except:
            associations = []
        
        memory_id = metadata.get("memory_id", doc.get("id", "unknown"))
        
        memory = MemoryEntry(
            content=doc.get("content", ""),
            memory_type="long_term",  # 从持久化加载的都是长期记忆
            importance=float(metadata.get("importance", 0.5)),
            emotional_tag={},
            timestamp=created_at,
            access_count=int(metadata.get("access_count", 0)),
            associations=associations,
            relevance_score=float(metadata.get("relevance_score", 0.5)),
            tags=tags,
            emotional_valence=float(metadata.get("emotional_valence", 0.0))
        )
        
        return memory_id, memory
    
    def _save_to_chroma(self, memory: MemoryEntry):
        """保存单个记忆到ChromaDB"""
        if self.collection is None:
            return
            
        try:
            doc = self._memory_to_document(memory)
            self.collection.add(
                ids=[doc["id"]],
                documents=[doc["content"]],
                metadatas=[doc["metadata"]],
                embeddings=[doc["embedding"]]
            )
        except Exception as e:
            logger.error(f"⚠️  保存记忆到ChromaDB失败: {e}")
    
    def _memory_to_dict(self, memory: MemoryEntry, memory_id: str = None) -> Dict:
        """将MemoryEntry转换为字典（用于JSON存储）"""
        return {
            "memory_id": memory_id or "unknown",
            "content": str(memory.content),
            "memory_type": memory.memory_type if isinstance(memory.memory_type, str) else str(memory.memory_type),
            "created_at": memory.timestamp.isoformat() if isinstance(memory.timestamp, datetime) else str(memory.timestamp),
            "importance": memory.importance,
            "access_count": memory.access_count,
            "relevance_score": memory.relevance_score,
            "tags": memory.tags,
            "emotional_valence": memory.emotional_valence,
            "associations": memory.associations,
            "emotional_tag": memory.emotional_tag
        }
    
    def _dict_to_memory(self, data: Dict) -> Tuple[str, MemoryEntry]:
        """将字典转换回MemoryEntry（用于JSON加载）"""
        # 解析时间
        created_at_str = data.get("created_at") or data.get("timestamp", datetime.now().isoformat())
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except:
            created_at = datetime.now()
        
        memory_id = data.get("memory_id", "unknown")
        
        memory = MemoryEntry(
            content=data.get("content", ""),
            memory_type=data.get("memory_type", "long_term"),
            importance=float(data.get("importance", 0.5)),
            emotional_tag=data.get("emotional_tag", {}),
            timestamp=created_at,
            access_count=int(data.get("access_count", 0)),
            associations=data.get("associations", []),
            relevance_score=float(data.get("relevance_score", 0.5)),
            tags=data.get("tags", []),
            emotional_valence=float(data.get("emotional_valence", 0.0))
        )
        
        return memory_id, memory
    
    def _save_to_json(self, memory: MemoryEntry, memory_id: str = None):
        """保存单个记忆到JSON文件"""
        try:
            # 读取现有数据
            data = {"memories": []}
            if self.json_storage_path.exists():
                with open(self.json_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 添加新记忆（避免重复）
            memories = data.get("memories", [])
            
            # 如果没有提供memory_id，尝试从字典中查找
            if memory_id is None:
                for mid, mem in self.long_term_memory.items():
                    if mem is memory:
                        memory_id = mid
                        break
            
            if memory_id is None:
                memory_id = f"long_term_{hash(str(memory.content)) & 0xFFFFFFFF}"
            
            memory_dict = self._memory_to_dict(memory, memory_id)
            
            # 检查是否已存在
            existing_ids = {m.get("memory_id") for m in memories}
            if memory_id not in existing_ids:
                memories.append(memory_dict)
                data["memories"] = memories
                
                # 写回文件
                with open(self.json_storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"⚠️  保存记忆到JSON失败: {e}")
    
    def _load_from_chroma(self):
        """从ChromaDB加载所有记忆"""
        if self.collection is None:
            return
            
        try:
            # 获取所有记忆
            results = self.collection.get()
            
            if not results or not results.get("ids"):
                logger.info("📭 没有历史记忆")
                return
            
            count = len(results["ids"])
            logger.info(f"📚 正在加载 {count} 条历史记忆...")
            
            for i, memory_id in enumerate(results["ids"]):
                doc = {
                    "id": memory_id,
                    "content": results["documents"][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                }
                mid, memory = self._document_to_memory(doc)
                self.long_term_memory[mid] = memory
            
            logger.info(f"✅ 已恢复 {count} 条记忆")
            
        except Exception as e:
            logger.error(f"⚠️  从ChromaDB加载记忆失败: {e}")
    
    def encode(
        self,
        content: Any,
        memory_type: str = "short_term",
        importance: float = 0.5,
        emotional_tag: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        编码新记忆（增强版，支持持久化）
        """
        # 调用父类方法编码记忆
        memory_id = super().encode(
            content=content,
            memory_type=memory_type,
            importance=importance,
            emotional_tag=emotional_tag,
            tags=tags
        )
        
        # 如果是长期记忆，自动持久化
        if memory_type == "long_term" and self.auto_persist and memory_id in self.long_term_memory:
            memory = self.long_term_memory[memory_id]
            if self.collection is not None:
                self._save_to_chroma(memory)
            else:
                self._save_to_json(memory, memory_id)
            logger.info(f"💾 记忆已持久化: {str(content)[:50]}...")
        
        return memory_id
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[MemoryEntry, float]]:
        """
        基于语义相似度检索记忆（增强版）
        """
        # 首先尝试从ChromaDB进行语义检索
        if self.collection is not None:
            try:
                query_embedding = self._get_embedding(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k * 2, 50),  # 多检索一些，后续再过滤
                    include=["metadatas", "documents", "distances"]
                )
                
                if results and results.get("ids") and results["ids"][0]:
                    chroma_memories = []
                    for i, memory_id in enumerate(results["ids"][0]):
                        if memory_id in self.long_term_memory:
                            memory = self.long_term_memory[memory_id]
                            # 转换距离为相似度分数 (Chroma返回的是L2距离)
                            distance = results["distances"][0][i] if results.get("distances") else 1.0
                            similarity = max(0, 1 - distance)
                            chroma_memories.append((memory, similarity))
                    
                    if chroma_memories:
                        # 按相似度排序
                        chroma_memories.sort(key=lambda x: x[1], reverse=True)
                        return chroma_memories[:top_k]
                        
            except Exception as e:
                logger.error(f"⚠️  ChromaDB检索失败，回退到内存检索: {e}")
        
        # 回退到父类的检索方法（父类返回的是memory_id，需要转换为MemoryEntry）
        parent_results = super().retrieve(query, top_k)
        converted_results = []
        for memory_id, score in parent_results:
            if memory_id in self.long_term_memory:
                converted_results.append((self.long_term_memory[memory_id], score))
        return converted_results
    
    def persist_all(self):
        """手动触发所有记忆的持久化"""
        count = 0
        for memory_id, memory in self.long_term_memory.items():
            if self.collection is not None:
                self._save_to_chroma(memory)
            else:
                self._save_to_json(memory, memory_id)
            count += 1
        
        logger.info(f"💾 已持久化 {count} 条长期记忆")
    
    def clear_persisted_memory(self):
        """清空持久化存储的记忆（危险操作！）"""
        if self.collection is not None:
            try:
                self.chroma_client.delete_collection(self.collection_name)
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Brain's long-term memory storage"}
                )
            except Exception as e:
                logger.error(f"⚠️  清空ChromaDB记忆失败: {e}")
        
        # 清空JSON文件
        if self.json_storage_path.exists():
            try:
                self.json_storage_path.unlink()
                logger.info("🗑️  JSON记忆文件已删除")
            except Exception as e:
                logger.error(f"⚠️  删除JSON文件失败: {e}")
        
        # 清空内存中的长期记忆
        self.long_term_memory.clear()
        logger.info("🗑️  持久化记忆已清空")
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        chroma_count = 0
        if self.collection is not None:
            try:
                chroma_count = self.collection.count()
            except:
                pass
        
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_memory_count": len(self.long_term_memory),
            "persisted_count": chroma_count,
            "storage_path": str(self.persist_directory),
            "auto_persist": self.auto_persist
        }
