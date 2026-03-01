
import contextvars
import uuid
from typing import Optional, Generator
from contextlib import contextmanager

# 定义 ContextVar 存储 trace_id
_trace_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)

def generate_trace_id() -> str:
    """生成一个新的 UUID 作为 trace_id"""
    return str(uuid.uuid4())

def get_trace_id() -> Optional[str]:
    """获取当前的 trace_id"""
    return _trace_id_ctx_var.get()

def set_trace_id(trace_id: str) -> contextvars.Token:
    """设置当前的 trace_id，返回 Token 用于恢复"""
    return _trace_id_ctx_var.set(trace_id)

def reset_trace_id(token: contextvars.Token) -> None:
    """恢复之前的 trace_id"""
    _trace_id_ctx_var.reset(token)

@contextmanager
def trace_context(trace_id: Optional[str] = None) -> Generator[str, None, None]:
    """
    上下文管理器，用于在代码块中自动管理 trace_id
    如果未提供 trace_id，则自动生成一个新的
    """
    if trace_id is None:
        trace_id = generate_trace_id()
    
    token = set_trace_id(trace_id)
    try:
        yield trace_id
    finally:
        reset_trace_id(token)
