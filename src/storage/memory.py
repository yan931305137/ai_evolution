import os
import datetime
import chromadb
import logging
import numpy as np
from typing import List, Dict, Optional, Any
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.utils import embedding_functions
from apscheduler.schedulers.background import BackgroundScheduler

from src.utils.llm import LLMClient

from src.utils.needs import Needs

class SilentSentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function that disables the tqdm progress bar
    to prevent thread crashes on Windows.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("sentence_transformers is not installed.")

    def __call__(self, input: Documents) -> Embeddings:
        # Explicitly disable progress bar
        embeddings = self.model.encode(input, convert_to_numpy=True, show_progress_bar=False)
        # Convert to list of numpy arrays as expected by Chroma
        return [np.array(embedding, dtype=np.float32) for embedding in embeddings]


class SimpleEmbeddingFunction(EmbeddingFunction):
    """
    Simple fallback embedding function using basic TF-IDF-like approach.
    Used when sentence-transformers is not available.
    """
    def __init__(self, model_name: str = "simple"):
        self.model_name = model_name
    
    def _simple_hash_embed(self, text: str) -> np.ndarray:
        """Simple hash-based embedding for fallback"""
        # Create a fixed-size embedding using character hash
        import hashlib
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        # Convert to 384-dim vector (matching default model size)
        vector = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            vector.extend([val] * 3)  # Repeat to get 384 dimensions
        return np.array(vector[:384], dtype=np.float32)
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = [self._simple_hash_embed(text) for text in input]
        return embeddings

from src.utils.constants import CHROMA_DB_DIR

