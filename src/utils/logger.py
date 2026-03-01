
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

# 默认日志配置
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "app.log"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

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
    
    # 获取 logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除现有的 handlers，防止重复添加
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 1. Console Handler (使用 Rich)
    console_handler = RichHandler(
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
