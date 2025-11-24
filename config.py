"""
项目配置文件

集中管理项目的所有配置参数，支持环境变量覆盖默认值
"""
import os
from typing import Dict, Any, Optional


class Config:
    """
    配置类，提供应用程序的所有配置参数
    """
    
    # ===== 基础配置 =====
    # 应用名称
    APP_NAME: str = "YuKeTang App"
    
    # 应用版本
    APP_VERSION: str = "1.0.0"
    
    # ===== API配置 =====
    # 雨课堂API基础URL
    API_BASE_URL: str = "https://www.yuketang.cn"
    
    # 默认超时时间（秒）
    API_TIMEOUT: int = 30
    
    # 默认重试次数
    API_RETRY_COUNT: int = 3
    
    # 默认重试间隔（秒）
    API_RETRY_DELAY: float = 1.0
    
    # 请求前延迟时间（秒）
    API_REQUEST_DELAY: float = 2.0
    
    # ===== 文件配置 =====
    # Cookie文件路径
    COOKIE_FILE_PATH: str = "cookie.json"
    
    # 默认任务输出文件
    DEFAULT_TASK_OUTPUT_FILE: str = "tasks.json"
    
    # 默认日志目录
    DEFAULT_LOG_DIR: str = "logs"
    
    # 默认日志文件
    DEFAULT_LOG_FILE: str = os.path.join(DEFAULT_LOG_DIR, "app.log")
    
    # ===== 日志配置 =====
    # 默认日志级别
    DEFAULT_LOG_LEVEL: str = "INFO"
    
    # 日志格式
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    
    # 日志日期格式
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # ===== 任务配置 =====
    # 默认课程索引
    DEFAULT_COURSE_INDEX: int = 7
    
    # 是否自动保存任务数据
    AUTO_SAVE_TASKS: bool = False
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        获取所有配置参数的字典形式
        
        Returns:
            包含所有配置参数的字典
        """
        config_dict = {}
        for key, value in cls.__dict__.items():
            # 排除私有属性和方法
            if not key.startswith("_") and not callable(value):
                config_dict[key] = value
        return config_dict
    
    @classmethod
    def load_from_env(cls) -> None:
        """
        从环境变量加载配置，覆盖默认值
        环境变量格式：YUKETANG_<参数名>
        """
        for key, _ in cls.get_config_dict().items():
            env_key = f"YUKETANG_{key}"
            if env_key in os.environ:
                # 获取原始值的类型
                original_value = getattr(cls, key)
                
                # 根据类型转换环境变量值
                if isinstance(original_value, bool):
                    # 布尔值特殊处理
                    env_value = os.environ[env_key].lower()
                    setattr(cls, key, env_value in ("true", "1", "yes", "y"))
                elif isinstance(original_value, int):
                    try:
                        setattr(cls, key, int(os.environ[env_key]))
                    except ValueError:
                        pass
                elif isinstance(original_value, float):
                    try:
                        setattr(cls, key, float(os.environ[env_key]))
                    except ValueError:
                        pass
                else:
                    # 默认为字符串
                    setattr(cls, key, os.environ[env_key])
    
    @classmethod
    def ensure_directories(cls) -> None:
        """
        确保配置中指定的目录存在
        """
        # 确保日志目录存在
        log_dir = os.path.dirname(cls.DEFAULT_LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 确保输出文件的目录存在
        output_dir = os.path.dirname(cls.DEFAULT_TASK_OUTPUT_FILE)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)


# 全局配置实例
config = Config()

# 从环境变量加载配置
config.load_from_env()

# 确保必要的目录存在
config.ensure_directories()


# 导出配置对象供其他模块使用
__all__ = ['Config', 'config']