class MemorySystem:
    """
    Manages long-term memory using ChromaDB (Vector Database).
    Stores conversation history and project knowledge.
    """
    
    def __init__(self, db_path: str = str(CHROMA_DB_DIR), needs_system: Optional[Needs] = None):
        self.db_path = db_path
        self.client = None
        self.needs = needs_system # Link to vital system for energy rewards
        
        # 设置模型缓存目录到项目内部，避免每次重新下载
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cache_dir = os.path.join(project_root, '.cache', 'chroma')
        os.environ.setdefault('CHROMA_CACHE_DIR', cache_dir)
        
        try:
            # 支持内存模式测试和持久化模式生产
            if db_path == ":memory:":
                self.client = chromadb.EphemeralClient()
            else:
                # Initialize persistent client
                self.client = chromadb.PersistentClient(path=db_path)
            
            # Try to use sentence-transformers, fallback to simple embedding
            try:
                ef = SilentSentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
                logging.info("Using sentence-transformers for embeddings")
            except Exception as e:
                logging.warning(f"Failed to load sentence-transformers ({e}), using simple embedding")
                ef = SimpleEmbeddingFunction()
            
            self.conversations = self.client.get_or_create_collection(
                name="conversations",
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"}  # 明确使用余弦距离，保证相似度计算准确
            )
            self.knowledge = self.client.get_or_create_collection(
                name="knowledge",
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"}  # 明确使用余弦距离，保证相似度计算准确
            )
            
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB: {e}")
            # Fallback or raise error depending on strictness
            self.client = None
        
        # 初始化定时任务，定期清理过期记忆和合并重复记忆
        self.scheduler = None
        if self.client:
            try:
                self.scheduler = BackgroundScheduler()
                # 调整为每周日凌晨3点执行记忆维护任务，降低CPU占用频率
                self.scheduler.add_job(
                    self.maintain_memories,
                    'cron',
                    day_of_week=6,
                    hour=3,
                    minute=0,
                    id='memory_maintenance'
                )
                self.scheduler.start()
                logging.info("Memory maintenance scheduler started successfully")
            except Exception as e:
                logging.error(f"Failed to start memory scheduler: {e}")
    
    def maintain_memories(self):
        """执行记忆维护任务：清理过期记忆、合并重复记忆"""
        if not self.client:
            return
        
        logging.info("Starting memory maintenance task")
        self.clean_expired_memories()
        self.merge_duplicate_memories()
        logging.info("Memory maintenance task completed")
    
    def clean_expired_memories(self):
        """清理所有过期的记忆"""
        if not self.client:
            return
        
        now = datetime.datetime.now().isoformat()
        for collection in [self.conversations, self.knowledge]:
            try:
                # 查询所有过期的记忆
                expired = collection.get(
                    where={"expire_time": {"$lt": now}}
                )
                if expired and expired['ids']:
                    collection.delete(ids=expired['ids'])
                    logging.info(f"Cleaned {len(expired['ids'])} expired memories from {collection.name} collection")
            except Exception as e:
                logging.error(f"Failed to clean expired memories from {collection.name}: {e}")
    
    def merge_duplicate_memories(self, similarity_threshold: float = 0.95, max_process_count: int = 100):
        """合并相似度极高的重复记忆，优化CPU占用：限制每次处理数量，避免全量O(n²)扫描"""
        if not self.client:
            return
        
        for collection in [self.conversations, self.knowledge]:
            try:
                # 只获取最近的max_process_count条记忆进行去重，避免全量扫描导致的高CPU占用
                total_count = collection.count()
                if total_count == 0:
                    continue
                # 按时间倒序获取最近的记忆（ID包含时间信息，取最新的）
                all_memories = collection.get(
                    limit=min(max_process_count, total_count),
                    include=['documents', 'metadatas', 'embeddings']
                )
                if not all_memories or not all_memories['documents']:
                    continue
                
                to_delete = set()
                n = len(all_memories['documents'])
                # 预计算所有向量的范数，避免重复计算
                norms = [np.linalg.norm(emb) for emb in all_memories['embeddings']]
                
                for i in range(n):
                    if i in to_delete:
                        continue
                    emb_i = all_memories['embeddings'][i]
                    norm_i = norms[i]
                    for j in range(i + 1, n):
                        if j in to_delete:
                            continue
                        emb_j = all_memories['embeddings'][j]
                        norm_j = norms[j]
                        # 计算余弦相似度，使用预计算的范数减少重复计算
                        similarity = np.dot(emb_i, emb_j) / (norm_i * norm_j) if norm_i > 0 and norm_j > 0 else 0
                        if similarity >= similarity_threshold:
                            # 保留重要度更高的记忆，删除另一个
                            imp_i = all_memories['metadatas'][i].get('importance', 0)
                            imp_j = all_memories['metadatas'][j].get('importance', 0)
                            to_delete.add(j if imp_i >= imp_j else i)
                
                if to_delete:
                    delete_ids = [all_memories['ids'][idx] for idx in to_delete]
                    collection.delete(ids=delete_ids)
                    logging.info(f"Merged {len(delete_ids)} duplicate memories from {collection.name} collection (processed {n} entries)")
            except Exception as e:
                logging.error(f"Failed to merge duplicate memories from {collection.name}: {e}")

    def consolidate_memories(self, llm_client: LLMClient) -> List[str]:
        """
        Consolidate recent conversation memories into general knowledge.
        This simulates 'dreaming' or 'offline processing'.
        Consumes significant energy (brain power) but rewards with knowledge (food).
        """
        if self.needs:
             # Dreaming costs energy
             self.needs.consume_energy(5.0)
        
        if not self.client:
            return []
            
        try:
            # 1. Fetch recent raw conversations (limit to last 10 for demo)
            # In a real system, you'd track which memories have been consolidated
            count = self.conversations.count()
            if count == 0:
                return []
                
            results = self.conversations.peek(limit=10) 
            if not results or not results['documents']:
                return []
                
            raw_texts = results['documents']
            context = "\n---\n".join(raw_texts)
            
            # 2. Ask LLM to summarize into facts/knowledge
            prompt = f"""
            You are a Knowledge Manager.
            
            Below are raw conversation logs from an AI agent's recent activities:
            {context}
            
            Task: Extract 1-3 key facts, concepts, or technical knowledge points that are worth preserving long-term.
            Ignore trivial interactions like "Hello" or "Done".
            Focus on technical details, successful tool usages, or environment specifics.
            
            Return ONLY a JSON list of strings.
            Example: ["The 'requests' library requires a timeout.", "Project config is at config/config.yaml"]
            """
            
            messages = [{"role": "user", "content": prompt}]
            
            # Use stream_generate but collect all content, add 3 retries with exponential backoff
            import time
            content = ""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    stream = llm_client.stream_generate(messages)
                    for chunk in stream:
                        content += chunk
                    if content.strip():
                        break
                except Exception as e:
                    logging.warning(f"Memory consolidation LLM call attempt {attempt+1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        logging.error("All LLM call attempts failed for memory consolidation")
                        return []
                    time.sleep(1 * (2 ** attempt))
                
            # 3. Parse and Save
            import json
            content = content.strip()
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            
            consolidated = []
            if json_match:
                facts = json.loads(json_match.group(0))
                if isinstance(facts, list):
                    for fact in facts:
                        if isinstance(fact, str):
                            self.add_knowledge(fact, {"type": "fact", "source": "consolidation"})
                            consolidated.append(fact)
                            
            return consolidated
            
        except Exception as e:
            logging.error(f"Memory consolidation failed: {e}")
            return []

    def add_memory(self, text: str, metadata: Dict[str, Any], collection_name: str = "conversations"):
        """Add a new memory entry."""
        if not self.client:
            return False
            
        try:
            collection = self.conversations if collection_name == "conversations" else self.knowledge
            
            # 自动设置重要度和过期时间
            memory_type = metadata.get('type', 'general')
            if 'importance' not in metadata:
                if collection_name == 'knowledge' or memory_type == 'fact':
                    metadata['importance'] = 4  # 知识类记忆重要度高
                elif memory_type == 'chat':
                    metadata['importance'] = 2  # 普通对话重要度中等
                else:
                    metadata['importance'] = 3
            
            if 'expire_time' not in metadata:
                if metadata['importance'] >=4:
                    # 高重要度记忆有效期1年
                    expire_at = datetime.datetime.now() + datetime.timedelta(days=365)
                elif metadata['importance'] >=2:
                    # 中等重要度记忆有效期30天
                    expire_at = datetime.datetime.now() + datetime.timedelta(days=30)
                else:
                    # 低重要度记忆有效期7天
                    expire_at = datetime.datetime.now() + datetime.timedelta(days=7)
                metadata['expire_time'] = expire_at.isoformat()
            
            # Generate a unique ID (simple counter for now, UUID better for prod)
            count = collection.count()
            memory_id = f"{collection_name}_{count + 1}"
            
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[memory_id]
            )
            # 记录记忆能力使用成功
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("memory", True)
            return True
        except Exception as e:
            logging.error(f"Failed to add memory: {e}")
            # 记录记忆能力使用失败
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("memory", False)
            return False

    def add_knowledge(self, text: str, metadata: Dict[str, Any]):
        """
        Add a knowledge entry (rule, strategy, fact).
        REWARD: Gaining knowledge gives energy (Food).
        """
        success = self.add_memory(text, metadata, collection_name="knowledge")
        
        if success and self.needs:
            # Reward amount depends on source
            amount = 5.0
            source = metadata.get("source", "unknown")
            
            if source == "consolidation": amount = 10.0 # High value deep thoughts
            elif source == "starvation": amount = 30.0  # Crucial survival info
            elif source == "reflection": amount = 15.0  # Self-improvement
            
            self.needs.feed(amount)
            logging.info(f"Knowledge Acquired! Gained {amount} Energy.")
            
        return success

    def retrieve(self, query: str, n_results: int = 3, collection_name: str = "conversations", similarity_threshold: float = 0.6) -> List[str]:
        """Retrieve relevant memories based on semantic similarity."""
        if not self.client:
            return []
            
        try:
            collection = self.conversations if collection_name == "conversations" else self.knowledge
            
            # Query the collection, include distances and metadatas
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'distances', 'metadatas']
            )
            
            # Process results: filter by similarity threshold, sort by combined score of similarity and importance
            memory_candidates = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    # 余弦距离直接转换为相似度，距离越小相似度越高
                    similarity = 1 - distance
                    if similarity >= similarity_threshold:
                        # 提前缓存重要度归一化值，避免重复除法计算
                        importance = metadata.get('importance', 0)
                        normalized_importance = importance * 0.2  # 等价于importance/5，性能更优
                        # 综合分数 = 相似度权重70% + 重要度权重30%
                        combined_score = similarity * 0.7 + normalized_importance * 0.3
                        memory_candidates.append((-combined_score, doc))  # 负号用于升序排序得到综合分数降序
            
            # 按综合分数排序
            memory_candidates.sort()
            memories = [doc for (_, doc) in memory_candidates]
            
            # 记录记忆检索成功
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("memory", True)
            return memories
        except Exception as e:
            logging.error(f"Failed to retrieve memory: {e}")
            # 记录记忆检索失败
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("memory", False)
            return []

    def save_context(self, user_input: str, ai_output: str):
        """Helper to save a conversation turn."""
        text = f"User: {user_input}\nAI: {ai_output}"
        # metadata values must be str, int, float, or bool
        self.add_memory(text, {"type": "chat", "source": "user_interaction"})

# Global instance
memory = MemorySystem()
