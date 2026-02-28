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

from src.utils.llm import LLMClient
from src.utils.needs import Needs
from src.utils.emotions import EmotionType
from src.utils.constants import CHROMA_DB_DIR

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
                 llm_client: Optional[LLMClient] = None):
        self.db_path = db_path
        self.needs = needs_system
        self.llm_client = llm_client
        self.client = None
        
        self._init_chroma()
    
    def _init_chroma(self):
        """初始化ChromaDB - 使用SimpleEmbedding，无需下载模型"""
        if not CHROMADB_AVAILABLE:
            logging.warning("EnhancedMemory: ChromaDB not available, memory system disabled")
            self.client = None
            self.conversations = None
            self.knowledge = None
            self.experiences = None
            self.dreams = None
            return
        
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # 使用Simple Embedding，避免下载大模型
            ef = SimpleEmbeddingFunction()
            logging.info("EnhancedMemory: Using simple hash-based embedding (no model download)")
            
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
        Args:
            content: 记忆内容
            metadata: 元数据
        Returns:
            重要性分数（0-100）
        """
        importance = 50.0  # 基础重要性
        
        # 基于内容长度（适度长度的记忆更重要）
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
                   content: str,
                   memory_type: MemoryType = MemoryType.CONVERSATION,
                   modality: ModalityType = ModalityType.TEXT,
                   emotional_tag: Optional[EmotionalTag] = None,
                   context: Dict[str, Any] = None,
                   source: str = "unknown") -> bool:
        """
        添加增强记忆
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            modality: 模态类型
            emotional_tag: 情感标签
            context: 上下文信息
            source: 来源
        Returns:
            是否成功
        """
        if not self.client:
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
                "memory_type": memory_type.value,
                "modality": modality.value,
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
                }, ensure_ascii=False)
            
            # 计算重要性
            metadata["importance"] = self._calculate_importance(content, metadata)
            
            # 生成唯一ID
            count = collection.count()
            memory_id = f"{memory_type.value}_{count + 1}_{int(time.time())}"
            
            # 添加到集合
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            # 如果是知识且needs系统存在，给予奖励
            if memory_type == MemoryType.KNOWLEDGE and self.needs:
                self.needs.feed(5.0)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to add memory: {e}")
            return False
    
    def retrieve(self, 
                query: str,
                memory_type: MemoryType = None,
                n_results: int = 5,
                min_importance: float = 0.0,
                emotion_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        检索记忆（支持高级过滤）
        Args:
            query: 查询内容
            memory_type: 记忆类型（None表示所有类型）
            n_results: 返回结果数量
            min_importance: 最小重要性阈值
            emotion_filter: 情感过滤器
        Returns:
            记忆列表，每个记忆包含内容和元数据
        """
        if not self.client:
            return []
        
        results = []
        
        try:
            # 确定要查询的集合
            collections = []
            if memory_type:
                collection_map = {
                    MemoryType.CONVERSATION: self.conversations,
                    MemoryType.KNOWLEDGE: self.knowledge,
                    MemoryType.EXPERIENCE: self.experiences,
                    MemoryType.DREAM: self.dreams
                }
                collections.append(collection_map.get(memory_type))
            else:
                collections = [self.conversations, self.knowledge, 
                             self.experiences, self.dreams]
            
            # 查询每个集合
            for collection in collections:
                if not collection:
                    continue
                
                query_results = collection.query(
                    query_texts=[query],
                    n_results=n_results * 2  # 获取更多结果以便过滤
                )
                
                if query_results and query_results['documents']:
                    for i, doc in enumerate(query_results['documents'][0]):
                        meta = query_results['metadatas'][0][i]
                        doc_id = query_results['ids'][0][i]
                        
                        # 应用过滤器
                        if min_importance > 0:
                            if meta.get('importance', 0) < min_importance:
                                continue
                        
                        # 解析情感标签
                        emo_tag = meta.get('emotional_tag')
                        if isinstance(emo_tag, str):
                            try:
                                emo_tag = json.loads(emo_tag)
                                meta['emotional_tag'] = emo_tag
                            except:
                                emo_tag = {}
                        
                        # 解析上下文
                        context = meta.get('context')
                        if isinstance(context, str):
                            try:
                                meta['context'] = json.loads(context)
                            except:
                                pass

                        if emotion_filter:
                            if not emo_tag or emo_tag.get('emotion') != emotion_filter:
                                continue
                        
                        # 更新访问统计
                        meta['access_count'] = meta.get('access_count', 0) + 1
                        meta['last_access'] = time.time()
                        
                        # 构建结果
                        results.append({
                            'content': doc,
                            'metadata': meta,
                            'id': doc_id,
                            'collection': collection.name
                        })
                        
                        # 更新访问统计到数据库
                        collection.update(
                            ids=[doc_id],
                            metadatas=[meta]
                        )
                
                if len(results) >= n_results:
                    break
            
            # 按重要性排序
            results.sort(key=lambda x: x['metadata'].get('importance', 0), reverse=True)
            
            return results[:n_results]
            
        except Exception as e:
            logging.error(f"Failed to retrieve memory: {e}")
            return []
    
    def get_emotional_memories(self, 
                              emotion: str, 
                              n_results: int = 5) -> List[Dict]:
        """
        获取特定情感的记忆
        Args:
            emotion: 情感类型
            n_results: 返回数量
        Returns:
            情感记忆列表
        """
        if not self.client:
            return []
        
        results = []
        
        try:
            # 查询所有集合
            collections = [self.conversations, self.knowledge, 
                         self.experiences, self.dreams]
            
            for collection in collections:
                if not collection:
                    continue
                
                # 获取所有记录
                all_data = collection.get()
                
                if all_data and all_data['metadatas']:
                    for i, meta in enumerate(all_data['metadatas']):
                        emo_tag = meta.get('emotional_tag')
                        if isinstance(emo_tag, str):
                            try:
                                emo_tag = json.loads(emo_tag)
                                meta['emotional_tag'] = emo_tag
                            except:
                                emo_tag = {}
                        
                        context = meta.get('context')
                        if isinstance(context, str):
                            try:
                                meta['context'] = json.loads(context)
                            except:
                                pass

                        if emo_tag and emo_tag.get('emotion') == emotion:
                            results.append({
                                'content': all_data['documents'][i],
                                'metadata': meta,
                                'id': all_data['ids'][i],
                                'collection': collection.name
                            })
                
                if len(results) >= n_results:
                    break
            
            # 按情感强度排序
            results.sort(
                key=lambda x: x['metadata'].get('emotional_tag', {}).get('intensity', 0),
                reverse=True
            )
            
            return results[:n_results]
            
        except Exception as e:
            logging.error(f"Failed to get emotional memories: {e}")
            return []
    
    def consolidate_experiences(self, llm_client: LLMClient = None) -> List[str]:
        """
        巩固经验记忆（将原始对话转换为知识）
        Args:
            llm_client: LLM客户端
        Returns:
            生成的知识点列表
        """
        if not self.client:
            return []
        
        if self.needs:
            self.needs.consume_energy(10.0)  # 巩固记忆消耗能量
        
        llm_client = llm_client or self.llm_client
        if not llm_client:
            return []
        
        try:
            # 获取最近的经验记忆
            count = self.experiences.count()
            if count == 0:
                return []
            
            recent_experiences = self.experiences.peek(limit=10)
            
            if not recent_experiences or not recent_experiences['documents']:
                return []
            
            # 准备上下文
            contexts = []
            for i, doc in enumerate(recent_experiences['documents']):
                meta = recent_experiences['metadatas'][i]
                context_str = f"\n---\nExperience: {doc}\n"
                emo_tag = meta.get('emotional_tag')
                if isinstance(emo_tag, str):
                    try:
                        emo_tag = json.loads(emo_tag)
                        meta['emotional_tag'] = emo_tag
                    except:
                        emo_tag = {}

                if emo_tag:
                    context_str += f"Emotion: {emo_tag.get('emotion')} ({emo_tag.get('intensity'):.0f}%)\n"
                contexts.append(context_str)
            
            full_context = "".join(contexts)
            
            # 使用LLM提取知识
            prompt = f"""
你是一个知识提取专家。以下是我最近的经历：
{full_context}

请从这些经历中提取3-5个值得长期保存的知识点或洞见。
忽略琐碎的日常对话，重点关注：
- 成功的策略和方法
- 失败的原因和教训
- 环境规律和模式
- 个人能力认知

只返回JSON数组，每个元素是一个字符串。
"""
            
            messages = [{"role": "user", "content": prompt}]
            
            # 收集LLM响应，新增3次重试机制和指数退避
            content = ""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    generator = llm_client.stream_generate(messages)
                    if generator:
                        for chunk in generator:
                            if chunk:
                                content += chunk
                        if content.strip():
                            break  # 成功获取内容则退出重试
                except Exception as e:
                    logging.warning(f"LLM consolidation attempt {attempt+1} failed: {e}")
                    if attempt == max_retries -1:
                        logging.error(f"All {max_retries} LLM consolidation attempts failed")
                        return []
                    time.sleep(1 * (2 ** attempt))  # 指数退避等待
            
            # 解析JSON
            import json
            knowledge_points = []
            
            # 清理内容
            content = content.strip()
            # 尝试提取JSON部分，用正则提升匹配成功率
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    points = json.loads(json_str)
                    if isinstance(points, list):
                        for point in points:
                            if isinstance(point, str):
                                knowledge_points.append(point)
                                # 添加到知识库
                                try:
                                    self.add_memory(
                                        content=point,
                                        memory_type=MemoryType.KNOWLEDGE,
                                        modality=ModalityType.TEXT,
                                        context={"source": "consolidation"},
                                        source="experience_consolidation"
                                    )
                                except Exception as e:
                                    logging.error(f"Failed to add consolidated memory: {e}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse consolidation result: {e}. Content: {content[:100]}...")
            else:
                 logging.warning(f"No JSON list found in LLM response: {content[:100]}...")
            
            if knowledge_points and self.needs:
                # 获得知识给予奖励
                total_reward = len(knowledge_points) * 10.0
                self.needs.feed(total_reward)
                logging.info(f"Consolidated {len(knowledge_points)} knowledge points. Gained {total_reward} energy.")
            
            # 记录学习能力使用结果
            learning_success = len(knowledge_points) > 0
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("learning", learning_success)
            
            # 记录学习能力使用结果
            learning_success = len(knowledge_points) > 0
            # 上报学习能力使用情况
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("learning", learning_success)
            return knowledge_points
            
        except Exception as e:
            logging.error(f"Experience consolidation failed: {e}")
            # 记录学习能力使用失败
            if hasattr(self, 'awareness'):
                self.awareness.record_capability_usage("learning", False)
            return []
    
    def dream_generation(self, llm_client: LLMClient = None) -> str:
        """
        生成梦境（随机组合记忆产生新想法）
        Args:
            llm_client: LLM客户端
        Returns:
            梦境内容
        """
        if not self.client:
            return ""
        
        if self.needs:
            self.needs.consume_energy(15.0)  # 梦境生成消耗更多能量
        
        llm_client = llm_client or self.llm_client
        if not llm_client:
            return ""
        
        try:
            # 随机选择3-5个记忆片段
            all_collections = [self.conversations, self.knowledge, 
                             self.experiences, self.dreams]
            
            fragments = []
            for collection in all_collections:
                if not collection:
                    continue
                
                count = collection.count()
                if count > 0:
                    data = collection.get(limit=3, offset=random.randint(0, max(0, count-3)))
                    if data and data['documents']:
                        fragments.extend(data['documents'][:2])
                
                if len(fragments) >= 5:
                    break
            
            if len(fragments) < 2:
                return ""
            
            # 随机选择3个片段
            selected_fragments = random.sample(fragments, min(3, len(fragments)))
            
            # 使用LLM生成梦境
            prompt = f"""
你正在做梦。以下是你记忆中的碎片：
{chr(10).join([f"- {frag}" for frag in selected_fragments])}

请将这些记忆片段自由组合，产生一个富有想象力的梦境描述。
梦境可以是超现实的、隐喻的或象征性的。
用第一人称描述，让梦境感觉真实。
"""
            
            messages = [{"role": "user", "content": prompt}]
            
            dream_content = ""
            try:
                stream = llm_client.stream_generate(messages)
                for chunk in stream:
                    dream_content += chunk
            except Exception as e:
                logging.error(f"Dream generation failed: {e}")
                return ""
            
            # 保存梦境
            if dream_content:
                self.add_memory(
                    content=dream_content,
                    memory_type=MemoryType.DREAM,
                    modality=ModalityType.TEXT,
                    context={"fragments": len(selected_fragments)},
                    source="dream_generation"
                )
            
            return dream_content
            
        except Exception as e:
            logging.error(f"Dream generation failed: {e}")
            return ""
    
    def get_memory_statistics(self) -> Dict:
        """获取记忆系统统计信息"""
        if not self.client:
            return {"error": "Memory system not initialized"}
        
        stats = {
            "conversations": self.conversations.count(),
            "knowledge": self.knowledge.count(),
            "experiences": self.experiences.count(),
            "dreams": self.dreams.count(),
            "total": 0
        }
        stats["total"] = sum([
            stats["conversations"], stats["knowledge"],
            stats["experiences"], stats["dreams"]
        ])
        
        return stats


