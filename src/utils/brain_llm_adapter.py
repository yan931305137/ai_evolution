"""
Brain LLM Adapter - 将人类级大脑作为LLM使用

使用方式:
    export LLM_PROVIDER=brain
    
或者在代码中:
    from src.utils.llm import LLMClient
    llm = LLMClient(provider="brain")
    response = llm.generate(messages)
"""
import asyncio
import logging
from typing import List, Dict, Generator, Optional, Any
from dataclasses import dataclass

# 尝试导入Brain模块
try:
    from src.brain.human_level_brain import HumanLevelBrain
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False
    logging.warning("Brain模块不可用，请确保src/brain已正确安装")


@dataclass
class BrainResponse:
    """模拟LangChain响应格式"""
    content: str
    reasoning_content: Optional[str] = None
    
    def __post_init__(self):
        # 兼容LangChain响应格式
        self.choices = [type('obj', (object,), {
            'message': type('obj', (object,), {'content': self.content})()
        })()]


class BrainLLMClient:
    """
    Brain作为LLM的适配器
    
    将HumanLevelBrain包装成与LLMClient相同的接口，
    使其可以无缝替换现有LLM调用。
    """
    
    def __init__(
        self,
        start_as_infant: bool = False,
        **kwargs
    ):
        """
        初始化Brain LLM客户端
        
        Args:
            start_as_infant: 是否从婴儿阶段开始发育
            **kwargs: 其他配置参数（保留扩展性）
        """
        if not BRAIN_AVAILABLE:
            raise ImportError("Brain模块不可用，无法初始化BrainLLMClient")
        
        self.provider = "brain"
        self.model_name = "human-level-brain-v1"
        self.brain = HumanLevelBrain(start_as_infant=start_as_infant)
        
        # 统计信息
        self.interaction_count = 0
        self.developmental_stage = self.brain.developmental.stage.name
        
        logging.info(f"🧠 Brain LLM客户端已初始化 | 发育阶段: {self.developmental_stage}")
    
    def _messages_to_stimulus(self, messages: List[Dict[str, str]]) -> Dict:
        """
        将LLM消息格式转换为Brain的感官输入格式
        
        Args:
            messages: OpenAI格式的消息列表
            
        Returns:
            Brain感官输入字典
        """
        # 提取系统提示
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
        
        # 构建感官输入
        sensory_input = {
            "cognitive": user_content,
            "context": "\n".join(context_history[-3:]),  # 最近3轮上下文
            "system_prompt": system_content,
            "energy": 0.8,  # 默认高能量状态
            "event": {
                "relevance_to_self": 0.7,
                "expected_outcome": 0.5,
                "complexity": len(user_content) / 100  # 基于长度估计复杂度
            }
        }
        
        return sensory_input
    
    def _brain_result_to_response(
        self, 
        result: Dict, 
        original_messages: List[Dict[str, str]]
    ) -> BrainResponse:
        """
        将Brain处理结果转换为LLM响应格式
        
        Args:
            result: Brain.experience()的返回结果
            original_messages: 原始消息列表
            
        Returns:
            BrainResponse对象
        """
        cognitive_response = result.get("cognitive_response", {})
        action = getattr(cognitive_response, "action", "respond")
        reasoning = getattr(cognitive_response, "reasoning", "")
        confidence = getattr(cognitive_response, "confidence", 0.8)
        
        # 构建响应内容
        emotional_state = result.get("emotional_state")
        reflection = result.get("reflection", {})
        dominant_drive = result.get("dominant_drive")
        
        # 主响应内容
        if action == "respond":
            # 根据情感状态调整响应语气
            valence = emotional_state.valence if emotional_state else 0
            if valence > 0.5:
                tone = "（带着积极的态度）"
            elif valence < -0.5:
                tone = "（略显担忧地）"
            else:
                tone = ""
            
            content = f"{tone}{reasoning}" if reasoning else "我理解了，请继续。"
        else:
            content = f"[{action}] {reasoning}"
        
        # 构建思考过程（类似于reasoning_content）
        thinking_parts = []
        if reflection:
            thinking_parts.append(f"反思: {reflection.get('reflection', '')}")
        if emotional_state:
            thinking_parts.append(f"情感状态: valence={emotional_state.valence:.2f}")
        if dominant_drive:
            thinking_parts.append(f"主导驱力: {dominant_drive}")
        thinking_parts.append(f"发育阶段: {result.get('developmental_stage', 'UNKNOWN')}")
        thinking_parts.append(f"置信度: {confidence:.2f}")
        
        reasoning_content = "\n".join(thinking_parts) if thinking_parts else None
        
        return BrainResponse(
            content=content,
            reasoning_content=reasoning_content
        )
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        temperature: float = 0.7
    ) -> Any:
        """
        生成响应（同步接口）
        
        与LLMClient.generate()保持相同的接口
        
        Args:
            messages: 消息列表
            stream: 是否流式输出（Brain不支持真正的流式，返回完整响应）
            temperature: 温度参数（Brain中影响随机性）
            
        Returns:
            BrainResponse对象
        """
        try:
            # 转换输入格式
            sensory_input = self._messages_to_stimulus(messages)
            
            # 运行Brain处理（异步转同步）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.brain.experience(sensory_input)
            )
            
            # 更新统计
            self.interaction_count += 1
            self.developmental_stage = result.get("developmental_stage", self.developmental_stage)
            
            # 转换输出格式
            response = self._brain_result_to_response(result, messages)
            
            # 如果开启了流式模式，返回一个模拟的生成器
            if stream:
                def stream_generator():
                    # 将内容分块"流式"输出
                    content = response.content
                    chunk_size = max(1, len(content) // 5)
                    for i in range(0, len(content), chunk_size):
                        yield content[i:i + chunk_size]
                return stream_generator()
            
            return response
            
        except Exception as e:
            logging.error(f"Brain处理失败: {e}")
            # 返回兜底响应
            return BrainResponse(
                content="抱歉，我当前状态不太好，请稍后再试。",
                reasoning_content=f"错误: {str(e)}"
            )
    
    def stream_generate(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式生成（模拟）
        
        Brain不支持真正的流式生成，这里模拟流式效果
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            
        Yields:
            文本片段
        """
        response = self.generate(messages, stream=False, temperature=temperature)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # 模拟流式输出
        words = content.split()
        for word in words:
            yield word + " "
    
    def get_stats(self) -> Dict:
        """
        获取Brain运行统计
        
        Returns:
            统计信息字典
        """
        return {
            "interaction_count": self.interaction_count,
            "developmental_stage": self.developmental_stage,
            "current_emotion": self.brain.report_subjective_experience(),
            "self_concept": self.brain.get_self_concept()
        }
    
    def reset(self, start_as_infant: bool = False):
        """
        重置Brain状态
        
        Args:
            start_as_infant: 是否从婴儿重新开始
        """
        self.brain = HumanLevelBrain(start_as_infant=start_as_infant)
        self.interaction_count = 0
        self.developmental_stage = self.brain.developmental.stage.name
        logging.info(f"🧠 Brain已重置 | 发育阶段: {self.developmental_stage}")


# 便捷函数
def create_brain_llm(
    start_as_infant: bool = False,
    **kwargs
) -> BrainLLMClient:
    """
    创建Brain LLM客户端的便捷函数
    
    Args:
        start_as_infant: 是否从婴儿开始
        **kwargs: 其他配置参数
        
    Returns:
        BrainLLMClient实例
    """
    return BrainLLMClient(
        start_as_infant=start_as_infant,
        **kwargs
    )
