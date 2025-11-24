# utils/logger.py
import logging
import os
from typing import Optional
from colorlog import ColoredFormatter


class EnhancedLogger(logging.Logger):
    """增强版日志记录器，添加自定义日志方法"""
    
    def success(self, message, *args, **kwargs):
        """成功日志，使用绿色"""
        self.info(f"[SUCCESS] {message}", *args, **kwargs)
    
    def progress(self, message, *args, **kwargs):
        """进度日志，使用蓝色"""
        self.info(f"[PROGRESS] {message}", *args, **kwargs)
    
    def data(self, message, *args, **kwargs):
        """数据日志，使用青色"""
        self.debug(f"[DATA] {message}", *args, **kwargs)
    
    def hint(self, message, *args, **kwargs):
        """提示日志，使用绿色"""
        self.info(f"[HINT] {message}", *args, **kwargs)


class LoggerConfig:
    """日志配置类"""
    # 默认日志级别
    DEFAULT_LOG_LEVEL = logging.DEBUG
    
    # 控制台日志格式
    CONSOLE_FORMAT = "%(log_color)s%(asctime)s%(reset)s [%(log_color)s%(levelname)-8s%(reset)s] [%(log_color)s%(name)-15s%(reset)s] %(message_log_color)s%(message)s%(reset)s"
    
    # 文件日志格式
    FILE_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    
    # 日期格式
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 日志级别颜色映射
    LOG_COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
    
    # 消息颜色映射
    MESSAGE_COLORS = {
        "DEBUG": "purple",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
    
    # 特殊消息类型颜色映射
    SPECIAL_MESSAGE_COLORS = {
        "SUCCESS": "bold_green",
        "PROGRESS": "bold_blue",
        "DATA": "cyan",
        "HINT": "green",
    }


# 注册自定义Logger类
logging.setLoggerClass(EnhancedLogger)


def get_logger(name: Optional[str] = None, log_file: Optional[str] = None, 
               level: int = LoggerConfig.DEFAULT_LOG_LEVEL) -> EnhancedLogger:
    """
    获取配置好的logger实例
    
    Args:
        name: logger名称，默认为当前模块名
        log_file: 日志文件路径，为None时只输出到控制台
        level: 日志级别
        
    Returns:
        配置好的logging.Logger实例
    """
    logger = logging.getLogger(name or __name__)
    
    # 如果logger已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(level)
    
    # 避免日志重复
    logger.propagate = False
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建彩色格式化器，使用增强的颜色配置
    console_formatter = ColoredFormatter(
        LoggerConfig.CONSOLE_FORMAT,
        datefmt=LoggerConfig.DATE_FORMAT,
        log_colors=LoggerConfig.LOG_COLORS,
        secondary_log_colors={
            'message': LoggerConfig.MESSAGE_COLORS
        },
        reset=True,  # 确保每个日志行后重置颜色
        style='%'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(os.path.abspath(log_file))
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            
            # 创建文件格式化器（无颜色）
            file_formatter = logging.Formatter(
                LoggerConfig.FILE_FORMAT,
                datefmt=LoggerConfig.DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.debug(f"日志文件已配置: {log_file}")
        except Exception as e:
            # 如果文件日志失败，只输出警告而不影响程序运行
            logger.warning(f"无法创建日志文件处理器: {str(e)}")
    
    # 由于我们使用了EnhancedLogger类，自定义方法已经在类中定义，不需要动态添加
    
    return logger


def set_global_log_level(level: int) -> None:
    """
    设置全局日志级别
    
    Args:
        level: 日志级别
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


# 默认 logger
logger = get_logger()
