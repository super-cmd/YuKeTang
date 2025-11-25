import json
import time
import requests
from utils.helpers import load_cookie, smart_decompress
from utils.logger import get_logger
from utils.headers import random_headers
from config import config
import random

# 创建一个统一的日志记录器
logger = get_logger(__name__)


class CourseAPI:
    """课程相关API操作类"""
    
    def __init__(self, cookie: str):
        """初始化课程API类，设置配置信息"""
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
        url = f"https://www.yuketang.cn/v2/api/web/logs/learn/{classroom_id}?actype=-1&page=0&offset=200&sort=-1"

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

    def fetch_leaf_info(self, classroom_id, video_id):
        """
        根据 classroom_id + video_id 获取完整 leaf 信息
        可通过 extra_headers 临时添加或覆盖请求头
        """
        url = f"https://www.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/{classroom_id}/{video_id}/"

        logger.debug(f"请求 leaf_info: {url}")
        # if hasattr(self, "cookie"):
        #     logger.debug(f"当前 cookie: {self.cookie}")

        logger.info(f"正在获取 leaf_info: classroom={classroom_id}, video={video_id}")

        extra_headers = {
            "classroom-id": f"{classroom_id}",
            "xtbz": "ykt"
        }

        # 临时修改 _make_request 传入额外 header
        try:
            if extra_headers:
                response = self._make_request(url, "获取 leaf_info", extra_headers=extra_headers)
            else:
                response = self._make_request(url, "获取 leaf_info")

            if not response or not response.get("success"):
                logger.error(f"leaf_info 接口异常，返回：{response}")
                return None

            data = response.get("data", {})
            if not data:
                logger.error(f"leaf_info data 为空：{response}")
                return None

            result = {
                "video_id": video_id,
                "classroom_id": classroom_id,
                "user_id": data.get("user_id"),
                "sku_id": data.get("sku_id"),
                "course_id": data.get("course_id"),
                "course_name": data.get("name"),
                "price": data.get("price"),
                "university_id": data.get("university_id"),
                "teacher": data.get("teacher"),
                "is_score": data.get("is_score"),
                "is_assessed": data.get("is_assessed"),
                "is_open_type": data.get("is_open_type"),
                "has_classend": data.get("has_classend"),
                "class_start_time": data.get("class_start_time"),
                "class_end_time": data.get("class_end_time"),
                "publish_time": data.get("publish_time"),
                "leaf_id": data.get("id"),
                "leaf_type": data.get("leaf_type"),
                "media": data.get("content_info", {}).get("media", {}),
                "score_info": data.get("content_info", {}).get("score_evaluation", {}),
            }

            logger.info(
                f"获取成功: user_id={result['user_id']}, sku_id={result['sku_id']}, course_id={result['course_id']}"
            )
            return result

        except Exception as e:
            logger.exception(f"获取 leaf_info 发生异常：{e}")
            return None

    def fetch_video_watch_progress(self, classroom_id, user_id, cid, video_id):
        """
        获取视频观看进度
        返回:
            1 = 已完成
            0 = 未完成
            None = 请求/解析失败
        """
        logger.info(f"正在获取视频 {video_id} 的观看进度")

        url = (
            "https://www.yuketang.cn/video-log/get_video_watch_progress/"
            f"?cid={cid}"
            f"&user_id={user_id}"
            f"&classroom_id={classroom_id}"
            f"&video_type=video"
            f"&vtype=rate"
            f"&video_id={video_id}"
            f"&snapshot=1"
        )

        logger.debug(f"请求URL: {url}")

        # ⭐ 关键 header，不加会出现 data = {}
        extra_headers = {
            "xtbz": "ykt"
        }

        response = self._make_request(
            url,
            f"获取视频{video_id}观看进度",
            extra_headers=extra_headers
        )

        # logger.debug(f"响应数据: {response}")

        if not response:
            logger.warning(f"无法获取视频 {video_id} 的观看进度")
            return None

        try:
            # ① data 完全为空 => 代表 未观看 / 未完成
            data = response.get("data", {})
            if not data:
                logger.info(f"视频 {video_id} 的完成状态: 0（未完成 data 空）")
                return 0

            # ② data 存在，但没有对应 video_id
            video_info = data.get(str(video_id))
            if not video_info:
                logger.info(f"视频 {video_id} 的完成状态: 0（无 video_id 数据）")
                return 0

            # ③ 雨课堂视频完成字段
            completed = video_info.get("completed", 0)
            logger.info(f"视频 {video_id} 的完成状态: {completed}")

            return completed

        except Exception as e:
            logger.error(f"解析视频 {video_id} 进度数据时出错: {e}")
            return None

    def get_video_progress(self, classroom_id: int, user_id: int, cid: int, video_id: int):
        """
        获取指定 video_id 的观看进度信息

        参数:
            classroom_id: 教室 ID
            user_id: 用户 ID
            cid: 课程 ID（course_id）
            video_id: 视频 ID

        返回:
            dict:
            {
                "first_point": float,
                "last_point": float,
                "completed": 0/1,
                "watch_length": int,
                "ult": float,
                "rate": float,
                "video_length": float
            }
            或 None
        """

        logger.info(
            f"请求视频进度: classroom_id={classroom_id}, cid={cid}, user_id={user_id}, video_id={video_id}"
        )

        url = (
            "https://www.yuketang.cn/video-log/get_video_watch_progress/"
            f"?cid={cid}"
            f"&user_id={user_id}"
            f"&classroom_id={classroom_id}"
            f"&video_type=video"
            f"&vtype=rate"
            f"&video_id={video_id}"
            f"&snapshot=1"
        )

        logger.debug(f"请求URL: {url}")

        extra_headers = {
            "classroom-id": f"{classroom_id}",
            "xtbz": "ykt"
        }

        try:
            if extra_headers:
                response = self._make_request(url, "获取视频观看进度", extra_headers=extra_headers)
            else:
                response = self._make_request(url, "获取视频观看进度")

            if not response:
                logger.error("服务器返回为空")
                return None

            if response.get("code") != 0:
                logger.error(f"服务器返回错误：{response}")
                return None

            data = response.get("data", {})
            video_key = str(video_id)

            if video_key not in data:
                logger.warning(f"视频 {video_id} 的数据不在 data 中")
                return None

            info = data[video_key]

            result = {
                "first_point": info.get("first_point"),
                "last_point": info.get("last_point"),
                "completed": info.get("completed"),
                "watch_length": info.get("watch_length"),
                "ult": info.get("ult"),
                "rate": info.get("rate"),
                "video_length": info.get("video_length"),
            }

            logger.info(f"视频 {video_id} 进度获取成功：rate={result['rate']}, watch={result['watch_length']}s")
            return result

        except Exception as e:
            logger.exception(f"获取视频进度时出错: {e}")
            return None

    def send_video_heartbeat(self, cid, classroom_id, video_id, user_id, skuid, duration, current_time):
        url = "https://www.yuketang.cn/video-log/heartbeat/"

        timestamp = int(time.time() * 1000)

        heart = {
            "i": 5,
            "et": "loadeddata",
            "p": "web",
            "n": "ali-cdn.xuetangx.com",
            "lob": "cloud4",
            "cp": current_time,
            "fp": 0,
            "tp": 0,
            "sp": 2,
            "ts": str(timestamp),
            "u": int(user_id),
            "uip": "",
            "c": int(cid),
            "v": int(video_id),
            "skuid": skuid,
            "classroomid": classroom_id,
            "cc": video_id,
            "d": duration,
            "pg": f"{video_id}_{''.join(random.sample('0123456789abcdef', 4))}",
            "sq": 1,
            "t": "video"
        }

        payload = {"heart_data": [heart]}

        # 使用随机 headers
        headers = random_headers(self.cookie)
        # 如果需要，临时添加额外字段
        headers.update({
            "classroom-id": str(classroom_id),
            "xtbz": "ykt"
        })

        return requests.post(url, json=payload, headers=headers)
