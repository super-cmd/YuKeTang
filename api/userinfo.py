import json
import time

import requests
from utils.logger import get_logger
from utils.helpers import load_cookie, smart_decompress
from utils.headers import random_headers
from config import config

# 创建一个统一的日志记录器
logger = get_logger(__name__)


class UserAPI:
    """用户相关API操作类"""

    def __init__(self, cookie: str):
        """初始化用户API类，设置配置信息"""
        # 使用统一的logger变量
        self.base_url = config.API_BASE_URL  # 基础URL
        self.timeout = config.API_TIMEOUT    # 请求超时时间
        self.retry_count = config.API_RETRY_COUNT  # 重试次数
        self.retry_delay = config.API_RETRY_DELAY  # 重试间隔时间
        self.request_delay = config.API_REQUEST_DELAY  # 请求间隔时间
        self.cookie = cookie  # 加载cookie

    def _make_request(self, url, endpoint="", extra_headers=None):
        """
        发送HTTP请求的通用方法，支持临时插入额外 header

        参数:
            url: 完整的URL或相对于 base_url 的路径
            endpoint: 请求描述，用于日志记录
            extra_headers: dict，可临时添加或覆盖请求头

        返回:
            解析后的 JSON 数据，如果请求失败则返回 None
        """
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"

        try:
            # 延迟请求，防止频繁请求
            if getattr(self, "request_delay", 0) > 0:
                logger.info(f"请求前等待 {self.request_delay:.2f} 秒: {endpoint or full_url}")
                time.sleep(self.request_delay)

            # 构建请求头
            headers = random_headers(getattr(self, "cookie", None))
            if extra_headers:
                headers.update(extra_headers)  # 临时覆盖或添加额外 header

            # 发送 GET 请求
            res = requests.get(full_url, headers=headers)
            res.raise_for_status()

            # 处理响应内容
            text = smart_decompress(res.content)

            # 尝试解析为 JSON
            if res.headers.get("Content-Type", "").startswith("application/json"):
                return res.json()
            else:
                return json.loads(text)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "未知"
            logger.error(f"{endpoint} 请求失败: HTTP错误 {status_code}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{endpoint} 返回的数据不是有效的 JSON 格式")
            return None
        except Exception as e:
            logger.error(f"{endpoint} 请求发生错误: {str(e)}")
            return None

    def fetch_user_info(self):
        """
        获取当前用户的基本信息

        返回:
            包含用户信息的字典，如果获取失败则返回None
        """
        logger.info("正在获取用户信息...")
        url = "/v2/api/web/userinfo"

        # 发送请求获取用户信息
        data = self._make_request(url, "获取用户信息")

        if data:
            # 从响应中提取用户列表
            user_list = data.get("data", [])

            # 验证用户列表是否有效
            if isinstance(user_list, list) and user_list:
                # 获取第一个用户的信息
                first_user = user_list[0]
                user_id = first_user.get("user_id", "未知用户ID")
                username = first_user.get("name", "未知用户")

                logger.info(f"登录成功: 用户ID: {user_id}, 用户名: {username}")
                return data
            else:
                logger.error("用户信息为空或格式错误")

        return None


    # 添加fetch_user_id函数，用于从topic_robot_config接口获取用户ID
    def fetch_user_id(classroom_id, cid):
        """
        从topic_robot_config接口获取用户ID

        参数:
            classroom_id: 教室ID
            cid: 课程ID

        返回:
            用户ID（字符串或None）
        """
        logger.info(f"尝试从topic_robot_config接口获取用户ID (classroom_id={classroom_id}, cid={cid})")

        # 构建请求URL
        url = f"https://www.yuketang.cn/v2/api/web/topic_robot_config/{cid}/{classroom_id}"

        try:
            # 准备请求头
            cookie = load_cookie(config.COOKIE_FILE_PATH)
            headers = random_headers(cookie)

            # 发送请求
            response = requests.get(url, headers=headers, timeout=config.API_TIMEOUT)
            response.raise_for_status()

            # 解析响应
            data = response.json()

            # 提取用户ID
            user_id = data.get("data", {}).get("user_id")

            if user_id:
                logger.info(f"成功从topic_robot_config获取用户ID: {user_id}")
                return str(user_id)
            else:
                logger.warning("从topic_robot_config未获取到用户ID")
                return None

        except Exception as e:
            logger.error(f"获取topic_robot_config失败: {str(e)}")
            return None

    def fetch_entity_agents(self, entity_id):
        logger.info(f"正在获取课件资源 entity_id={entity_id}")

        url = (
            "/c27/online_courseware/agent/entity_agents/"
            f"?entity_type=1"
            f"&entity_id={entity_id}"
            f"&category=1"
            f"&has_role=1"
        )

        extra_headers = {
            "Xt-Agent": "web",
            "Xtbz": "ykt",
        }

        data = self._make_request(url, "获取课件资源", extra_headers)

        logger.debug(f"url:{url}")
        logger.debug( data)

        if not data:
            return None

        # 你要的：直接提取 login_user_id
        return data.get("data", {}).get("login_user_id")


