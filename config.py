"""
项目配置文件

集中管理项目的所有配置参数，支持环境变量覆盖默认值
"""
import os
import random
from typing import Dict, Any


class Config:
    """
    配置类，提供应用程序的所有配置参数
    """

    # ===== 基础配置 =====
    APP_NAME: str = "YuKeTang App"
    APP_VERSION: str = "1.0.0"

    # ===== API配置 =====
    API_BASE_URL: str = "https://www.yuketang.cn"
    API_TIMEOUT: int = 30
    API_RETRY_COUNT: int = 3
    API_RETRY_DELAY: float = 1.0
    # API_REQUEST_DELAY: float =

    # ===== 文件配置 =====
    COOKIE_FILE_PATH: str = "cookie.json"
    DEFAULT_LOG_DIR: str = "logs"
    DEFAULT_LOG_FILE: str = os.path.join(DEFAULT_LOG_DIR, "app.log")

    # ===== 日志配置 =====
    DEFAULT_LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # ===== 任务配置 =====
    DEFAULT_COURSE_INDEX: int = 7
    AUTO_SAVE_TASKS: bool = False

    # ======= 新增：刷课配置 =======
    # 心跳包发送间隔（秒）
    HEARTBEAT_INTERVAL: float = 30.0

    # 播放倍速（1 = 正常速度, 2 = 两倍速）
    VIDEO_SPEED: float = 2.0


    # ===== 读取与覆盖机制 =====
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        config_dict = {}
        for key, value in cls.__dict__.items():
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
                original_value = getattr(cls, key)

                if isinstance(original_value, bool):
                    env_value = os.environ[env_key].lower()
                    setattr(cls, key, env_value in ("true", "1", "yes", "y"))

                elif isinstance(original_value, int):
                    try:
                        setattr(cls, key, int(os.environ[env_key]))
                    except ValueError:
                        pass

                elif isinstance(original_value, float):
                        setattr(cls, key, float(os.environ[env_key]))

                else:
                    setattr(cls, key, os.environ[env_key])

    @classmethod
    def ensure_directories(cls) -> None:
        log_dir = os.path.dirname(cls.DEFAULT_LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)


# 全局配置对象
config = Config()
config.load_from_env()
config.ensure_directories()

__all__ = ['Config', 'config']
