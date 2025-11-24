import json
import requests
from utils.logger import get_logger
from utils.helpers import load_cookie, smart_decompress
from utils.headers import random_headers
from config import config

# 创建一个统一的日志记录器
logger = get_logger(__name__)


class UserAPI:
    """用户相关API操作类"""
    
    def __init__(self):
        """初始化用户API类，设置配置信息"""
        # 使用统一的logger变量
        self.base_url = config.API_BASE_URL  # 基础URL
        self.timeout = config.API_TIMEOUT    # 请求超时时间
        self.retry_count = config.API_RETRY_COUNT  # 重试次数
        self.retry_delay = config.API_RETRY_DELAY  # 重试间隔时间
        self.cookie = load_cookie(config.COOKIE_FILE_PATH)  # 加载cookie
    
    def _make_request(self, url, endpoint=""):
        """
        发送HTTP请求的通用方法
        
        这个方法处理所有与API的通信，包括构建URL、发送请求、
        处理响应和错误情况。
        
        参数:
            url: 完整的URL或相对于base_url的路径
            endpoint: 请求描述，用于日志记录
            
        返回:
            解析后的JSON数据，如果请求失败则返回None
        """
        # 构建完整的URL
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"
        
        try:
            # 准备请求头和发送请求
            headers = random_headers(self.cookie)
            res = requests.get(full_url, headers=headers)
            res.raise_for_status()  # 如果状态码不是200，抛出异常
            
            # 处理响应内容，支持压缩数据
            text = smart_decompress(res.content)
            
            # 尝试解析为JSON
            if res.headers.get("Content-Type", "").startswith("application/json"):
                return res.json()
            else:
                return json.loads(text)
            
        except requests.exceptions.HTTPError as e:
            # 获取HTTP状态码，如果可用的话
            status_code = e.response.status_code if e.response else "未知"
            logger.error(f"{endpoint}请求失败: HTTP错误 {status_code}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{endpoint}返回的数据不是有效的JSON格式")
            return None
        except Exception as e:
            logger.error(f"{endpoint}请求发生错误: {str(e)}")
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


# 创建全局实例，方便其他模块直接导入使用
user_api = UserAPI()

# 将类方法暴露为模块级别的函数，方便直接调用
fetch_user_info = user_api.fetch_user_info
