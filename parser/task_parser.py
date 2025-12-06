import time

import requests

from api.userinfo import UserAPI
from api.homework import HomeworkAPI
from api.WebSocket import YKTWebSocket
from utils.answer_helper import normalize_answer, get_submit_answer
from utils.helpers import inject_cookie_fields
from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import CourseAPI
from config import config
from utils.cache import LeafCache  # 通用缓存

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
        6: "作业"
    }

    def __init__(self, course_api: CourseAPI, user_api: UserAPI, homework_api: HomeworkAPI,log_file=None, cookie_file=None, cookie_str=None):
        self.homework = homework_api
        self.course_api = course_api
        self.user_api = user_api
        self.logger = get_logger(__name__, log_file)
        self.leaf_cache = LeafCache(cookie_file) if cookie_file else None
        self.cookie_str = cookie_str  # 新增 cookie 字符串，用于 WS

    def get_task_type_name(self, task_type):
        return self.TASK_TYPES.get(task_type, f"未知类型({task_type})")

    def get_leaf_type_name(self, leaf_type):
        return self.LEAF_TYPES.get(leaf_type, f"未知类型({leaf_type})")

    def _mark_leaf_completed(self, leaf_id):
        if self.leaf_cache:
            self.leaf_cache.mark_completed(leaf_id)

    def _process_homework(self, leaf_id, classroom_id, sku_id=None):
        """
        处理作业任务
        """
        # 如果有缓存，且作业已完成，则直接跳过
        if self.leaf_cache and self.leaf_cache.is_completed(leaf_id):
            self.logger.info(f"作业 leaf {leaf_id} 已缓存完成，跳过")
            return

        # 获取 leaf 信息
        leaf_info = self.course_api.fetch_leaf_info(classroom_id, leaf_id)
        leaf_type_id = leaf_info.get("leaf_type_id")

        # 获取作业题目列表
        homework_info = self.homework.get_exercise_list(classroom_id, leaf_type_id)
        problems = homework_info.get("problems", [])
        completed_map = homework_info.get("completed_map", {})  # 作业层级的完成状态字典

        self.logger.info(f"作业 leaf {leaf_type_id} 共 {len(problems)} 道题，开始自动提交...")

        for p in problems:
            problem_id = p.get("problem_id")
            is_completed = completed_map.get(problem_id, False)  # 从作业层级字典获取

            self.logger.debug(f"problem_id={problem_id}, is_completed={is_completed}")

            if is_completed:
                self.logger.info(f"题目 {problem_id} 已完成，跳过")
                continue  # 已完成题跳过

            # 请求题库获取答案
            try:
                res = requests.post("https://frpclient04.xhyonline.com:9310/api/questions/search", json=p)
                raw_answer = res.json().get("answer")
            except Exception as e:
                self.logger.error(f"题目 {problem_id} 获取题库答案失败: {str(e)}")
                continue

            self.logger.debug(f"题目 {problem_id} 获取答案: {raw_answer}")

            # 格式化答案
            submit = get_submit_answer(p, raw_answer)
            self.logger.debug(f"题目 {p} 原始答案: {raw_answer}")
            self.logger.debug(f"题目 {problem_id} 提交答案: {submit}")

            # 提交题目答案
            self.homework.problem_apply(classroom_id, problem_id, submit)
            self.logger.info(f"题目 {problem_id} 提交成功: {submit}")

        # 提交完成后标记缓存
        if self.leaf_cache:
            self._mark_leaf_completed(leaf_id)
            self.logger.info(f"作业 leaf {leaf_id} 已全部提交，缓存完成")

    def _process_video(self, leaf_id, classroom_id):
        if not classroom_id:
            return

        if self.leaf_cache and self.leaf_cache.is_completed(leaf_id):
            self.logger.info(f"leaf {leaf_id} 已缓存完成，跳过")
            return

        leaf_info = self.course_api.fetch_leaf_info(classroom_id, leaf_id)
        score_deadline = leaf_info.get("class_end_time")

        if score_deadline:
            now_ms = int(time.time() * 1000)
            if now_ms > score_deadline:
                self.logger.warning(f"leaf {leaf_id} 截止时间已过（{to_datetime(score_deadline)}），跳过")
                return

        user_id = leaf_info.get("user_id")
        sku_id = leaf_info.get("sku_id")
        cid = leaf_info.get("course_id")

        res = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
        completed = res['completed']
        if completed == 1:
            self.logger.info(f"leaf {leaf_id} 已完成，跳过")
            self._mark_leaf_completed(leaf_id)
            return

        self.logger.warning(f"leaf {leaf_id} 未完成，模拟观看中…")
        max_retry, retry = 5, 0
        video_length = None
        while retry < max_retry:
            prog = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
            video_length = prog.get("video_length") if prog else None
            if video_length == 0:
                self.logger.warning(f"leaf {leaf_id} 视频失效或截")
                return
            if video_length:
                break
            self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id, duration=0, current_time=0)
            retry += 1
            self.logger.warning(f"获取视频长度失败，第 {retry}/{max_retry} 次重试…")
            time.sleep(1)

        if not video_length:
            video_length = 5400
            self.logger.error(f"leaf {leaf_id} 视频长度获取失败，默认 5400s")

        HEARTBEAT_INTERVAL = config.HEARTBEAT_INTERVAL
        VIDEO_SPEED = config.VIDEO_SPEED
        video_frame, step = 0, HEARTBEAT_INTERVAL * VIDEO_SPEED * 0.8
        while video_frame < video_length:
            video_frame = min(video_frame + step, video_length)
            self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id,
                                                 duration=video_length, current_time=video_frame)
            self.logger.info(f"已观看 {video_frame}/{video_length} 秒（leaf_id={leaf_id}）")
            time.sleep(HEARTBEAT_INTERVAL)

        final = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
        self.logger.info(f"leaf {leaf_id} 完成状态：{final}")
        self._mark_leaf_completed(leaf_id)

    def _process_leaf(self, leaf_id, leaf_type, classroom_id, sku_id=None):
        """统一处理叶子节点，包括视频和图文"""
        if leaf_type == 0:
            self._process_video(leaf_id, classroom_id)
        elif leaf_type == 3:
            if self.leaf_cache and self.leaf_cache.is_completed(leaf_id):
                self.logger.info(f"leaf {leaf_id} 图文已完成，跳过")
                return
            status = self.course_api.user_article_finish_status(leaf_id, classroom_id)
            if not status:
                self.logger.info(f"leaf {leaf_id} 图文未完成，提交作业")
                self.course_api.user_article_finish(leaf_id, classroom_id, sku_id)
            self._mark_leaf_completed(leaf_id)
        elif leaf_type == 6:  # 作业
            self._process_homework(leaf_id, classroom_id, sku_id)
        else:
            self.logger.warning(f"未知 leaf_type {leaf_type}，leaf_id={leaf_id}")

    def parse_leaf_structure(self, leaf_res, parent_titles=None, classroom_id=None, sku_id=None):
        if parent_titles is None:
            parent_titles = []

        leaf_tasks = []
        data = leaf_res.get("data", {})
        content_info = data.get("content_info", [])

        def _parse_section(section, titles):
            current_titles = titles + [section.get("name") or section.get("chapter") or "未命名章节"]

            for leaf in section.get("leaf_list", []):
                leaf_title = leaf.get("title", "未命名课件")
                leaf_type = leaf.get("leaf_type", -1)
                leaf_id = leaf.get("id")
                leaf_type_name = self.get_leaf_type_name(leaf_type)

                self.logger.info(f"{'│   ' * (len(current_titles)-1)}└─ {leaf_type_name}：{leaf_title} (id={leaf_id})")
                self._process_leaf(leaf_id, leaf_type, classroom_id, sku_id)

                leaf_tasks.append({
                    "parent_titles": current_titles,
                    "title": leaf_title,
                    "leaf_id": leaf_id,
                    "leaf_type": leaf_type,
                    "leaf_type_name": leaf_type_name,
                    "start_time": leaf.get("start_time"),
                    "deadline": leaf.get("score_deadline"),
                })

            for sub_section in section.get("section_list", []):
                _parse_section(sub_section, current_titles)

        for chapter in content_info:
            _parse_section(chapter, parent_titles)

        return leaf_tasks

    def parse_tasks(self, res, classroom_id=None):
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
            content = item.get("content") or {}
            leaf_id = content.get("leaf_id")
            sku_id = content.get("sku_id")
            courseware_id = item.get("courseware_id")
            deadline = content.get("score_d")
            type_name = self.get_task_type_name(task_type)

            self.logger.info(f"任务类型：{type_name}\t任务ID:{item_id}\t标题:{title}\t截止时间:{to_datetime(deadline)}")

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

            if task_type in [16, 17] and leaf_id:
                # 主目录视频或图文处理
                self._process_leaf(leaf_id, 0 if task_type == 17 else 3, classroom_id, sku_id)

            if task_type == 2 and courseware_id:
                # 先检查缓存
                if self.leaf_cache and self.leaf_cache.is_completed(courseware_id):
                    self.logger.info(f"课件 {courseware_id} 已缓存完成，跳过")
                    continue

                view_info = self.course_api.fetch_course_view_depth(classroom_id, courseware_id)
                finish_time = view_info["finish_time"]
                if finish_time:
                    self.logger.info(f"课件 {courseware_id} 已完成")

                    if self.leaf_cache:
                        self.leaf_cache.mark_completed(courseware_id)
                        self.logger.debug(f"课件 {courseware_id} 已缓存完成")

                    continue

                self.logger.debug(f"课件任务，获取课件信息 (courseware_id={courseware_id})")
                card_info = self.course_api.fetch_course_card_info(classroom_id, courseware_id)
                count = card_info["count"]
                self.logger.info(f"课件 {courseware_id} 共 {count} 页")

                user_id = self.user_api.fetch_entity_agents(classroom_id)
                self.logger.info(f"课件 {courseware_id} 获取用户ID：{user_id}")
                new_cookie = inject_cookie_fields(self.cookie_str, classroomId=classroom_id)

                ws_client = YKTWebSocket(
                    cookie=new_cookie,
                    classroom_id=classroom_id,
                    user_id=user_id,
                    cards_id=courseware_id,
                    page_count=count,
                    log_file=self.logger.file if hasattr(self.logger, "file") else None
                )
                ws_client.run()

                # 等待课件观看完成
                while not ws_client.finished:
                    time.sleep(0.2)

                self.logger.info(f"课件 {courseware_id} 已完成，WS 已关闭，继续解析下一任务")

                # 标记缓存
                if self.leaf_cache:
                    self.leaf_cache.mark_completed(courseware_id)
                    self.logger.debug(f"课件 {courseware_id} 已缓存完成")

            if task_type == 15 and courseware_id:
                self.logger.info(f"下拉目录任务，获取二级目录... (courseware_id={courseware_id})")
                leaf_res = self.course_api.fetch_leaf_list(courseware_id)
                if leaf_res:
                    leaf_tasks = self.parse_leaf_structure(leaf_res, parent_titles=[title],
                                                           classroom_id=classroom_id, sku_id=sku_id)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 模块级别创建 TaskParser 实例
task_parser = TaskParser(course_api=None, user_api=None, homework_api=None)  # main.py 运行时传入实际实例
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
