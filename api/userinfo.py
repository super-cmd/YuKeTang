import requests
import json
from typing import Optional, Dict, Any
from utils.logger import get_logger
from utils.helpers import load_cookie, smart_decompress
from utils.headers import random_headers
from config import config

logger = get_logger(__name__)


class UserAPI:
    """用户相关API操作类"""
    
    def __init__(self):
        """初始化UserAPI类"""
        self.logger = get_logger(__name__)
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.retry_count = config.API_RETRY_COUNT
        self.retry_delay = config.API_RETRY_DELAY
        self.cookie = load_cookie(config.COOKIE_FILE_PATH)
    
    def _make_request(self, url: str, endpoint: str = "") -> dict:
        """
        通用请求方法
        
        Args:
            url: 完整的URL或相对于base_url的路径
            endpoint: 用于日志的端点描述
            
        Returns:
            解析后的JSON数据或None（如果请求失败）
        """
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"
        
        try:
            headers = random_headers(self.cookie)
            res = requests.get(full_url, headers=headers)
            res.raise_for_status()
            
            text = smart_decompress(res.content)
            return res.json() if res.headers.get("Content-Type", "").startswith("application/json") else json.loads(text)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"{endpoint}请求失败: HTTP错误 {e.response.status_code}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{endpoint}返回非JSON格式数据")
            return None
        except Exception as e:
            logger.error(f"{endpoint}请求异常: {str(e)}")
            return None
    
    def fetch_user_info(self) -> dict:
        """
        获取当前用户信息
        
        Returns:
            包含用户信息的字典或None
        """
        logger.info("正在获取用户信息...")
        url = "/v2/api/web/userinfo"
        data = self._make_request(url, "获取用户信息")
        
        if data:
            user_list = data.get("data", [])
            if isinstance(user_list, list) and len(user_list) > 0:
                user_id = user_list[0].get("user_id", "未知用户ID")
                username = user_list[0].get("name", "未知用户")
                logger.info(f"登录成功: UserID: {user_id}, Username: {username}")
                return data
            else:
                logger.error("用户信息为空或格式错误")
        
        return None


# 创建全局实例以便直接导入使用
user_api = UserAPI()
fetch_user_info = user_api.fetch_user_info
