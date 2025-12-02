import time
import random

from utils import to_datetime
from utils.logger import get_logger
from utils.headers import random_headers
from utils.request_helper import make_request

logger = get_logger(__name__)


class CourseAPI:
    """课程相关API操作类"""

    def __init__(self, cookie: str):
        """初始化课程API类"""
        self.cookie = cookie

    def fetch_course_list(self):
        logger.info("正在获取课程列表...")
        url = "/v2/api/web/courses/list?identity=2"
        return make_request(url, cookie=self.cookie, endpoint="获取课程列表")

    def fetch_learn_log(self, classroom_id, raw_response=False):
        url = f"/v2/api/web/logs/learn/{classroom_id}?actype=-1&page=0&offset=200&sort=-1"
        extra_headers = random_headers(self.cookie)
        response = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取班级 {classroom_id} 学习日志",
            extra_headers=extra_headers
        )
        return response if not raw_response else response

    def fetch_leaf_list(self, courseware_id):
        url = f"/c27/online_courseware/xty/kls/pub_news/{courseware_id}"
        return make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取课件{courseware_id}下拉列表"
        )

    def fetch_leaf_info(self, classroom_id, video_id):
        url = f"/mooc-api/v1/lms/learn/leaf_info/{classroom_id}/{video_id}/"
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}
        response = make_request(
            url,
            cookie=self.cookie,
            endpoint="获取 leaf_info",
            extra_headers=extra_headers
        )
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
            f"获取成功: user_id={result['user_id']}, sku_id={result['sku_id']}, course_id={result['course_id']}, 截止时间={to_datetime(result['class_end_time'])}"
        )
        return result

    def get_video_progress(self, classroom_id, user_id, cid, video_id):
        url = (
            "/video-log/get_video_watch_progress/"
            f"?cid={cid}&user_id={user_id}&classroom_id={classroom_id}"
            f"&video_type=video&vtype=rate&video_id={video_id}&snapshot=1"
        )
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}
        response = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取视频 {video_id} 观看进度",
            extra_headers=extra_headers
        )
        if not response or response.get("code") != 0:
            logger.error(f"视频 {video_id} 进度接口异常: {response}")
            return None

        data = response.get("data", {})
        info = data.get(str(video_id))
        if not info:
            return None

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

    def send_video_heartbeat(self, cid, classroom_id, video_id, user_id, skuid, duration, current_time):
        url = "/video-log/heartbeat/"
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
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}
        return make_request(
            url,
            cookie=self.cookie,
            endpoint="发送视频心跳",
            extra_headers=extra_headers,
            method="POST",
            json_data=payload
        )

    def user_article_finish_status(self, leaf_id, classroom_id):
        url = f"/mooc-api/v1/lms/learn/user_article_finish_status/{leaf_id}/"
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}
        res = make_request(
            url,
            cookie=self.cookie,
            endpoint="获取图文完成状态",
            extra_headers=extra_headers
        )
        if not res or "data" not in res:
            return None
        return res["data"].get("finish", 0) == 1

    def user_article_finish(self, leaf_id, classroom_id, sid):
        url = f"/mooc-api/v1/lms/learn/user_article_finish/{leaf_id}/?cid={classroom_id}&sid={sid}"
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}
        res = make_request(
            url,
            cookie=self.cookie,
            endpoint="图文标记完成",
            extra_headers=extra_headers,
            method="POST"
        )
        return res.get("success", False) if res else False

    def fetch_course_card_info(self, classroom_id, cards_id):
        url = f"/v2/api/web/cards/cover?classroom_id={classroom_id}&cards_id={cards_id}"
        response = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取课件封面 cards_id={cards_id}"
        )
        if not response or response.get("errcode") != 0:
            return None
        data = response.get("data", {})
        result = {
            "count": data.get("count", 0),
            "title": data.get("title"),
            "cover": data.get("cover"),
            "start": data.get("start"),
            "end": data.get("end"),
            "qinghua": data.get("qinghua", False)
        }
        return result

    def fetch_course_view_depth(self, classroom_id, cards_id):
        url = f"/v2/api/web/cards/view_depth?classroom_id={classroom_id}&cards_id={cards_id}"
        response = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取课件观看深度 cards_id={cards_id}"
        )
        if not response or response.get("errcode") != 0:
            return None
        data = response.get("data", {})
        result = {
            "finish_time": data.get("finish_time"),
            "depth_detail": data.get("depth_detail", []),
            "duration": data.get("duration"),
            "depth": data.get("depth"),
            "problem_finish_time": data.get("problem_finish_time"),
            "id": data.get("id"),
        }
        return result
