"""
上下文压缩管理器 (Context Compression Manager)

管理长对话的上下文窗口，防止超出 Token 限制
"""
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CompressionStats:
    """压缩统计"""
    original_messages: int = 0
    compressed_messages: int = 0
    original_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: float = 0.0
    summaries_generated: int = 0


class ContextCompressor:
    """
    上下文压缩器
    
    策略:
    1. 保留系统提示和最近的 N 条消息
    2. 对早期消息进行摘要压缩
    3. 丢弃超出窗口的无关消息
    """
    
    def __init__(
        self,
        max_messages: int = 20,           # 最大保留消息数
        max_tokens: int = 8000,           # 最大 Token 数（约等于上下文窗口的80%）
        compress_threshold: int = 15,     # 触发压缩的消息数阈值
        summary_length: int = 200         # 摘要长度（字符）
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.compress_threshold = compress_threshold
        self.summary_length = summary_length
        self.stats = CompressionStats()
        
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """
        估算 Token 数量
        简单估算：每4个字符约1个token
        """
        total_chars = sum(len(json.dumps(msg, ensure_ascii=False)) for msg in messages)
        return total_chars // 4
    
    def compress(self, messages: List[Dict]) -> List[Dict]:
        """
        压缩消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            压缩后的消息列表
        """
        if len(messages) <= self.compress_threshold:
            return messages
        
        self.stats.original_messages = len(messages)
        self.stats.original_tokens = self.estimate_tokens(messages)
        
        # 策略：保留系统提示 + 最近消息 + 早期摘要
        compressed = self._compress_messages(messages)
        
        self.stats.compressed_messages = len(compressed)
        self.stats.compressed_tokens = self.estimate_tokens(compressed)
        if self.stats.original_tokens > 0:
            self.stats.compression_ratio = (
                1 - self.stats.compressed_tokens / self.stats.original_tokens
            )
        
        logger.info(
            f"Context compressed: {self.stats.original_messages} -> "
            f"{self.stats.compressed_messages} messages, "
            f"ratio: {self.stats.compression_ratio:.1%}"
        )
        
        return compressed
    
    def _compress_messages(self, messages: List[Dict]) -> List[Dict]:
        """执行压缩"""
        if not messages:
            return messages
        
        compressed = []
        
        # 1. 保留系统提示（第一条）
        if messages[0].get("role") == "system":
            compressed.append(messages[0])
            messages_to_process = messages[1:]
        else:
            messages_to_process = messages
        
        # 2. 如果消息数量在阈值内，直接保留
        if len(messages_to_process) <= self.max_messages - 1:
            compressed.extend(messages_to_process)
            return compressed
        
        # 3. 策略：保留最近的消息，对早期的进行摘要
        # 保留最近的 N 条消息完整
        recent_keep = 8
        recent_messages = messages_to_process[-recent_keep:]
        
        # 对早期的消息进行摘要
        older_messages = messages_to_process[:-recent_keep]
        if older_messages:
            summary = self._generate_summary(older_messages)
            compressed.append({
                "role": "user",
                "content": f"[Earlier conversation summary]: {summary}"
            })
            self.stats.summaries_generated += 1
        
        # 添加最近的消息
        compressed.extend(recent_messages)
        
        return compressed
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """
        生成消息摘要
        简化实现：提取关键动作和结果
        """
        actions = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            
            if role == "assistant":
                # 尝试提取动作
                if '"action"' in content:
                    try:
                        data = json.loads(content)
                        action = data.get("action", "")
                        if action and action != "finish":
                            actions.append(action)
                    except:
                        pass
            elif role == "user" and content.startswith("Observation:"):
                # 提取观察结果（简化）
                result = content.replace("Observation: ", "")[:50]
                if actions:
                    actions[-1] += f" -> {result}..."
        
        # 生成简洁摘要
        if actions:
            summary = "Performed: " + "; ".join(actions[-5:])  # 只保留最近5个动作
        else:
            summary = f"{len(messages)} messages exchanged"
        
        return summary[:self.summary_length]
    
    def should_compress(self, messages: List[Dict]) -> bool:
        """判断是否需要压缩"""
        if len(messages) > self.compress_threshold:
            return True
        if self.estimate_tokens(messages) > self.max_tokens:
            return True
        return False
    
    def get_stats(self) -> CompressionStats:
        """获取压缩统计"""
        return self.stats


class SlidingWindowCompressor(ContextCompressor):
    """
    滑动窗口压缩器
    
    简单的滑动窗口策略，只保留最近的 N 条消息
    """
    
    def _compress_messages(self, messages: List[Dict]) -> List[Dict]:
        """滑动窗口：只保留最近的消息"""
        if not messages:
            return messages
        
        # 保留系统提示
        compressed = []
        if messages[0].get("role") == "system":
            compressed.append(messages[0])
            # 保留最近的消息
            compressed.extend(messages[-(self.max_messages-1):])
        else:
            compressed.extend(messages[-self.max_messages:])
        
        return compressed


# 便捷函数
def compress_context(
    messages: List[Dict],
    strategy: str = "summary",  # "summary" 或 "sliding_window"
    **kwargs
) -> List[Dict]:
    """
    压缩上下文
    
    Args:
        messages: 消息列表
        strategy: 压缩策略
        **kwargs: 压缩器配置
        
    Returns:
        压缩后的消息列表
    """
    if strategy == "sliding_window":
        compressor = SlidingWindowCompressor(**kwargs)
    else:
        compressor = ContextCompressor(**kwargs)
    
    return compressor.compress(messages)


if __name__ == "__main__":
    # 测试
    test_messages = [
        {"role": "system", "content": "You are an AI agent."},
        {"role": "user", "content": "Start task 1"},
        {"role": "assistant", "content": '{"action": "search", "action_input": {"keyword": "test"}}'},
        {"role": "user", "content": "Observation: Found 5 results"},
        {"role": "assistant", "content": '{"action": "read", "action_input": {"file": "test.py"}}'},
        {"role": "user", "content": "Observation: File content..."},
        {"role": "assistant", "content": '{"action": "write", "action_input": {"file": "output.py"}}'},
        {"role": "user", "content": "Observation: Write successful"},
        {"role": "assistant", "content": '{"action": "finish", "action_input": {}}'},
    ]
    
    compressor = ContextCompressor(max_messages=6, compress_threshold=5)
    compressed = compressor.compress(test_messages)
    
    print("Original:", len(test_messages), "messages")
    print("Compressed:", len(compressed), "messages")
    print("\nCompressed messages:")
    for i, msg in enumerate(compressed):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:60]}...")
