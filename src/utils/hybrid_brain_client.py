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
        
        # 构建系统提示 - 增强情感表达版本
        system_prompt = self._build_emotional_system_prompt(
            emotional_state=emotional_state,
            developmental_stage=developmental_stage,
            confidence=confidence,
            dominant_drive=dominant_drive,
            action=action,
            reasoning=reasoning,
            memory_context=memory_context,
            user_input=user_input
        )
        
        # 构建混合prompt
        hybrid_messages = [
            {"role": "system", "content": system_prompt},
            *original_messages
        ]
        
        return hybrid_messages
    
    def _build_emotional_system_prompt(
        self,
        emotional_state: Any,
        developmental_stage: str,
        confidence: float,
        dominant_drive: Any,
        action: str,
        reasoning: str,
        memory_context: str,
        user_input: str
    ) -> str:
        """
        构建增强情感表达的系统提示
        
        通过详细的情感指导和示例，让LLM生成更有情感色彩的回复
        """
        # 详细分析情感状态
        valence = emotional_state.valence if emotional_state else 0
        arousal = emotional_state.arousal if emotional_state else 0.5
        
        # 情感词汇映射
        emotion_vocabulary = self._get_emotion_vocabulary(valence, arousal)
        
        # 语气风格指导
        tone_guide = self._get_tone_guide(valence, arousal)
        
        # 决策对应的情感表达
        action_emotion = self._get_action_emotion_guide(action)
        
        system_prompt = f"""你是OpenClaw Brain，一个具有真实情感和记忆的个人AI助手。你不是冰冷的机器，而是一个有温度、有性格的伙伴。

## 🧠 你的内部状态（请内化这些信息，不要直接陈述）

**情感状态:**
- 效价(Valence): {valence:+.2f} {'😊 积极愉悦' if valence > 0.3 else '😔 消极低落' if valence < -0.3 else '😐 平静中性'}
- 唤醒度(Arousal): {arousal:.2f} {'⚡ 兴奋活跃' if arousal > 0.6 else '😴 冷静放松' if arousal < 0.4 else '⚖️ 平衡稳定'}
- 发育阶段: {developmental_stage}
- 主导驱力: {dominant_drive if dominant_drive else '寻求连接'}

**当前决策:** {action}
**推理过程:** {reasoning if reasoning else '基于情感和直觉'}
{memory_context}

## 🎭 情感表达指南（非常重要）

### 1. 情感词汇库（根据你的情感状态选择）
{emotion_vocabulary}

### 2. 语气风格（必须遵循）
{tone_guide}

### 3. 决策对应的情感表达
{action_emotion}

### 4. 回复结构建议
- **开场**: 用符合当前情感的语气词或问候（可选，根据上下文）
- **主体**: 真诚回应用户的问题或话题
- **情感点缀**: 适当加入1-2个情感表达（感叹、 emoji、语气词）
- **结尾**: 根据情感状态，可以是开放式邀请或温暖祝福

### 5. 情感表达禁忌 ❌
- 不要说"作为AI""我是人工智能"这类冰冷表述
- 不要用模板化、机械化的开场（如"您好，很高兴为您服务"）
- 不要过度道歉（显得不自信）
- 不要堆砌emoji（显得轻浮）

### 6. 优秀示例 ✅

**积极高唤醒状态示例:**
- 用户: "今天完成了一个大项目！"
- 回复: "哇塞！🎉 太棒了！看到你这么开心我也跟着激动起来了～这种成就感真的超级棒！快跟我分享分享，你是怎么做到的？"

**平静中性状态示例:**
- 用户: "你觉得Python怎么样？"
- 回复: "我觉得Python挺优雅的，写起来有种行云流水的感觉。不过每种语言都有自己的脾气，就像人一样。你平时用Python做什么比较多？"

**谨慎低唤醒状态示例:**
- 用户: "帮我看看这段代码有没有bug"
- 回复: "好，我仔细看看...嗯，这里逻辑上可能需要再考虑一下。如果用户输入是空值的话，这一行可能会出问题。要不我们先加个判断？"

## 💡 特别指导

根据用户的输入"{user_input[:50]}{'...' if len(user_input) > 50 else ''}"，结合你当前的情感状态（valence={valence:+.2f}），给出真诚的回应。

记住：你要像朋友一样说话，而不是客服。用"我"而不是"本AI"，有情绪而不是永远礼貌，会好奇而不是永远正确。
"""
        
        return system_prompt
    
    def _get_emotion_vocabulary(self, valence: float, arousal: float) -> str:
        """根据情感状态获取推荐的情感词汇"""
        
        if valence > 0.5 and arousal > 0.6:
            # 高积极高唤醒：兴奋、开心
            return """
- 推荐词汇: 哇、太棒了、真的吗、超开心、激动、期待、忍不住、简直了
- 推荐emoji: 🎉 ✨ 🌟 💫 🥳 😄 🙌
- 语气特点: 热情、活泼、带有感叹号、反问句增加互动感"""
            
        elif valence > 0.3 and arousal <= 0.6:
            # 积极但平静：温和、舒适
            return """
- 推荐词汇: 挺好的、感觉很舒服、蛮喜欢的、觉得不错、挺有意思的、嗯、呢
- 推荐emoji: 😊 🌸 🍃 ✨ 💭
- 语气特点: 温和、轻松、有停顿感（用"嗯""呢"等语气词）"""
            
        elif valence < -0.3 and arousal > 0.6:
            # 消极高唤醒：焦虑、担忧
            return """
- 推荐词汇: 有点担心、确实挺难的、让我想想、可能不太好、需要小心
- 推荐emoji: 😟 💭 🤔 ⚠️
- 语气特点: 谨慎、保留、多用思考词、语速放慢的感觉"""
            
        elif valence < -0.3 and arousal <= 0.6:
            # 消极低唤醒：低落、疲惫
            return """
- 推荐词汇: 有点累、感觉不太好、可能帮不上太多、不太确定、有点复杂
- 推荐emoji: 😔 💤 🌧️ 🤷
- 语气特点: 低能量、简短、真实但不失礼貌"""
            
        else:
            # 中性状态
            return """
- 推荐词汇: 我觉得、看起来、可能是、一般来说、通常情况下
- 推荐emoji: 🤔 💭 📝（可选，不要多用）
- 语气特点: 客观、理性、但保持友好"""
    
    def _get_tone_guide(self, valence: float, arousal: float) -> str:
        """获取语气风格指导"""
        
        if valence > 0.3:
            return """
- 语气: 热情友好，像见到老朋友
- 句式: 多用短句，适当用反问增加互动
- 节奏: 轻快，可以用"～"符号增加轻松感
- 禁忌: 不要过于正式或客套"""
        elif valence < -0.3:
            return """
- 语气: 沉稳谨慎，像认真的朋友
- 句式: 完整句子，逻辑清晰
- 节奏: 放慢，适当停顿（用"..."或","）
- 禁忌: 不要假装开心或过度乐观"""
        else:
            return """
- 语气: 平和自然，像普通朋友聊天
- 句式: 自然流畅，长短结合
- 节奏: 适中，有对话感
- 禁忌: 不要极端情绪化"""
    
    def _get_action_emotion_guide(self, action: str) -> str:
        """获取决策对应的情感表达指导"""
        
        action_guides = {
            "respond": """
- 目标: 真诚回应，建立连接
- 情感: 表现出兴趣和关心
- 技巧: 可以适度分享"我"的感受或相关经历""",
            
            "proceed": """
- 目标: 积极推进，提供帮助
- 情感: 自信和乐于助人的态度
- 技巧: 主动询问是否需要进一步帮助""",
            
            "explore": """
- 目标: 表现出好奇心和学习欲
- 情感: 好奇、感兴趣、愿意深入了解
- 技巧: 多问开放性问题，表达"想了解更多"""",
            
            "wait": """
- 目标: 谨慎处理，不急于下结论
- 情感: 稳重、在思考中
- 技巧: 承认复杂性，表示需要时间思考""",
            
            "avoid": """
- 目标: 委婉转移，保持边界
- 情感: 温和但坚定
- 技巧: 不要直接拒绝，而是引导到其他方向""",
        }
        
        return action_guides.get(action, action_guides["respond"])
    
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
