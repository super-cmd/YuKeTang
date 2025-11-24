import json
import time
import requests
from utils.helpers import load_cookie, smart_decompress
from utils.logger import get_logger
from utils.headers import random_headers
from config import config

# 创建一个统一的日志记录器
logger = get_logger(__name__)


class CourseAPI:
    """课程相关API操作类"""
    
    def __init__(self):
        """初始化课程API类，设置配置信息"""
        # 使用统一的logger变量
        self.base_url = config.API_BASE_URL  # 基础URL
        self.timeout = config.API_TIMEOUT    # 请求超时时间
        self.retry_count = config.API_RETRY_COUNT  # 重试次数
        self.retry_delay = config.API_RETRY_DELAY  # 重试间隔时间
        self.request_delay = config.API_REQUEST_DELAY  # 请求间隔时间
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
            # 在发送请求前添加延迟，避免频繁请求导致的限制
            if self.request_delay > 0:
                logger.info(f"请求前等待 {self.request_delay:.2f} 秒: {endpoint or full_url}")
                time.sleep(self.request_delay)
                
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
            status_code = e.response.status_code if e.response else "未知"
            logger.error(f"{endpoint}请求失败: HTTP错误 {status_code}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{endpoint}返回的数据不是有效的JSON格式")
            return None
        except Exception as e:
            logger.error(f"{endpoint}请求发生错误: {str(e)}")
            return None
    
    def fetch_course_list(self):
        """
        获取用户的课程列表
        
        返回:
            包含课程列表的字典，如果获取失败则返回None
        """
        logger.info("正在获取课程列表...")
        url = "/v2/api/web/courses/list?identity=2"
        response = self._make_request(url, "获取课程列表")
        
        # 调试日志，帮助理解返回的数据结构
        if response:
            logger.debug(f"响应类型: {type(response).__name__}")
            if isinstance(response, dict):
                logger.debug(f"响应包含的键: {list(response.keys())}")
                if 'data' in response:
                    logger.debug(f"'data'字段类型: {type(response['data']).__name__}")
                    # 只显示部分数据，避免日志过长
                    if isinstance(response['data'], list) and response['data']:
                        first_course = response['data'][0]
                        logger.debug(f"第一个课程类型: {type(first_course).__name__}")
                        if isinstance(first_course, dict):
                            # 只显示前5个键
                            logger.debug(f"第一个课程包含的键: {list(first_course.keys())[:5]}")
        
        return response

    def fetch_learn_log(self, classroom_id, raw_response=False):
        """
        获取指定班级的学习日志
        
        参数:
            classroom_id: 班级ID
            raw_response: 是否返回原始响应对象（默认返回JSON）
            
        返回:
            学习日志数据（JSON格式或原始响应对象），如果失败则返回None
        """
        logger.info(f"正在获取班级 {classroom_id} 的学习日志...")

        # 构建完整的URL（这里需要使用完整域名）
        url = f"https://www.yuketang.cn/v2/api/web/logs/learn/{classroom_id}?actype=-1&page=0&offset=20&sort=-1"

        try:
            # 准备请求头并发送请求
            headers = random_headers(self.cookie)
            res = requests.get(url, headers=headers)
            
            # 如果用户要求原始响应对象，直接返回
            if raw_response:
                return res
            
            # 默认返回JSON格式的数据
            try:
                return res.json()
            except:
                # 如果解析失败，尝试解压后再解析
                try:
                    text = smart_decompress(res.content)
                    return json.loads(text)
                except:
                    logger.error("学习日志返回的内容无法解析为JSON")
                    return None
        
        except Exception as e:
            logger.error(f"获取学习日志时出错: {str(e)}")
            return None

    def fetch_leaf_list(self, courseware_id):
        """
        获取课件的下拉列表内容
        
        参数:
            courseware_id: 课件ID
            
        返回:
            包含下拉列表内容的字典，如果获取失败则返回None
        """
        logger.info(f"正在获取课件 {courseware_id} 的下拉列表...")
        url = f"/c27/online_courseware/xty/kls/pub_news/{courseware_id}"
        return self._make_request(url, f"获取课件{courseware_id}的下拉列表")

    def fetch_video_watch_progress(self, classroom_id, user_id, cid, video_id):
        """
        获取视频的观看状态
        
        参数:
            classroom_id: 教室ID
            user_id: 用户ID
            cid: 课程ID
            video_id: 视频ID
            
        返回:
            视频完成状态（1表示已完成，0表示未完成），如果获取失败则返回None
        """
        logger.info(f"正在获取视频 {video_id} 的观看进度")
        
        # 构建视频进度查询的URL
        url = f"https://www.yuketang.cn/video-log/get_video_watch_progress/?" \
              f"cid={cid}&user_id={user_id}&classroom_id={classroom_id}" \
              f"&video_type=video&vtype=rate&video_id={video_id}&snapshot=1"
        
        logger.debug(f"请求URL: {url}")
        
        # 发送请求获取视频进度
        response = self._make_request(url, f"获取视频{video_id}观看进度")
        
        if response:
            # 解析响应数据，提取视频完成状态
            try:
                data = response.get("data", {})
                video_info = data.get(str(video_id), {})
                completed = video_info.get("completed")
                logger.info(f"视频 {video_id} 的完成状态: {completed}")
                return completed
            except:
                logger.error(f"解析视频 {video_id} 进度数据时出错")
                return None
        else:
            logger.warning(f"无法获取视频 {video_id} 的观看进度")
            return None


# 创建全局实例，方便其他模块直接导入使用
course_api = CourseAPI()

# 将类方法暴露为模块级别的函数，方便直接调用
fetch_course_list = course_api.fetch_course_list
fetch_learn_log = course_api.fetch_learn_log
fetch_leaf_list = course_api.fetch_leaf_list
fetch_video_watch_progress = course_api.fetch_video_watch_progress