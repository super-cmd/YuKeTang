import requests
import json
import time
from utils.helpers import load_cookie, smart_decompress
from utils.logger import get_logger
from utils.headers import random_headers
from config import config

logger = get_logger(__name__)


class CourseAPI:
    """课程相关API操作类"""
    
    def __init__(self):
        """初始化CourseAPI类"""
        self.logger = get_logger(__name__)
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.retry_count = config.API_RETRY_COUNT
        self.retry_delay = config.API_RETRY_DELAY
        self.request_delay = config.API_REQUEST_DELAY
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
            # 请求前添加延迟，避免频繁请求
            if self.request_delay > 0:
                self.logger.info(f"请求前延迟 {self.request_delay:.2f} 秒: {endpoint or full_url}")
                time.sleep(self.request_delay)
                
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
    
    def fetch_course_list(self) -> dict:
        """
        获取用户课程列表
        
        Returns:
            包含课程列表的字典或None
        """
        logger.info("正在获取课程列表...")
        url = "/v2/api/web/courses/list?identity=2"
        response = self._make_request(url, "获取课程列表")
        
        # 添加调试日志，打印响应数据结构
        if response:
            logger.debug(f"API响应数据类型: {type(response).__name__}")
            logger.debug(f"API响应数据键: {list(response.keys()) if isinstance(response, dict) else None}")
            if 'data' in response:
                logger.debug(f"'data'字段类型: {type(response['data']).__name__}")
                # 只打印部分数据避免日志过长
                if isinstance(response['data'], list) and len(response['data']) > 0:
                    logger.debug(f"第一个课程项类型: {type(response['data'][0]).__name__}")
                    if isinstance(response['data'][0], dict):
                        logger.debug(f"第一个课程项键: {list(response['data'][0].keys())[:5]}")  # 只显示前5个键
        
        return response

    def fetch_learn_log(self, classroom_id: int, raw_response: bool = False):
        """
        根据classroom_id获取学习日志
        :param classroom_id: 班级ID
        :param raw_response: 若为True则返回原始response对象
        """
        logger.info(f"正在获取班级 {classroom_id} 的学习日志...")

        # 构造完整 URL（这里必须手写完整域名，否则不能返回原始 response）
        url = f"https://www.yuketang.cn/v2/api/web/logs/learn/{classroom_id}?actype=-1&page=0&offset=20&sort=-1"

        headers = random_headers(self.cookie)
        try:
            res = requests.get(url, headers=headers)
        except Exception as e:
            logger.error(f"学习日志请求异常: {e}")
            return None

        # ⭐ 如果用户要求返回原始 response 对象
        if raw_response:
            return res

        # ⭐ 兼容旧逻辑：返回 JSON
        try:
            return res.json()
        except:
            try:
                # 可能 gzip 压缩，需要你的 smart_decompress
                text = smart_decompress(res.content)
                return json.loads(text)
            except Exception:
                logger.error("学习日志返回内容无法解析为 JSON")
                return None

    def fetch_leaf_list(self, courseware_id: int) -> dict:
        """
        根据courseware_id获取下拉列表内容
        
        Args:
            courseware_id: 课件ID
            
        Returns:
            包含下拉列表内容的字典或None
        """
        logger.info(f"正在获取课件 {courseware_id} 的下拉列表...")
        url = f"/c27/online_courseware/xty/kls/pub_news/{courseware_id}"
        return self._make_request(url, f"获取下拉列表(courseware_id={courseware_id})")


# 创建全局实例以便直接导入使用
course_api = CourseAPI()
fetch_course_list = course_api.fetch_course_list
fetch_learn_log = course_api.fetch_learn_log
fetch_leaf_list = course_api.fetch_leaf_list
fetch_video_watch_progress = course_api.fetch_video_watch_progress