"""
Hybrid Brain - Brain + LLM 混合模式

结合Brain的认知架构优势和LLM的语言生成能力：
- Brain负责：情感、记忆、决策
- LLM负责：自然、流畅、智能的语言表达

使用方式:
    export LLM_PROVIDER=hybrid
    
或者:
    from src.utils.llm import LLMClient
    llm = LLMClient(provider="hybrid")
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Generator
from dataclasses import dataclass

# Brain模块
try:
    from src.brain.human_level_brain import HumanLevelBrain
    from src.brain.human_cognition import EmotionalState
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

# LLM模块
try:
    from src.utils.llm import LLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


@dataclass
class HybridResponse:
    """混合模式响应格式"""
    content: str
    reasoning_content: Optional[str] = None
    brain_state: Optional[Dict] = None
    
    def __post_init__(self):
        self.choices = [type('obj', (object,), {
            'message': type('obj', (object,), {'content': self.content})()
        })()]


class HybridBrainClient:
    """
    Brain + LLM 混合客户端
    
    Brain思考，LLM表达
    """
    
    def __init__(
        self,
        start_as_infant: bool = False,
        llm_provider: Optional[str] = None,
        **kwargs
    ):
        """
        初始化混合大脑客户端
        
        Args:
            start_as_infant: Brain是否从婴儿阶段开始
            llm_provider: LLM提供商（默认从环境变量读取）
            **kwargs: 其他配置
        """
        if not BRAIN_AVAILABLE:
            raise ImportError("Brain模块不可用")
        if not LLM_AVAILABLE:
            raise ImportError("LLM模块不可用")
        
        self.provider = "hybrid"
        self.model_name = "brain+llm-hybrid"
        
        # 初始化Brain（决策者）
        self.brain = HumanLevelBrain(start_as_infant=start_as_infant)
        
        # 初始化LLM（表达者）- 使用非brain的provider
        llm_provider = llm_provider or self._detect_llm_provider()
        if llm_provider == "brain" or llm_provider == "hybrid":
            # 避免递归，默认使用coze
            llm_provider = "coze"
        
        self.llm = LLMClient(provider=llm_provider)
        self.llm_provider = llm_provider
        
        # 统计信息
        self.interaction_count = 0
        self.developmental_stage = self.brain.developmental.stage.name
        
        logging.info(f"🧠🤖 Hybrid Brain已初始化 | Brain发育阶段: {self.developmental_stage} | LLM: {llm_provider}")
    
    def _detect_llm_provider(self) -> str:
        """检测可用的LLM提供商"""
        import os
        
        # 优先级：COZE_API_KEY > OPENAI_API_KEY > DEEPSEEK_API_KEY
        if os.getenv("COZE_API_KEY"):
            return "coze"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        else:
            return "coze"  # 默认
    
    def _messages_to_stimulus(self, messages: List[Dict[str, str]]) -> Dict:
        """将消息转换为Brain的感官输入"""
        system_content = ""
        user_content = ""
        context_history = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_content = content
            elif role == "user":
                if not user_content:
                    user_content = content
                else:
                    context_history.append(f"User: {content}")
            elif role == "assistant":
                context_history.append(f"Assistant: {content}")
        
        return {
            "cognitive": user_content,
            "context": "\n".join(context_history[-3:]),
            "system_prompt": system_content,
            "energy": 0.8,
            "event": {
                "relevance_to_self": 0.7,
                "expected_outcome": 0.5,
                "complexity": len(user_content) / 100
            }
        }
    
    def _build_hybrid_prompt(
        self,
        user_input: str,
        brain_result: Dict,
        original_messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        构建混合模式的Prompt
        
        将Brain的状态信息注入到LLM的prompt中
        """
        # 提取Brain状态
        cognitive_response = brain_result.get("cognitive_response", {})
        action = getattr(cognitive_response, "action", "respond")
        reasoning = getattr(cognitive_response, "reasoning", "")
        confidence = getattr(cognitive_response, "confidence", 0.8)
        
        emotional_state = brain_result.get("emotional_state")
        developmental_stage = brain_result.get("developmental_stage", "UNKNOWN")
        dominant_drive = brain_result.get("dominant_drive")
        
        # 提取记忆
        memories = self.brain.recall_memories(query=user_input, top_k=3)
        memory_context = ""
        if memories:
            memory_context = "\n相关记忆:\n" + "\n".join([
                f"- {m.content[:100]}..." if len(m.content) > 100 else f"- {m.content}"
                for m in memories[:2]
            ])
        
        # 情感描述
        emotion_desc = ""
        if emotional_state:
            valence = emotional_state.valence
            arousal = emotional_state.arousal
            if valence > 0.3:
                emotion_desc = "感到积极、友好"
            elif valence < -0.3:
                emotion_desc = "感到谨慎、保守"
            else:
                emotion_desc = "保持中立、理性"
            
            if arousal > 0.6:
                emotion_desc += "，比较兴奋"
            elif arousal < 0.4:
                emotion_desc += "，比较平静"
        
        # 构建系统提示
        system_prompt = f"""你是OpenClaw Brain，一个具有人类级认知架构的AI助手。

## 你的内部状态
- 发育阶段: {developmental_stage}
- 当前情感: {emotion_desc}
- 决策置信度: {confidence:.0%}
- 主导驱力: {dominant_drive}

## 决策信息
- Brain决策: {action}
- 推理过程: {reasoning}
{memory_context}

## 表达指南
1. 以第一人称"我"来回应
2. 语气要自然、有温度，像人类对话
3. 适当体现情感状态（如果积极可以热情一些，如果谨慎可以更稳重）
4. 不要暴露你的技术实现细节（不要说"作为AI"，可以说"我觉得"）
5. 如果决策是"explore"，表现出好奇心；如果是"avoid"，委婉转移话题
"""

        # 构建混合prompt
        hybrid_messages = [
            {"role": "system", "content": system_prompt},
            *original_messages
        ]
        
        return hybrid_messages
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7
    ) -> HybridResponse:
        """
        生成响应（Brain思考 + LLM表达）
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
            temperature: 温度参数
            
        Returns:
            HybridResponse对象
        """
        try:
            # Step 1: Brain处理（思考）
            sensory_input = self._messages_to_stimulus(messages)
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            brain_result = loop.run_until_complete(
                self.brain.experience(sensory_input)
            )
            
            # Step 2: 提取用户输入
            user_input = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break
            
            # Step 3: 构建混合Prompt
            hybrid_messages = self._build_hybrid_prompt(
                user_input=user_input,
                brain_result=brain_result,
                original_messages=messages
            )
            
            # Step 4: LLM生成（表达）
            llm_response = self.llm.generate(
                messages=hybrid_messages,
                stream=False,
                temperature=temperature
            )
            
            # Step 5: 更新统计
            self.interaction_count += 1
            self.developmental_stage = brain_result.get("developmental_stage", self.developmental_stage)
            
            # 提取内容
            content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            
            # 构建reasoning_content
            reasoning_parts = []
            cognitive_response = brain_result.get("cognitive_response", {})
            if cognitive_response:
                reasoning_parts.append(f"Brain决策: {getattr(cognitive_response, 'action', 'unknown')}")
                reasoning_parts.append(f"置信度: {getattr(cognitive_response, 'confidence', 0):.2f}")
            
            emotional_state = brain_result.get("emotional_state")
            if emotional_state:
                reasoning_parts.append(f"情感状态: valence={emotional_state.valence:.2f}, arousal={emotional_state.arousal:.2f}")
            
            reasoning_parts.append(f"发育阶段: {self.developmental_stage}")
            reasoning_parts.append(f"LLM: {self.llm_provider}")
            
            return HybridResponse(
                content=content,
                reasoning_content="\n".join(reasoning_parts),
                brain_state={
                    "action": getattr(cognitive_response, "action", "unknown"),
                    "emotional_valence": emotional_state.valence if emotional_state else 0,
                    "developmental_stage": self.developmental_stage
                }
            )
            
        except Exception as e:
            logging.error(f"Hybrid Brain处理失败: {e}")
            # 降级到纯Brain模式
            return HybridResponse(
                content="抱歉，我当前状态不太好，请稍后再试。",
                reasoning_content=f"错误: {str(e)}"
            )
    
    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式生成（Brain先思考，LLM流式表达）
        
        注意：Brain的处理是一次性的，LLM的输出是流式的
        """
        # 先让Brain思考（这一步不能流式）
        response = self.generate(messages, stream=False, temperature=temperature)
        content = response.content
        
        # 模拟流式输出
        words = content.split()
        for word in words:
            yield word + " "
    
    def get_stats(self) -> Dict:
        """获取混合大脑运行统计"""
        return {
            "interaction_count": self.interaction_count,
            "developmental_stage": self.developmental_stage,
            "llm_provider": self.llm_provider,
            "current_emotion": self.brain.report_subjective_experience(),
            "self_concept": self.brain.get_self_concept()
        }
    
    def reset(self, start_as_infant: bool = False):
        """重置混合大脑状态"""
        self.brain = HumanLevelBrain(start_as_infant=start_as_infant)
        self.interaction_count = 0
        self.developmental_stage = self.brain.developmental.stage.name


# 为了兼容LLMClient的调用方式
def create_hybrid_client(**kwargs) -> HybridBrainClient:
    """工厂函数：创建混合大脑客户端"""
    return HybridBrainClient(**kwargs)
