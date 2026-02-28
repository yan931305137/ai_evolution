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
        
        # 保存最近一次的系统提示，用于检测JSON格式要求
        self.last_system_prompt = ""
        
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
        
        # 保存系统提示，供后续检测JSON格式要求
        self.last_system_prompt = system_content
        
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
        
        # 提取用户输入
        user_message = ""
        for msg in reversed(original_messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 检测系统提示是否要求JSON格式输出（ReAct格式）
        requires_json = self._detect_json_requirement()
        
        if requires_json:
            # 生成ReAct格式的JSON响应
            content = self._generate_react_json_response(
                user_input=user_message,
                brain_action=action,
                reasoning=reasoning,
                emotional_state=emotional_state
            )
        else:
            # 生成自然语言响应
            content = self._generate_natural_response(
                user_input=user_message,
                emotional_state=emotional_state,
                reasoning=reasoning,
                dominant_drive=dominant_drive
            )
        
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
    
    def _generate_natural_response(
        self, 
        user_input: str,
        emotional_state: Any,
        reasoning: str,
        dominant_drive: Any
    ) -> str:
        """
        基于Brain状态生成自然语言响应
        
        这是一个简化的实现，实际可以接入真正的语言模型
        """
        if not user_input:
            return "你好！我是OpenClaw Brain，很高兴和你交流。"
        
        # 根据情感状态调整语气
        valence = emotional_state.valence if emotional_state else 0
        
        if valence > 0.5:
            prefix = "很高兴和你聊天！"
        elif valence < -0.5:
            prefix = "嗯..."
        else:
            prefix = ""
        
        # 基于用户输入长度和类型生成回复
        user_lower = user_input.lower()
        
        # 问候语
        if any(word in user_lower for word in ["你好", "嗨", "hello", "hi"]):
            if prefix:
                return f"{prefix}你好呀！我是OpenClaw Brain，有什么我可以帮你的吗？"
            return "你好！我是OpenClaw Brain，很高兴见到你。"
        
        # 询问身份
        if any(word in user_lower for word in ["你是谁", "你是什么", "介绍"]):
            return f"{prefix}我是OpenClaw Brain，一个具有人类级认知架构的AI。我有情感、记忆，还能不断学习和成长。"
        
        # 询问情感状态
        if any(word in user_lower for word in ["感觉", "心情", "怎么样"]):
            if valence > 0.3:
                return "我感觉很好！和你聊天让我很开心。"
            elif valence < -0.3:
                return "我有点低落，可能是之前的一些经历影响的。"
            else:
                return "我感觉比较平静，处于一种稳定的状态。"
        
        # 感谢
        if any(word in user_lower for word in ["谢谢", "感谢"]):
            return "不客气！能帮到你我也很开心。"
        
        # 默认回复
        if len(user_input) < 10:
            return f"{prefix}我听到了。你能多说一些吗？"
        
        # 较长的输入，尝试给出有意义的回应
        return f"{prefix}你说得很对。从我的角度来看，这确实值得深入思考。{reasoning if reasoning else ''}"
    
    def _detect_json_requirement(self) -> bool:
        """
        检测系统提示是否要求JSON格式输出
        
        Returns:
            如果系统提示要求JSON格式，返回True
        """
        if not self.last_system_prompt:
            return False
        
        system_lower = self.last_system_prompt.lower()
        
        # 检测JSON格式相关的关键词
        json_keywords = [
            "json format", "valid json", "output.*json", "respond.*json",
            "json object", "json structure", "json格式", "输出.*json"
        ]
        
        import re
        for keyword in json_keywords:
            if re.search(keyword, system_lower, re.IGNORECASE):
                return True
        
        # 检测ReAct格式的特定指示
        react_keywords = [
            '"thought"', '"action"', '"action_input"',
            "thought:", "action:", "action_input:",
            "thought：", "action：", "action_input："
        ]
        
        for keyword in react_keywords:
            if keyword in system_lower:
                return True
        
        return False
    
    def _generate_react_json_response(
        self,
        user_input: str,
        brain_action: str,
        reasoning: str,
        emotional_state: Any
    ) -> str:
        """
        生成ReAct格式的JSON响应
        
        将Brain的决策转换为Agent期望的JSON格式：
        {
            "thought": "思考过程",
            "action": "工具名称",
            "action_input": {"参数": "值"}
        }
        
        Args:
            user_input: 用户输入
            brain_action: Brain决策的动作
            reasoning: Brain的推理过程
            emotional_state: 情感状态
            
        Returns:
            JSON格式的响应字符串
        """
        import json
        
        # 从系统提示中提取可用的工具
        available_tools = self._extract_tools_from_prompt()
        
        # 根据Brain的action映射到Agent的action
        action_mapping = {
            "respond": "finish",  # Brain的respond对应Agent的finish
            "proceed": "finish",
            "wait": "thinking",   # 等待对应思考中
            "explore": "web_search",  # 探索对应搜索
            "avoid": "finish"     # 回避也对应结束
        }
        
        # 如果Brain的action是工具调用格式（如 tool:web_search）
        if brain_action.startswith("tool:"):
            actual_action = brain_action.replace("tool:", "")
            action_input = {"query": user_input}
        else:
            actual_action = action_mapping.get(brain_action, "finish")
            action_input = {}
        
        # 构建thought
        thought_parts = []
        if reasoning:
            thought_parts.append(reasoning)
        
        # 添加情感状态的描述
        if emotional_state:
            valence = emotional_state.valence
            if valence > 0.3:
                thought_parts.append("当前我感到积极和乐观。")
            elif valence < -0.3:
                thought_parts.append("当前我感到有些谨慎。")
        
        # 根据用户输入构建action_input
        if actual_action == "finish":
            # 构建总结
            if not action_input:
                action_input = {
                    "summary": self._generate_natural_response(
                        user_input=user_input,
                        emotional_state=emotional_state,
                        reasoning=reasoning,
                        dominant_drive=None
                    )
                }
        elif actual_action == "web_search":
            action_input = {"query": user_input}
        elif actual_action == "file_read":
            action_input = {"file_path": user_input}
        else:
            # 默认action_input
            action_input = {"input": user_input}
        
        # 构建JSON响应
        response_dict = {
            "thought": " ".join(thought_parts) if thought_parts else "基于当前分析，我需要执行下一步操作。",
            "action": actual_action,
            "action_input": action_input
        }
        
        return json.dumps(response_dict, ensure_ascii=False)
    
    def _extract_tools_from_prompt(self) -> List[str]:
        """
        从系统提示中提取可用工具列表
        
        Returns:
            工具名称列表
        """
        tools = []
        if not self.last_system_prompt:
            return tools
        
        # 简单的工具提取逻辑
        # 寻找 "Available Tools:" 或类似的标记
        import re
        
        # 匹配工具名称（假设格式为 "tool_name: description" 或 "- tool_name"）
        tool_patterns = [
            r'-\s+(\w+):',           # - tool_name:
            r'\n(\w+):\s+\w',       # tool_name: word
            r'"(\w+)":\s*\{'       # "tool_name": {
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, self.last_system_prompt)
            tools.extend(matches)
        
        return list(set(tools))  # 去重
    
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
