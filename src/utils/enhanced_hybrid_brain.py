"""
Enhanced Hybrid Brain - 增强版Brain+LLM混合模式

核心改进：让Brain承担更多功能，大幅减少LLM调用

能力分层：
- L1: 本地模板匹配（<1ms）
- L2: 规则合成（<5ms）
- L3: 语义检索（<10ms）
- L4: 本地推理（<50ms）
- L5: LLM生成（>500ms，仅在必要时）

使用方式:
    export LLM_PROVIDER=enhanced_hybrid
    
或者:
    from src.utils.enhanced_hybrid_brain import EnhancedHybridBrain
    client = EnhancedHybridBrain()
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 导入基础组件
try:
    from src.utils.hybrid_brain_client import HybridBrainClient, HybridResponse
    from src.brain.local_response_system import (
        IntentRouter, TemplateResponseEngine, 
        SemanticResponseRetriever, LocalInferenceEngine
    )
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    logging.warning(f"组件导入失败: {e}")


class ProcessingLevel(Enum):
    """处理级别"""
    TEMPLATE = "template"           # L1: 模板匹配
    SEMANTIC = "semantic"           # L3: 语义检索
    INFERENCE = "inference"         # L4: 本地推理
    LLM = "llm"                     # L5: LLM生成


@dataclass
class ProcessingDecision:
    """处理决策"""
    level: ProcessingLevel
    reason: str
    confidence: float
    estimated_cost: float  # 预估成本（相对值）
    estimated_time: float  # 预估时间（毫秒）


@dataclass
class UsageStats:
    """使用统计"""
    total_requests: int = 0
    template_hits: int = 0
    semantic_hits: int = 0
    inference_hits: int = 0
    llm_calls: int = 0
    
    total_latency: float = 0.0
    llm_latency: float = 0.0
    
    cost_savings: float = 0.0  # 节省的成本估算
    
    def get_local_ratio(self) -> float:
        """获取本地处理比例"""
        if self.total_requests == 0:
            return 0.0
        local = self.template_hits + self.semantic_hits + self.inference_hits
        return local / self.total_requests
    
    def get_avg_latency(self) -> float:
        """获取平均延迟"""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests


class LLMCallDecider:
    """
    LLM调用决策器
    
    智能决定是否调用LLM，以及何时使用本地处理
    """
    
    def __init__(self):
        # 阈值配置
        self.confidence_threshold = 0.75  # 本地处理置信度阈值
        self.complexity_threshold = 0.6   # 复杂度阈值
        
        # 决策历史
        self.decision_history: List[Dict] = []
        self.feedback_loop: Dict[str, float] = {}  # 意图 -> 成功率
    
    def decide(
        self,
        intent: str,
        intent_confidence: float,
        message: str,
        context: List[Dict] = None,
        user_profile: Dict = None
    ) -> ProcessingDecision:
        """
        做出处理决策
        
        Returns:
            ProcessingDecision对象
        """
        context = context or []
        
        # 1. 计算消息复杂度
        complexity = self._calculate_complexity(message)
        
        # 2. 检查历史成功率
        historical_success = self.feedback_loop.get(intent, 0.5)
        
        # 3. 决策逻辑
        
        # L1: 高置信度简单意图 -> 模板
        if intent_confidence > 0.8 and complexity < 0.3:
            if intent in ["greeting", "farewell", "gratitude", "confirmation"]:
                return ProcessingDecision(
                    level=ProcessingLevel.TEMPLATE,
                    reason=f"高置信度({intent_confidence:.2f})简单意图，使用模板",
                    confidence=intent_confidence,
                    estimated_cost=0.01,
                    estimated_time=1.0
                )
        
        # L2: 上下文追问 -> 本地推理
        if self._is_follow_up(message, context):
            return ProcessingDecision(
                level=ProcessingLevel.INFERENCE,
                reason="检测到上下文追问，使用本地推理",
                confidence=0.7,
                estimated_cost=0.05,
                estimated_time=20.0
            )
        
        # L3: 知识查询且历史成功率高 -> 本地推理
        if intent == "knowledge" and historical_success > 0.7 and complexity < 0.5:
            return ProcessingDecision(
                level=ProcessingLevel.INFERENCE,
                reason="知识查询且本地历史成功率高",
                confidence=historical_success,
                estimated_cost=0.05,
                estimated_time=30.0
            )
        
        # L4: 低复杂度且模板可用 -> 尝试模板
        if complexity < 0.4 and intent_confidence > 0.6:
            return ProcessingDecision(
                level=ProcessingLevel.TEMPLATE,
                reason="低复杂度，优先尝试模板",
                confidence=intent_confidence * 0.8,
                estimated_cost=0.01,
                estimated_time=2.0
            )
        
        # L5: 语义检索尝试
        if complexity < 0.5:
            return ProcessingDecision(
                level=ProcessingLevel.SEMANTIC,
                reason="中等复杂度，尝试语义检索",
                confidence=0.6,
                estimated_cost=0.02,
                estimated_time=10.0
            )
        
        # L6: 默认使用LLM
        return ProcessingDecision(
            level=ProcessingLevel.LLM,
            reason=f"复杂度较高({complexity:.2f})或不确定，使用LLM",
            confidence=0.95,
            estimated_cost=1.0,
            estimated_time=800.0
        )
    
    def _calculate_complexity(self, message: str) -> float:
        """计算消息复杂度 0-1"""
        complexity = 0.0
        
        # 长度
        if len(message) > 200:
            complexity += 0.3
        elif len(message) > 100:
            complexity += 0.15
        
        # 多问题
        question_count = message.count("?") + message.count("？")
        complexity += min(0.2, question_count * 0.1)
        
        # 复杂词汇
        complex_indicators = ["解释", "分析", "比较", "区别", "实现", "设计", "为什么"]
        for indicator in complex_indicators:
            if indicator in message:
                complexity += 0.1
                break
        
        # 代码相关
        code_indicators = ["```", "代码", "编程", "函数", "class", "def "]
        if any(ind in message for ind in code_indicators):
            complexity += 0.3
        
        return min(1.0, complexity)
    
    def _is_follow_up(self, message: str, context: List[Dict]) -> bool:
        """检查是否是追问"""
        if not context or len(context) < 2:
            return False
        
        follow_up_keywords = ["为什么", "然后呢", "接着", "还有", "什么意思", "怎么说"]
        return any(kw in message for kw in follow_up_keywords)
    
    def feedback(self, intent: str, level: ProcessingLevel, success: bool):
        """接收反馈，优化决策"""
        # 更新成功率
        current = self.feedback_loop.get(intent, 0.5)
        alpha = 0.1  # 学习率
        self.feedback_loop[intent] = current + alpha * (1.0 if success else 0.0 - current)
        
        # 记录历史
        self.decision_history.append({
            "intent": intent,
            "level": level.value,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史大小
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]


class EnhancedHybridBrain:
    """
    增强版Brain+LLM混合客户端
    
    大幅减少LLM调用，让Brain承担更多
    """
    
    def __init__(
        self,
        start_as_infant: bool = False,
        llm_provider: Optional[str] = None,
        local_first: bool = True,  # 优先本地处理
        **kwargs
    ):
        if not COMPONENTS_AVAILABLE:
            raise ImportError("必要组件不可用")
        
        self.provider = "enhanced_hybrid"
        self.model_name = "enhanced-brain+llm"
        self.local_first = local_first
        
        # 初始化基础Brain（用于复杂任务）
        self.base_client = HybridBrainClient(
            start_as_infant=start_as_infant,
            llm_provider=llm_provider,
            **kwargs
        )
        
        # 初始化本地处理组件
        self.intent_router = IntentRouter()
        self.template_engine = TemplateResponseEngine(brain_reference=self.base_client.brain)
        self.semantic_retriever = SemanticResponseRetriever(
            memory_system=getattr(self.base_client.brain, 'memory', None)
        )
        self.inference_engine = LocalInferenceEngine()
        self.llm_decider = LLMCallDecider()
        
        # 统计
        self.stats = UsageStats()
        self.session_start = datetime.now()
        
        logging.info(f"🧠⚡ Enhanced Hybrid Brain已初始化 | 本地优先: {local_first}")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7
    ) -> HybridResponse:
        """
        智能生成响应
        
        根据情况选择本地处理或LLM
        """
        start_time = time.time()
        self.stats.total_requests += 1
        
        try:
            # 1. 提取用户输入
            user_message = self._extract_last_user_message(messages)
            
            # 2. 意图识别
            intent, intent_confidence, _ = self.intent_router.classify_intent(user_message)
            
            # 3. 决策
            decision = self.llm_decider.decide(
                intent=intent,
                intent_confidence=intent_confidence,
                message=user_message,
                context=messages[:-1] if len(messages) > 1 else []
            )
            
            # 4. 根据决策执行
            response_content = None
            processing_level = decision.level
            
            if processing_level == ProcessingLevel.TEMPLATE:
                # L1: 模板生成
                response_content = self._generate_template(
                    intent, user_message
                )
                if response_content:
                    self.stats.template_hits += 1
                    self.llm_decider.feedback(intent, processing_level, True)
                else:
                    # 模板失败，降级到LLM
                    processing_level = ProcessingLevel.LLM
            
            if processing_level == ProcessingLevel.SEMANTIC:
                # L3: 语义检索
                response_content = self._generate_semantic(user_message)
                if response_content:
                    self.stats.semantic_hits += 1
                    self.llm_decider.feedback(intent, processing_level, True)
                else:
                    processing_level = ProcessingLevel.LLM
            
            if processing_level == ProcessingLevel.INFERENCE:
                # L4: 本地推理
                response_content = self._generate_inference(
                    user_message, messages[:-1]
                )
                if response_content:
                    self.stats.inference_hits += 1
                    self.llm_decider.feedback(intent, processing_level, True)
                else:
                    processing_level = ProcessingLevel.LLM
            
            if processing_level == ProcessingLevel.LLM or response_content is None:
                # L5: LLM生成
                llm_start = time.time()
                response_content = self._generate_llm(messages, temperature)
                self.stats.llm_calls += 1
                self.stats.llm_latency += (time.time() - llm_start) * 1000
                
                # 缓存响应
                self.semantic_retriever.cache_response(
                    user_message, response_content,
                    {"intent": intent, "level": "llm"}
                )
            
            # 5. 计算统计
            latency = (time.time() - start_time) * 1000
            self.stats.total_latency += latency
            
            # 估算节省成本
            if processing_level != ProcessingLevel.LLM:
                self.stats.cost_savings += 0.002  # 估算每次LLM调用成本
            
            # 6. 构建响应
            return HybridResponse(
                content=response_content,
                reasoning_content=self._build_reasoning(processing_level, decision),
                brain_state={
                    "processing_level": processing_level.value,
                    "intent": intent,
                    "decision_confidence": decision.confidence,
                    "latency_ms": round(latency, 2)
                }
            )
            
        except Exception as e:
            logging.error(f"Enhanced Hybrid处理失败: {e}")
            # 降级到基础客户端
            return self.base_client.generate(messages, stream, temperature)
    
    def _extract_last_user_message(self, messages: List[Dict]) -> str:
        """提取最后一条用户消息"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    def _generate_template(self, intent: str, message: str) -> Optional[str]:
        """使用模板生成"""
        emotional_state = getattr(self.base_client.brain, 'current_emotion', None)
        return self.template_engine.generate_response(intent, message, emotional_state)
    
    def _generate_semantic(self, message: str) -> Optional[str]:
        """使用语义检索生成"""
        return self.semantic_retriever.find_similar_response(message, threshold=0.88)
    
    def _generate_inference(self, message: str, context: List[Dict]) -> Optional[str]:
        """使用本地推理生成"""
        # 尝试问答
        answer = self.inference_engine.answer_question(message)
        if answer:
            return answer
        
        # 尝试上下文推理
        return self.inference_engine.infer_from_context(message, context)
    
    def _generate_llm(self, messages: List[Dict], temperature: float) -> str:
        """使用LLM生成"""
        response = self.base_client.generate(messages, stream=False, temperature=temperature)
        return response.content
    
    def _build_reasoning(
        self, 
        level: ProcessingLevel, 
        decision: ProcessingDecision
    ) -> str:
        """构建推理说明"""
        parts = [
            f"处理级别: {level.value.upper()}",
            f"决策原因: {decision.reason}",
            f"决策置信度: {decision.confidence:.2f}",
            f"预估成本: {decision.estimated_cost:.2f}x",
            f"预估时间: {decision.estimated_time:.0f}ms",
            "",
            f"--- 统计 ---",
            f"本地处理率: {self.stats.get_local_ratio():.1%}",
            f"平均延迟: {self.stats.get_avg_latency():.0f}ms",
            f"累计节省: ${self.stats.cost_savings:.4f}",
        ]
        return "\n".join(parts)
    
    def get_stats(self) -> Dict:
        """获取详细统计"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "session_duration_seconds": session_duration,
            "total_requests": self.stats.total_requests,
            "processing_breakdown": {
                "template": self.stats.template_hits,
                "semantic": self.stats.semantic_hits,
                "inference": self.stats.inference_hits,
                "llm": self.stats.llm_calls
            },
            "local_processing_ratio": self.stats.get_local_ratio(),
            "average_latency_ms": self.stats.get_avg_latency(),
            "llm_average_latency_ms": (
                self.stats.llm_latency / self.stats.llm_calls 
                if self.stats.llm_calls > 0 else 0
            ),
            "estimated_cost_savings": self.stats.cost_savings,
            "intent_stats": self.intent_router.get_stats(),
            "current_emotion": self.base_client.brain.report_subjective_experience(),
            "developmental_stage": self.base_client.developmental_stage
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print("\n" + "="*50)
        print("📊 Enhanced Hybrid Brain 运行统计")
        print("="*50)
        print(f"总会话数: {stats['total_requests']}")
        print(f"\n处理分布:")
        print(f"  📝 模板匹配: {stats['processing_breakdown']['template']}")
        print(f"  🔍 语义检索: {stats['processing_breakdown']['semantic']}")
        print(f"  🧠 本地推理: {stats['processing_breakdown']['inference']}")
        print(f"  🤖 LLM调用:  {stats['processing_breakdown']['llm']}")
        print(f"\n本地处理率: {stats['local_processing_ratio']:.1%}")
        print(f"平均响应延迟: {stats['average_latency_ms']:.0f}ms")
        print(f"预估节省成本: ${stats['estimated_cost_savings']:.4f}")
        print("="*50)
    
    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ):
        """流式生成"""
        # 流式输出只能使用LLM
        response = self.generate(messages, stream=False, temperature=temperature)
        
        # 模拟流式
        words = response.content.split()
        for word in words:
            yield word + " "
    
    def reset(self, start_as_infant: bool = False):
        """重置状态"""
        self.base_client.reset(start_as_infant=start_as_infant)
        self.stats = UsageStats()
        self.session_start = datetime.now()


# 兼容性包装
class EnhancedHybridClient(EnhancedHybridBrain):
    """兼容旧接口的包装类"""
    pass
