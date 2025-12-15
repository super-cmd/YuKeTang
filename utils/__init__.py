"""
工具模块

该模块提供各种通用功能，为其他模块提供支持

模块内容:
    - question_bank: 题库相关功能，包括答案查询和处理
    - helpers: 辅助函数，如文件操作、数据解压等
    - headers: HTTP请求头管理
    - logger: 日志系统，支持控制台和文件日志
    - time: 时间处理工具
"""

from .helpers import (
    load_cookie, 
    smart_decompress, 
    save_json, 
    ensure_directory
)
from .headers import (
    random_headers, 
    create_custom_headers,
    USER_AGENTS
)
from .logger import (
    get_logger, 
    set_global_log_level,
    LoggerConfig
)
from .time import (
    to_datetime,
    get_current_timestamp,
    format_time_duration,
    parse_datetime_string,
    get_time_difference
)

__all__ = [
    # helpers
    'load_cookie',
    'smart_decompress',
    'save_json',
    'ensure_directory',
    
    # headers
    'random_headers',
    'create_custom_headers',
    'USER_AGENTS',
    
    # logger
    'get_logger',
    'set_global_log_level',
    'LoggerConfig',
    
    # time
    'to_datetime',
    'get_current_timestamp',
    'format_time_duration',
    'parse_datetime_string',
    'get_time_difference'
]

__version__ = '1.0.0'
__author__ = 'YuKeTang App'
__description__ = '雨课堂工具模块，提供通用功能支持'