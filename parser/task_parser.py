import time
from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import CourseAPI
from config import config
from utils.video_cache import VideoCache


class TaskParser:
    """任务解析器类，用于解析和处理课程任务数据"""

    TASK_TYPES = {
        2: "课件",
        9: "公告",
        14: "课堂",
        15: "下拉目录",
        16: "图文",
        17: "视频",
        19: "作业",
        20: "考试"
    }

    LEAF_TYPES = {
        0: "视频",
        3: "图文",
    }

    def __init__(self, course_api: CourseAPI, log_file=None, cookie_file=None):
        """初始化 TaskParser，传入 CourseAPI 实例和可选的日志文件路径"""
        self.course_api = course_api
        self.logger = get_logger(__name__, log_file)
        self.video_cache = VideoCache(cookie_file) if cookie_file else None

    def get_task_type_name(self, task_type):
        """获取任务类型中文名称"""
        return self.TASK_TYPES.get(task_type, f"未知类型({task_type})")

    def get_leaf_type_name(self, leaf_type):
        """获取课件类型中文名称"""
        return self.LEAF_TYPES.get(leaf_type, f"未知类型({leaf_type})")

    def parse_leaf_structure(self, leaf_res, parent_title="", classroom_id=None):
        """解析下拉目录中的课件结构"""
        leaf_tasks = []

        data = leaf_res.get("data", {})
        content_info = data.get("content_info", [])

        for chapter in content_info:
            chapter_name = chapter.get("chapter", "未命名章节")
            self.logger.info(f"├─ 一级目录：{chapter_name}")

            for section in chapter.get("section_list", []):
                section_name = section.get("name", "未命名小节")
                self.logger.info(f"│   ├─ 二级目录：{section_name}")

                for leaf in section.get("leaf_list", []):
                    leaf_title = leaf.get("title", "未命名课件")
                    leaf_type = leaf.get("leaf_type", -1)
                    leaf_id = leaf.get("id")
                    leaf_type_name = self.get_leaf_type_name(leaf_type)

                    self.logger.info(
                        f"│   │   └─ {leaf_type_name}：{leaf_title} "
                        f"(type={leaf_type}, id={leaf_id})"
                    )

                    # 视频类型处理
                    if leaf_type == 0:
                        result = self.course_api.fetch_leaf_info(classroom_id, leaf_id)
                        user_id = result["user_id"]
                        sku_id = result["sku_id"]
                        cid = result["course_id"]

                        completed = self.course_api.fetch_video_watch_progress(
                            classroom_id, user_id, cid, leaf_id
                        )
                        self.logger.info(f"视频 {leaf_id} 当前完成状态：{completed}")

                        if completed == 1:
                            self.logger.info(f"视频 {leaf_id} 已完成，跳过刷课")
                            # 刷完标记完成
                            if self.video_cache:
                                self.video_cache.mark_completed(leaf_id)
                            continue

                        self.logger.warning(f"视频 {leaf_id} 未完成，准备模拟观看…")

                        max_retry = 5
                        retry = 0
                        video_length = None

                        while retry < max_retry:
                            prog = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
                            video_length = prog.get("video_length") if prog else None

                            if video_length:
                                break  # 成功获取

                            # 获取不到时，发一次心跳
                            self.course_api.send_video_heartbeat(
                                cid, classroom_id, leaf_id, user_id, sku_id,
                                duration=0,
                                current_time=0
                            )

                            retry += 1
                            self.logger.warning(f"获取视频 {leaf_id} 时长失败，第 {retry}/{max_retry} 次重试…")
                            time.sleep(1)

                        if not video_length:
                            # 超过最大重试次数，设置默认 90 分钟
                            video_length = 5400
                            self.logger.error(
                                f"获取视频 {leaf_id} 时长失败，已达最大重试次数，强制设置为 90 分钟（5400秒）。")

                        self.logger.info(f"视频 {leaf_id} 时长：{video_length}")

                        HEARTBEAT_INTERVAL = config.HEARTBEAT_INTERVAL
                        VIDEO_SPEED = config.VIDEO_SPEED
                        video_frame = 0
                        step = HEARTBEAT_INTERVAL * VIDEO_SPEED * 0.8

                        while video_frame < video_length:
                            video_frame = min(video_frame + step, video_length)
                            self.course_api.send_video_heartbeat(
                                cid, classroom_id, leaf_id, user_id, sku_id,
                                duration=video_length,
                                current_time=video_frame
                            )
                            self.logger.info(f"已观看 {video_frame}/{video_length} 秒（leaf_id={leaf_id}）")
                            time.sleep(HEARTBEAT_INTERVAL)

                        final = self.course_api.fetch_video_watch_progress(
                            classroom_id, user_id, cid, leaf_id
                        )
                        self.logger.info(f"视频 {leaf_id} 最终完成状态：{final}")
                        # 刷完标记完成
                        if self.video_cache:
                            self.video_cache.mark_completed(leaf_id)

                    leaf_tasks.append({
                        "parent_title": parent_title,
                        "chapter_name": chapter_name,
                        "section_name": section_name,
                        "title": leaf_title,
                        "leaf_id": leaf_id,
                        "leaf_type": leaf_type,
                        "leaf_type_name": leaf_type_name,
                        "start_time": leaf.get("start_time"),
                        "deadline": leaf.get("score_deadline"),
                    })

        return leaf_tasks

    def parse_tasks(self, res, classroom_id=None):
        """解析课程任务列表"""
        stats = {str(k): [] for k in self.TASK_TYPES.keys()}
        stats["other"] = []
        stats["leaf_tasks"] = []

        if not res or "data" not in res:
            self.logger.error("任务数据为空或格式错误")
            return stats

        activities = res["data"].get("activities", [])
        self.logger.info(f"检测到 {len(activities)} 个任务点（classroom_id={classroom_id}）")

        for item in activities:
            task_type = item.get("type")
            title = item.get("title", "未命名任务")
            item_id = item.get("id", "无ID")
            content = item.get("content") or {}  # 防止 content 为 None
            leaf_id = content.get("leaf_id")
            courseware_id = item.get("courseware_id")
            content = item.get("content", {})
            deadline = content.get("score_d")
            type_name = self.get_task_type_name(task_type)

            self.logger.info(
                f"任务类型：{type_name}\t任务ID:{item_id}\t标题:{title}\t截止时间:{to_datetime(deadline)}"
            )

            key = str(task_type) if task_type in self.TASK_TYPES else "other"
            stats[key].append({
                "id": item_id,
                "type": task_type,
                "type_name": type_name,
                "title": title,
                "courseware_id": courseware_id,
                "deadline": deadline,
                "raw_data": item
            })

            # === 主目录层级如果存在视频任务，也需要处理 ===
            if task_type == 17 and leaf_id:
                # 检查视频是否已缓存
                if self.video_cache and self.video_cache.is_completed(leaf_id):
                    self.logger.info(f"视频 {leaf_id} 已缓存完成，跳过")
                    continue

                self.logger.info(f"检测到主目录视频：{title} (leaf_id={leaf_id})")

                # 获取必须参数
                result = self.course_api.fetch_leaf_info(classroom_id, leaf_id)
                user_id = result["user_id"]
                sku_id = result["sku_id"]
                cid = result["course_id"]

                completed = self.course_api.fetch_video_watch_progress(
                    classroom_id, user_id, cid, leaf_id
                )
                self.logger.info(f"视频 {leaf_id} 当前完成状态：{completed}")

                if completed == 1:
                    self.logger.info(f"视频 {leaf_id} 已完成，跳过刷课")
                    # 刷完标记完成
                    if self.video_cache:
                        self.video_cache.mark_completed(leaf_id)
                else:
                    self.logger.warning(f"视频 {leaf_id} 未完成，准备模拟观看…")

                    # 获取视频时长
                    max_retry = 5
                    retry = 0
                    video_length = None

                    while retry < max_retry:
                        prog = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
                        video_length = prog.get("video_length") if prog else None

                        if video_length:
                            break  # 成功获取

                        # 获取不到时，发一次心跳
                        self.course_api.send_video_heartbeat(
                            cid, classroom_id, leaf_id, user_id, sku_id,
                            duration=0,
                            current_time=0
                        )

                        retry += 1
                        self.logger.warning(f"获取视频 {leaf_id} 时长失败，第 {retry}/{max_retry} 次重试…")
                        time.sleep(1)

                    if not video_length:
                        # 超过最大重试次数，设置默认 90 分钟
                        video_length = 5400
                        self.logger.error(f"获取视频 {leaf_id} 时长失败，已达最大重试次数，强制设置为 90 分钟（5400秒）。")

                    self.logger.info(f"视频 {leaf_id} 时长：{video_length}")

                    HEARTBEAT_INTERVAL = config.HEARTBEAT_INTERVAL
                    VIDEO_SPEED = config.VIDEO_SPEED
                    video_frame = 0
                    step = HEARTBEAT_INTERVAL * VIDEO_SPEED * 0.8

                    while video_frame < video_length:
                        video_frame = min(video_frame + step, video_length)
                        self.course_api.send_video_heartbeat(
                            cid, classroom_id, leaf_id, user_id, sku_id,
                            duration=video_length,
                            current_time=video_frame
                        )
                        self.logger.info(f"已观看 {video_frame}/{video_length} 秒（leaf_id={leaf_id}）")
                        time.sleep(HEARTBEAT_INTERVAL)

                    final = self.course_api.fetch_video_watch_progress(
                        classroom_id, user_id, cid, leaf_id
                    )
                    self.logger.info(f"视频 {leaf_id} 最终完成状态：{final}")
                    # 刷完标记完成
                    if self.video_cache:
                        self.video_cache.mark_completed(leaf_id)

            # ===== 主目录视频处理结束 =====

            if task_type == 15 and courseware_id:
                self.logger.info(f"  → 检测到下拉目录任务，正在获取二级目录... (courseware_id={courseware_id})")
                leaf_res = self.course_api.fetch_leaf_list(courseware_id)
                if leaf_res:
                    leaf_tasks = self.parse_leaf_structure(leaf_res, title, classroom_id)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 模块级别创建 TaskParser 的实例，方便导入
task_parser = TaskParser(course_api=None)  # 默认 None，main.py 运行时需要传入实例
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