# 便捷函数
def create_emotional_tag(emotion: EmotionType, intensity: float, valence: float = 0.0) -> EmotionalTag:
    """创建情感标签"""
    return EmotionalTag(
        emotion=emotion.value,
        intensity=max(0.0, min(100.0, intensity)),
        valence=max(-1.0, min(1.0, valence))
    )


if __name__ == "__main__":
    # 测试增强记忆系统
    print("=== 增强记忆系统测试 ===\n")
    
    # 注意：需要先配置LLM客户端和Needs系统
    memory = EnhancedMemorySystem()
    
    # 添加测试记忆
    memory.add_memory(
        content="今天学习了Python的高级特性，感觉很有收获。",
        memory_type=MemoryType.EXPERIENCE,
        emotional_tag=create_emotional_tag(EmotionType.HAPPINESS, 70.0, 0.8),
        source="learning"
    )
    
    memory.add_memory(
        content="遇到一个困难的bug，调试了很久才解决。",
        memory_type=MemoryType.EXPERIENCE,
        emotional_tag=create_emotional_tag(EmotionType.ANGER, 40.0, -0.3),
        source="debugging"
    )
    
    # 检索记忆
    results = memory.retrieve("学习经验", n_results=2)
    print(f"检索到 {len(results)} 条记忆:")
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result['content'][:50]}...")
        print(f"   重要性: {result['metadata'].get('importance', 0):.1f}")
    
    # 统计信息
    print(f"\n记忆统计: {memory.get_memory_statistics()}")
