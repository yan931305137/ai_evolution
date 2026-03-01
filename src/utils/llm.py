"""
LLM Client for Coze Platform
使用 LangChain 和 OpenAI 兼容接口调用 Coze 平台的大模型
"""
import os
import json
import logging
from typing import List, Dict, Generator, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 尝试导入 Coze 工具包，如果不存在则使用 None
try:
    from coze_coding_utils.runtime_ctx.context import default_headers, new_context
    COZE_UTILS_AVAILABLE = True
except ImportError:
    COZE_UTILS_AVAILABLE = False
    default_headers = None
    new_context = None


class LLMClient:
    """Wrapper for LLM Platform using LangChain ChatOpenAI.
    Supports Coze, Volcengine Ark, and Human-Level Brain.
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None, provider: str = None, **kwargs):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: API Key
            base_url: Base URL
            model_name: 模型名称
            provider: 服务提供商 ("coze", "ark", "brain"), 默认从配置文件读取
            **kwargs: 额外参数
        """
        # 尝试从配置文件读取
        try:
            from src.utils.config import cfg
            if not provider:
                # 显式读取环境变量，确保优先级
                provider = os.getenv("LLM_PROVIDER") or cfg.llm_provider
            self._config = cfg.llm_config
        except Exception:
            self._config = {}
        
        self.provider = provider or "coze"
        
        # Brain模式：使用人类级大脑
        if self.provider == "brain":
            self._init_brain_mode(**kwargs)
            return
        
        # Hybrid模式：Brain + LLM
        if self.provider == "hybrid":
            self._init_hybrid_mode(**kwargs)
            return
        
        if self.provider == "ark":
            self.api_key = api_key or os.getenv("ARK_API_KEY") or self._config.get("api_key")
            self.base_url = base_url or os.getenv("ARK_BASE_URL") or self._config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            self.model_name = model_name or os.getenv("ARK_MODEL") or self._config.get("model_name", "doubao-seed-2-0-pro-260215")
            extra_body = {}
            default_headers_config = None
        else:
            # Default to Coze
            self.api_key = api_key or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY") or self._config.get("api_key")
            self.base_url = base_url or os.getenv("COZE_INTEGRATION_MODEL_BASE_URL") or self._config.get("base_url", "https://api.coze.cn/open_api/v2")
            self.model_name = model_name or os.getenv("COZE_MODEL") or self._config.get("model_name", "doubao-seed-2-0-pro-260215")
            extra_body = {"thinking": {"type": "enabled"}}
            default_headers_config = default_headers(new_context(method="chat")) if COZE_UTILS_AVAILABLE else None
        
        if not self.api_key:
            logging.warning(f"API Key not found for provider {self.provider}. Please set the environment variable.")
        
        if not self.base_url:
            logging.warning(f"Base URL not found for provider {self.provider}. Please set the environment variable.")
        
        # 初始化 LangChain ChatOpenAI
        self.client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self._config.get("temperature", 0.7),
            streaming=True,
            timeout=self._config.get("timeout", 600),
            extra_body=extra_body,
            default_headers=default_headers_config
        )
        
        # 交互样本保存路径
        self.dataset_path = "training/dataset.jsonl"
    
    def _init_brain_mode(self, **kwargs):
        """初始化Brain模式"""
        try:
            from src.utils.brain_llm_adapter import BrainLLMClient
            
            # 从配置文件获取Brain设置
            brain_config = self._config.get("brain", {})
            
            # 合并kwargs和配置文件
            init_params = {
                "start_as_infant": brain_config.get("start_as_infant", False),
                **kwargs
            }
            
            self._brain_client = BrainLLMClient(**init_params)
            self.model_name = self._brain_client.model_name
            
            # 设置兼容属性（Brain模式不需要API Key）
            self.api_key = "brain_mode_no_api_key_needed"
            self.base_url = "local_brain"
            
            logging.info(f"🧠 LLMClient已切换到Brain模式 | 模型: {self.model_name}")
            logging.info(f"   配置来源: config.yaml | 婴儿模式: {init_params['start_as_infant']}")
            
        except ImportError as e:
            logging.error(f"Brain模块导入失败: {e}")
            raise RuntimeError("无法初始化Brain模式，请确保src/brain和src/utils/brain_llm_adapter.py存在")
    
    def _init_hybrid_mode(self, **kwargs):
        """初始化Brain + LLM混合模式"""
        try:
            from src.utils.hybrid_brain_client import HybridBrainClient
            
            # 从配置文件获取设置
            hybrid_config = self._config.get("hybrid", {})
            brain_config = self._config.get("brain", {})
            
            # 合并配置
            init_params = {
                "start_as_infant": hybrid_config.get("start_as_infant", brain_config.get("start_as_infant", False)),
                "llm_provider": hybrid_config.get("llm_provider", None),
                **kwargs
            }
            
            self._hybrid_client = HybridBrainClient(**init_params)
            self.model_name = self._hybrid_client.model_name
            
            # 设置兼容属性
            self.api_key = "hybrid_mode_uses_llm_key"
            self.base_url = "hybrid_brain_llm"
            
            logging.info(f"🧠🤖 LLMClient已切换到Hybrid混合模式 | 模型: {self.model_name}")
            logging.info(f"   Brain发育阶段: {self._hybrid_client.developmental_stage}")
            logging.info(f"   LLM提供商: {self._hybrid_client.llm_provider}")
            
        except ImportError as e:
            logging.error(f"混合模式模块导入失败: {e}")
            raise RuntimeError("无法初始化Hybrid模式，请确保所有依赖模块存在")
    
    def _extract_text_from_content(self, content: any) -> str:
        """Extract text from message content which could be string or list."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    elif "type" in item and item["type"] == "text":
                        text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        return ""

    def _is_low_complexity_scene(self, messages: List[Dict[str, str]]) -> bool:
        """判断是否属于低复杂度场景"""
        low_complexity_keywords = [
            "创意生成", "生成文案", "生成计划", "总结内容", "常规问答",
            "生成列表", "生成JSON", "翻译", "改写", "扩写", "缩写"
        ]
        all_content = "".join([self._extract_text_from_content(msg.get("content", "")) for msg in messages])
        return any(keyword in all_content for keyword in low_complexity_keywords)
    
    def _save_interaction_sample(self, messages: List[Dict[str, str]], response_content: str):
        """保存交互样本到微调数据集"""
        try:
            # 提取instruction和input
            instruction = self._extract_text_from_content(messages[0].get("content", "")) if messages else ""
            input_content = "".join([self._extract_text_from_content(msg.get("content", "")) for msg in messages[1:-1]]) if len(messages) > 2 else ""
            
            sample = {
                "instruction": instruction,
                "input": input_content,
                "output": response_content,
                "timestamp": datetime.now().isoformat(),
                "scene": "low_complexity" if self._is_low_complexity_scene(messages) else "high_complexity"
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
            
            # 追加写入数据集
            with open(self.dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            
            logging.debug(f"已保存交互样本到数据集: {self.dataset_path}")
        except Exception as e:
            logging.warning(f"保存交互样本失败: {e}")
    
    def _normalize_content(self, content: any) -> any:
        """Normalize content to OpenAI format if it's in Ark format."""
        if not isinstance(content, list):
            return content
            
        normalized_content = []
        for item in content:
            if isinstance(item, dict):
                # Handle Ark format
                if item.get("type") == "input_text":
                    normalized_content.append({
                        "type": "text",
                        "text": item.get("text", "")
                    })
                elif item.get("type") == "input_image":
                    normalized_content.append({
                        "type": "image_url",
                        "image_url": {"url": item.get("image_url", "")}
                    })
                else:
                    # Keep as is (assuming it's already compatible or unknown)
                    normalized_content.append(item)
            else:
                normalized_content.append(item)
        return normalized_content

    def _convert_messages_to_langchain(self, messages: List[Dict[str, str]]) -> List:
        """将消息字典转换为 LangChain 消息对象"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            raw_content = msg.get("content", "")
            content = self._normalize_content(raw_content)
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    def generate(self, messages: List[Dict[str, str]], stream: bool = False, temperature: float = 0.7) -> any:
        """
        生成文本（非流式）
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
            temperature: 温度参数
        
        Returns:
            响应对象
        """
        # Brain模式：使用人类级大脑
        if self.provider == "brain":
            return self._brain_client.generate(messages, stream=stream, temperature=temperature)
        
        # Hybrid模式：Brain + LLM
        if self.provider == "hybrid":
            return self._hybrid_client.generate(messages, stream=stream, temperature=temperature)
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages_to_langchain(messages)
            
            # 调用 Coze API
            if stream:
                # 流式生成
                response = self.client.stream(langchain_messages, temperature=temperature)
                # 返回生成器
                def stream_generator():
                    for chunk in response:
                        if hasattr(chunk, 'content') and chunk.content:
                            yield chunk.content
                return stream_generator()
            else:
                # 非流式生成
                response = self.client.invoke(langchain_messages, temperature=temperature)
                
                # 保存交互样本
                if response and hasattr(response, 'content'):
                    self._save_interaction_sample(messages, response.content)
                
                return response
                
        except Exception as e:
            logging.error(f"Coze API 调用失败: {e}")
            # 返回兜底响应
            return self._get_fallback_response(messages)
    
    def _get_fallback_response(self, messages: List[Dict[str, str]]) -> any:
        """获取兜底响应"""
        # 检测是否需要JSON
        need_json = any("JSON" in msg.get("content", "") for msg in messages)
        
        fallback_text = "抱歉，当前服务暂时繁忙，请稍后再试。"
        if need_json:
            fallback_text = '{\n    "thought": "System error, returning fallback JSON.",\n    "action": "finish",\n    "action_input": {\n        "summary": "LLM Connection Failed. Please check network."\n    }\n}'
        
        # 创建模拟响应对象
        class FallbackResponse:
            def __init__(self, content):
                self.content = content
                self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': content})()})()]
        
        return FallbackResponse(fallback_text)
    
    def stream_generate(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Generator[str, None, None]:
        """
        流式生成文本
        
        Args:
            messages: 消息列表
            temperature: 温度参数
        
        Yields:
            文本片段
        """
        # Brain模式：使用人类级大脑
        if self.provider == "brain":
            yield from self._brain_client.stream_generate(messages, temperature=temperature)
            return
        
        # Hybrid模式：Brain + LLM
        if self.provider == "hybrid":
            yield from self._hybrid_client.stream_generate(messages, temperature=temperature)
            return
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages_to_langchain(messages)
            
            # 流式生成
            for chunk in self.client.stream(langchain_messages, temperature=temperature):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            logging.error(f"Coze 流式生成失败: {e}")
            yield f"\n[Error: {str(e)}]"
