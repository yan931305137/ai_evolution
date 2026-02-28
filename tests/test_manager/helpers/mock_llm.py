"""
Mock LLM 工具

提供 LLM 响应的 Mock 工具
"""

import json
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import MagicMock


class MockLLMHelper:
    """Mock LLM 辅助类"""
    
    @staticmethod
    def create_response(
        content: str = "测试响应",
        tool_calls: Optional[List[Dict]] = None,
        model: str = "gpt-4-test",
        usage: Optional[Dict] = None
    ) -> MagicMock:
        """
        创建 LLM 响应对象
        
        Args:
            content: 响应内容
            tool_calls: 工具调用列表
            model: 模型名称
            usage: Token 使用情况
        
        Returns:
            Mock 响应对象
        """
        response = MagicMock()
        response.content = content
        response.tool_calls = tool_calls or []
        response.model = model
        response.usage = usage or {"prompt_tokens": 100, "completion_tokens": 50}
        
        # 支持 dict() 转换
        response.model_dump.return_value = {
            "content": content,
            "tool_calls": tool_calls or [],
            "model": model,
            "usage": usage or {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        return response
    
    @staticmethod
    def create_tool_call(
        name: str,
        args: Dict[str, Any],
        id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建工具调用对象
        
        Args:
            name: 工具名称
            args: 工具参数
            id: 调用 ID
        
        Returns:
            工具调用字典
        """
        return {
            "id": id or f"call_{hash(name) % 10000}",
            "name": name,
            "args": args
        }
    
    @staticmethod
    def create_streaming_response(
        chunks: List[str],
        delay: float = 0.01
    ) -> List[MagicMock]:
        """
        创建流式响应
        
        Args:
            chunks: 内容块列表
            delay: 每块延迟（秒）
        
        Returns:
            Mock 响应块列表
        """
        responses = []
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_chunk.content = chunk
            mock_chunk.delta = {"content": chunk}
            responses.append(mock_chunk)
        return responses
    
    @staticmethod
    def create_chat_message(
        role: str = "assistant",
        content: str = "消息内容",
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建聊天消息
        
        Args:
            role: 角色 (system/user/assistant)
            content: 消息内容
            name: 名称（可选）
        
        Returns:
            消息字典
        """
        msg = {
            "role": role,
            "content": content
        }
        if name:
            msg["name"] = name
        return msg


class LLMResponseBuilder:
    """
    LLM 响应构建器
    
    用于构建复杂的 LLM 响应场景
    
    使用示例:
        builder = LLMResponseBuilder()
        builder.add_text("首先")
        builder.add_tool_call("search", {"query": "测试"})
        builder.add_text("搜索结果是...")
        response = builder.build()
    """
    
    def __init__(self):
        self._content_parts: List[str] = []
        self._tool_calls: List[Dict] = []
    
    def add_text(self, text: str) -> 'LLMResponseBuilder':
        """添加文本内容"""
        self._content_parts.append(text)
        return self
    
    def add_tool_call(self, name: str, args: Dict[str, Any]) -> 'LLMResponseBuilder':
        """添加工具调用"""
        self._tool_calls.append({
            "name": name,
            "args": args
        })
        return self
    
    def add_code(self, code: str, language: str = "python") -> 'LLMResponseBuilder':
        """添加代码块"""
        self._content_parts.append(f"```{language}\n{code}\n```")
        return self
    
    def add_json(self, data: Dict) -> 'LLMResponseBuilder':
        """添加 JSON 数据"""
        self._content_parts.append(f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```")
        return self
    
    def build(self) -> MagicMock:
        """构建最终响应"""
        content = "\n\n".join(self._content_parts)
        return MockLLMHelper.create_response(content, self._tool_calls)


class MockLLMScenario:
    """
    Mock LLM 场景
    
    预定义的常见 LLM 响应场景
    """
    
    @staticmethod
    def code_generation(language: str = "python", task: str = "排序算法") -> MagicMock:
        """代码生成场景"""
        code = f"""
def {task.replace(' ', '_')}():
    # 实现{task}
    pass
"""
        return MockLLMHelper.create_response(
            content=f"这是{language}实现的{task}：\n```\n{code}\n```",
            tool_calls=[{"name": "generate_code", "args": {"language": language, "task": task}}]
        )
    
    @staticmethod
    def question_answer(question: str = "什么是AI？") -> MagicMock:
        """问答场景"""
        return MockLLMHelper.create_response(
            content=f"关于'{question}'的回答：\n\n这是一个很好的问题..."
        )
    
    @staticmethod
    def error_response(error_type: str = "rate_limit") -> MagicMock:
        """错误响应场景"""
        errors = {
            "rate_limit": "请求过于频繁，请稍后再试",
            "timeout": "请求超时",
            "invalid_key": "API 密钥无效",
            "context_length": "上下文长度超过限制"
        }
        return MockLLMHelper.create_response(
            content=f"错误：{errors.get(error_type, '未知错误')}"
        )
    
    @staticmethod
    def function_call_sequence() -> List[MagicMock]:
        """多步函数调用场景"""
        return [
            MockLLMHelper.create_response(
                content="我需要搜索相关信息",
                tool_calls=[{"name": "web_search", "args": {"query": "测试"}}]
            ),
            MockLLMHelper.create_response(
                content="现在让我分析结果",
                tool_calls=[{"name": "analyze", "args": {"data": "搜索结果"}}]
            ),
            MockLLMHelper.create_response(
                content="分析完成，这是最终答案"
            )
        ]
