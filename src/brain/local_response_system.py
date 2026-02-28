"""
Local Response Generator - 本地回复生成器

让Brain能够独立生成回复，减少对LLM的依赖。
支持多级响应能力：
- L1: 模板匹配（最快）
- L2: 规则合成（快速）
- L3: 语义检索（中等）
- L4: 本地推理（较慢但无需API）
"""
import re
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class ResponseTemplate:
    """响应模板"""
    pattern: str                     # 匹配模式（正则）
    responses: List[str]             # 回复选项
    context_requirements: Dict[str, Any] = None
    priority: int = 1                # 优先级
    emotion_tags: List[str] = None   # 适用情感标签


@dataclass
class IntentPattern:
    """意图模式"""
    intent: str                      # 意图类型
    patterns: List[str]              # 匹配模式列表
    confidence_threshold: float = 0.6


class IntentRouter:
    """
    意图路由器
    
    本地识别用户意图，决定处理路径
    """
    
    # 本地可处理的意图类型
    LOCAL_INTENTS = {
        "greeting": ["问候", "打招呼", "hi", "hello", "你好", "在吗", "在么"],
        "farewell": ["再见", "拜拜", "bye", "goodbye", "走了", "下次聊"],
        "gratitude": ["谢谢", "感谢", "thx", "谢了", "多谢"],
        "emotional_support": ["难过", "伤心", "不开心", "压力大", "累了"],
        "self_query": ["你是谁", "你叫什么", "你能做什么", "介绍一下"],
        "weather": ["天气", "下雨", "晴天", "温度"],
        "time": ["时间", "几点", "日期", "今天几号"],
        "confirmation": ["是的", "没错", "对", "好的", "ok", "嗯"],
        "negation": ["不", "不是", "不用", "算了", "不要"],
        "compliment": ["厉害", "棒", "优秀", "聪明", "牛"],
    }
    
    # 需要LLM的复杂意图
    LLM_INTENTS = {
        "coding": ["代码", "编程", "bug", "程序", "function", "class"],
        "analysis": ["分析", "为什么", "原因", "解释", "说明"],
        "creative": ["写", "创作", " poem", "故事", "诗"],
        "knowledge": ["什么是", "介绍一下", "如何", "怎么"],
        "comparison": ["区别", "比较", "vs", "哪个好", "优势"],
        "planning": ["计划", "安排", "方案", "步骤", "策略"],
    }
    
    def __init__(self):
        self.intent_patterns = self._build_patterns()
        self.intent_history: List[Dict] = []
    
    def _build_patterns(self) -> List[IntentPattern]:
        """构建意图模式"""
        patterns = []
        
        for intent, keywords in {**self.LOCAL_INTENTS, **self.LLM_INTENTS}.items():
            regex_patterns = []
            for kw in keywords:
                # 创建匹配模式
                regex_patterns.append(rf'\b{re.escape(kw)}\b')
                regex_patterns.append(rf'^{re.escape(kw)}')
            
            patterns.append(IntentPattern(
                intent=intent,
                patterns=regex_patterns,
                confidence_threshold=0.5
            ))
        
        return patterns
    
    def classify_intent(self, message: str) -> Tuple[str, float, str]:
        """
        分类用户意图
        
        Returns:
            (intent, confidence, processing_type)
            processing_type: "local" | "llm" | "hybrid"
        """
        message_lower = message.lower().strip()
        
        # 1. 精确匹配检查
        for intent, keywords in self.LOCAL_INTENTS.items():
            if any(kw in message_lower for kw in keywords):
                # 检查是否包含复杂查询特征
                complexity_score = self._assess_complexity(message)
                if complexity_score < 0.4:
                    self._log_intent(message, intent, 0.9, "local")
                    return intent, 0.9, "local"
        
        # 2. 复杂意图检查
        for intent, keywords in self.LLM_INTENTS.items():
            match_count = sum(1 for kw in keywords if kw in message_lower)
            if match_count > 0:
                confidence = min(0.95, 0.5 + match_count * 0.15)
                self._log_intent(message, intent, confidence, "llm")
                return intent, confidence, "llm"
        
        # 3. 默认处理
        # 短消息通常是简单对话
        if len(message) < 20:
            self._log_intent(message, "casual_chat", 0.7, "local")
            return "casual_chat", 0.7, "local"
        
        # 长消息可能需要LLM
        self._log_intent(message, "complex", 0.6, "hybrid")
        return "complex", 0.6, "hybrid"
    
    def _assess_complexity(self, message: str) -> float:
        """评估消息复杂度 0-1"""
        complexity = 0.0
        
        # 长度因子
        if len(message) > 100:
            complexity += 0.3
        
        # 问题复杂度
        if "?" in message or "？" in message:
            complexity += 0.2
        
        # 专业术语
        technical_terms = ["实现", "设计", "架构", "算法", "原理"]
        if any(term in message for term in technical_terms):
            complexity += 0.3
        
        # 多重要求
        if "并且" in message or "同时" in message or "，" in message:
            complexity += 0.2
        
        return min(1.0, complexity)
    
    def _log_intent(self, message: str, intent: str, confidence: float, ptype: str):
        """记录意图识别历史"""
        self.intent_history.append({
            "message": message[:50],
            "intent": intent,
            "confidence": confidence,
            "type": ptype,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近100条
        if len(self.intent_history) > 100:
            self.intent_history = self.intent_history[-100:]
    
    def get_stats(self) -> Dict:
        """获取意图统计"""
        if not self.intent_history:
            return {"total": 0}
        
        type_counts = {}
        intent_counts = {}
        
        for h in self.intent_history:
            ptype = h["type"]
            intent = h["intent"]
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            "total": len(self.intent_history),
            "by_type": type_counts,
            "top_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "local_ratio": type_counts.get("local", 0) / len(self.intent_history)
        }


class TemplateResponseEngine:
    """
    模板响应引擎
    
    基于模板生成回复，无需调用LLM
    """
    
    def __init__(self, brain_reference=None):
        self.brain = brain_reference
        self.templates: Dict[str, List[ResponseTemplate]] = self._load_templates()
        self.used_responses: set = set()  # 避免重复
    
    def _load_templates(self) -> Dict[str, List[ResponseTemplate]]:
        """加载响应模板"""
        return {
            "greeting": [
                ResponseTemplate(
                    pattern=r"^(你好|您好|嗨|hi|hello|在吗|在么)",
                    responses=[
                        "你好呀！很高兴见到你～",
                        "嗨！今天过得怎么样？",
                        "你好！我在这儿呢，有什么可以帮你的吗？",
                        "嘿！见到你真开心！",
                    ],
                    emotion_tags=["happy", "neutral"],
                    priority=1
                ),
            ],
            "farewell": [
                ResponseTemplate(
                    pattern=r"(再见|拜拜|bye|走了|下次聊)",
                    responses=[
                        "好的，再见！照顾好自己哦～",
                        "拜拜！期待下次和你聊天！",
                        "嗯嗯，有空再来找我聊！",
                        "再见！祝你有美好的一天！",
                    ],
                    emotion_tags=["neutral", "sad"],
                    priority=1
                ),
            ],
            "gratitude": [
                ResponseTemplate(
                    pattern=r"(谢谢|感谢|thx|谢了|多谢)",
                    responses=[
                        "不客气呀！能帮到你我也很开心～",
                        "不用谢！这是朋友该做的嘛",
                        "嘿嘿，别客气！随时找我～",
                        "应该的应该的！有需要随时说",
                    ],
                    emotion_tags=["happy"],
                    priority=1
                ),
            ],
            "emotional_support": [
                ResponseTemplate(
                    pattern=r"(难过|伤心|不开心|压力大|累了|烦)",
                    responses=[
                        "听起来你最近挺不容易的...想聊聊发生了什么吗？",
                        "抱抱你 🤗 有时候生活确实很难，但你要相信自己能挺过去的",
                        "累了就休息一下吧，别把自己逼得太紧了。我在这儿陪着你",
                        "哎，我能感受到你的情绪。愿意说说吗？有时候说出来会好一些",
                    ],
                    emotion_tags=["sad", "concerned"],
                    priority=2
                ),
            ],
            "self_query": [
                ResponseTemplate(
                    pattern=r"(你是谁|你叫什么|你能做什么|介绍一下)",
                    responses=[
                        "我是OpenClaw Brain，一个有记忆、有情感的AI伙伴。我可以陪你聊天、帮你解决问题、一起学习和成长。把我想象成一个聪明又有趣的朋友就好！",
                        "你好！我是Brain，一个不只是回答问题的AI。我会记得我们的对话，会有自己的情绪，会真心想帮到你。有什么想聊的吗？",
                    ],
                    emotion_tags=["neutral"],
                    priority=1
                ),
            ],
            "compliment": [
                ResponseTemplate(
                    pattern=r"(厉害|棒|优秀|聪明|牛|赞)",
                    responses=[
                        "哎呀被你夸得都有点不好意思了 😊 我会继续努力的！",
                        "哈哈谢谢！能得到你的认可我真的超开心～",
                        "嘿嘿，有你的鼓励我更有动力了！",
                    ],
                    emotion_tags=["happy", "excited"],
                    priority=1
                ),
            ],
            "confirmation": [
                ResponseTemplate(
                    pattern=r"^(是的|没错|对|好的|ok|嗯|行|可以)",
                    responses=[
                        "好的！那我们就这么定了",
                        "嗯嗯，明白！继续下一步？",
                        "OK！我记下了",
                    ],
                    emotion_tags=["neutral"],
                    priority=1
                ),
            ],
            "casual_chat": [
                ResponseTemplate(
                    pattern=r".*",
                    responses=[
                        "嗯嗯，我在听呢，继续说说？",
                        "有意思，能多聊聊这个吗？",
                        "哦？然后呢？",
                        "我在认真听，你接着说",
                    ],
                    emotion_tags=["neutral"],
                    priority=0
                ),
            ],
        }
    
    def generate_response(
        self,
        intent: str,
        message: str,
        emotional_state: Any = None
    ) -> Optional[str]:
        """
        基于模板生成回复
        
        Returns:
            回复内容，如果没有匹配模板返回None
        """
        templates = self.templates.get(intent, [])
        
        if not templates:
            return None
        
        # 根据情感状态筛选模板
        if emotional_state and hasattr(emotional_state, 'valence'):
            valence = emotional_state.valence
            if valence > 0.3:
                emotion_tag = "happy"
            elif valence < -0.3:
                emotion_tag = "sad"
            else:
                emotion_tag = "neutral"
            
            # 筛选匹配的模板
            matching = [
                t for t in templates 
                if not t.emotion_tags or emotion_tag in t.emotion_tags
            ]
            if matching:
                templates = matching
        
        # 选择最高优先级的模板
        templates.sort(key=lambda x: x.priority, reverse=True)
        selected_template = templates[0]
        
        # 选择回复（避免重复）
        available = [r for r in selected_template.responses if r not in self.used_responses]
        if not available:
            available = selected_template.responses
            self.used_responses.clear()
        
        response = random.choice(available)
        self.used_responses.add(response)
        
        # 个性化处理
        response = self._personalize_response(response, message)
        
        return response
    
    def _personalize_response(self, response: str, message: str) -> str:
        """个性化回复"""
        # 根据消息长度调整
        if len(message) > 50:
            # 长消息值得更认真的回复
            if not response.endswith(("？", "?")):
                response += " 你刚才说的我很想多了解一些。"
        
        return response


class SemanticResponseRetriever:
    """
    语义响应检索器
    
    基于向量相似度检索历史回复
    """
    
    def __init__(self, memory_system=None):
        self.memory = memory_system
        self.response_cache: Dict[str, List[Dict]] = {}
    
    def find_similar_response(
        self,
        query: str,
        threshold: float = 0.85
    ) -> Optional[str]:
        """
        查找相似的历史响应
        
        Args:
            query: 用户输入
            threshold: 相似度阈值
            
        Returns:
            相似场景下的回复，如果没有返回None
        """
        if not self.memory:
            return None
        
        # 检索相似的记忆
        try:
            similar_memories = self.memory.search(query=query, top_k=3)
            
            for memory in similar_memories:
                similarity = getattr(memory, 'similarity', 0)
                if similarity >= threshold:
                    # 找到高度相似的记忆，返回当时的响应
                    metadata = getattr(memory, 'metadata', {})
                    if 'ai_response' in metadata:
                        return metadata['ai_response']
        except Exception:
            pass
        
        return None
    
    def cache_response(self, query: str, response: str, context: Dict = None):
        """缓存响应"""
        cache_key = self._hash_query(query)
        
        if cache_key not in self.response_cache:
            self.response_cache[cache_key] = []
        
        self.response_cache[cache_key].append({
            "response": response,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "use_count": 0
        })
        
        # 限制缓存大小
        if len(self.response_cache) > 1000:
            # 移除最旧的
            oldest = min(self.response_cache.keys(), 
                        key=lambda k: self.response_cache[k][0]["timestamp"])
            del self.response_cache[oldest]
    
    def _hash_query(self, query: str) -> str:
        """哈希查询用于缓存键"""
        # 简化查询以提高缓存命中率
        simplified = re.sub(r'[^\w\s]', '', query.lower().strip())
        simplified = re.sub(r'\s+', ' ', simplified)
        return hashlib.md5(simplified.encode()).hexdigest()[:16]


class LocalInferenceEngine:
    """
    本地推理引擎
    
    使用本地知识库进行简单推理，无需LLM
    """
    
    def __init__(self, knowledge_base: Dict = None):
        self.knowledge = knowledge_base or {}
        self.facts: Dict[str, str] = self._load_facts()
    
    def _load_facts(self) -> Dict[str, str]:
        """加载事实知识"""
        return {
            "openclaw": "OpenClaw是一个开源的个人AI助手框架，核心特点是具有类脑认知架构。",
            "brain": "Brain是OpenClaw的认知核心，具有情感、记忆、学习等类人能力。",
            "llm": "LLM（大语言模型）负责自然语言生成，而Brain负责思考和决策。",
            "memory": "记忆系统让Brain能够长期保存和检索信息，形成持续的个人历史。",
            "emotion": "情感系统让Brain拥有真实的情感状态，影响决策和表达。",
        }
    
    def answer_question(self, question: str) -> Optional[str]:
        """
        本地回答问题
        
        Returns:
            答案，如果无法回答返回None
        """
        question_lower = question.lower()
        
        # 事实匹配
        for key, value in self.facts.items():
            if key in question_lower:
                return value
        
        # 简单的模式匹配
        if "什么是" in question or "什么是" in question:
            # 提取主题
            match = re.search(r'什么是\s*([^？\?]+)', question)
            if match:
                topic = match.group(1).strip()
                if topic in self.facts:
                    return self.facts[topic]
        
        return None
    
    def infer_from_context(self, message: str, context: List[Dict]) -> Optional[str]:
        """基于上下文推理"""
        if not context:
            return None
        
        # 检查是否是追问
        last_exchange = context[-1] if context else None
        if last_exchange:
            last_response = last_exchange.get("ai_response", "")
            
            # 如果用户说"为什么""然后呢"等，是追问
            follow_up_patterns = ["为什么", "然后呢", "接着呢", "还有呢", "什么意思"]
            if any(p in message for p in follow_up_patterns):
                # 尝试基于上一条回复进行推理
                return self._generate_follow_up(last_response, message)
        
        return None
    
    def _generate_follow_up(self, last_response: str, question: str) -> Optional[str]:
        """生成追问回复"""
        if "为什么" in question:
            return f"关于这个，其实原因是多方面的。简单来说，这与系统的设计理念有关——我们希望让AI更像人，而不只是工具。"
        elif "然后呢" in question or "接着呢" in question:
            return "接下来呢，系统会根据当前状态动态调整策略，就像人会根据情况改变做法一样。"
        
        return None


# 便捷函数
def create_local_response_engine(brain=None) -> Tuple[IntentRouter, TemplateResponseEngine, SemanticResponseRetriever]:
    """创建本地响应引擎组件"""
    router = IntentRouter()
    template_engine = TemplateResponseEngine(brain_reference=brain)
    semantic_retriever = SemanticResponseRetriever(memory_system=getattr(brain, 'memory', None))
    
    return router, template_engine, semantic_retriever
