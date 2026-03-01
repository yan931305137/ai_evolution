
import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from src.utils.trace_context import get_trace_id

# 默认日志配置
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "app.log"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class JSONFormatter(logging.Formatter):
    """
    JSON 日志格式化器，用于结构化日志输出
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "path": record.pathname
        }
        
        # 自动注入 trace_id
        trace_id = get_trace_id()
        if trace_id:
            log_record["trace_id"] = trace_id
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # 处理 extra 字段 (如果有)
        if hasattr(record, "extra_data"):
             log_record.update(record.extra_data)
            
        return json.dumps(log_record, ensure_ascii=False)

class TraceAwareRichHandler(RichHandler):
    """
    集成 Trace ID 的 RichHandler
    """
    def emit(self, record):
        trace_id = get_trace_id()
        if trace_id:
            # 将 trace_id (前8位) 添加到消息前缀，或者作为 extra 字段显示
            # 这里简单起见，修改 message 加上 trace_id 前缀
            original_msg = record.msg
            record.msg = f"[{trace_id[:8]}] {original_msg}"
            super().emit(record)
            record.msg = original_msg # 恢复原始消息，以免影响其他 Handler
        else:
            super().emit(record)

def setup_logger(
    name: str = None, 
    level: str = None, 
    log_dir: str = None, 
    log_file: str = None
) -> logging.Logger:
    """
    配置并返回一个 Logger 实例
    
    Args:
        name: Logger 名称，默认 None (root logger)
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)，默认从环境变量 LOG_LEVEL 读取或 INFO
        log_dir: 日志目录，默认 logs
        log_file: 日志文件名，默认 app.log
    
    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    # 确定参数
    level_str = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, level_str, logging.INFO)
    
    log_dir = log_dir or os.getenv("LOG_DIR", DEFAULT_LOG_DIR)
    log_file = log_file or os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
    log_file_format = os.getenv("LOG_FILE_FORMAT", "text").lower()
    
    # 获取 logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除现有的 handlers，防止重复添加
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 1. Console Handler (使用 TraceAwareRichHandler)
    console_handler = TraceAwareRichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False  # 简化输出，不显示完整路径
    )
    console_handler.setLevel(log_level)
    # RichHandler 自带格式化，通常不需要额外设置 formatter，除非有特殊需求
    logger.addHandler(console_handler)
    
    # 2. File Handler (Rotating)
    try:
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_path = os.path.join(log_dir, log_file)
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        
        if log_file_format == "json":
            formatter = JSONFormatter(datefmt=DEFAULT_DATE_FORMAT)
        else:
            formatter = logging.Formatter(
                fmt=DEFAULT_LOG_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT
            )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    except Exception as e:
        # 如果文件日志配置失败（如权限问题），仅输出错误到 stderr，不中断程序
        sys.stderr.write(f"Failed to setup file logging: {e}\n")
    
    # 禁止日志向上传播，避免重复（如果是 root logger 则无所谓）
    logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger，如果 root logger 未配置则先进行默认配置
    通常在模块中使用：logger = get_logger(__name__)
    """
    # 检查 root logger 是否已有 handler，如果没有，说明还没初始化
    if not logging.getLogger().hasHandlers():
        setup_logger()
        
    return logging.getLogger(name)

# 方便直接导入使用的默认 logger
logger = get_logger("OpenClaw")

# Register with Container
from src.core.container import container
container.register(logging.Logger, lambda: logger)
