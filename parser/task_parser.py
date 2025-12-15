import time

from api.userinfo import UserAPI
from api.homework import HomeworkAPI
from api.WebSocket import YKTWebSocket
from utils.question_bank import get_submit_answer, query_question_bank, prepare_question_data
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
        4: "讨论",
        3: "图文",
        6: "作业"
    }

    def __init__(self, course_api: CourseAPI, user_api: UserAPI, homework_api: HomeworkAPI, log_file=None,
                 cookie_file=None, cookie_str=None):
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

    def _process_homework(self, leaf_id, classroom_id):
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
        submit_time_map = homework_info.get("submit_time_map", {})  # 作业层级的完成状态字典

        self.logger.info(f"作业 leaf {leaf_type_id} 共 {len(problems)} 道题，开始自动提交...")

        for p in problems:
            problem_id = p.get("problem_id")
            submit_time = submit_time_map.get(problem_id, False)  # 从作业层级字典获取
            is_completed = bool(submit_time)

            self.logger.debug(f"problem_id={problem_id}, is_completed={is_completed}")

            if is_completed:
                self.logger.info(f"题目 {problem_id} 已完成")
                continue  # 已完成题跳过

            # 构造发送给题库的数据
            question_data = prepare_question_data(p)
            
            # 请求题库获取答案
            raw_answer = query_question_bank(question_data)

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

        # 获取叶子节点信息
        leaf_info = self.course_api.fetch_leaf_info(classroom_id, leaf_id)
        if not leaf_info:
            self.logger.error(f"获取 leaf_info 失败: leaf_id={leaf_id}")
            return

        score_deadline = leaf_info.get("class_end_time")

        if score_deadline:
            now_ms = int(time.time() * 1000)
            if now_ms > score_deadline:
                self.logger.warning(f"leaf {leaf_id} 截止时间已过（{to_datetime(score_deadline)}），跳过")
                return

        user_id = leaf_info.get("user_id")
        sku_id = leaf_info.get("sku_id")
        cid = leaf_info.get("course_id")

        # 检查必要参数
        if not all([user_id, sku_id, cid]):
            self.logger.error(f"缺少必要参数: leaf_id={leaf_id}, user_id={user_id}, sku_id={sku_id}, cid={cid}")
            return

        # 第一步：先发送初始心跳包激活视频学习状态
        self.logger.info(f"发送初始心跳激活视频状态...")
        try:
            self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id,
                                                 duration=0, current_time=0)
            self.logger.info("初始心跳发送成功，等待服务端初始化...")
            time.sleep(2)  # 等待服务端处理
        except Exception as e:
            self.logger.warning(f"初始心跳发送失败: {e}")
            # 即使失败也继续尝试

        # 第二步：获取视频进度 - 添加重试机制
        max_progress_retries = 3
        progress_retry_count = 0
        res = None

        while progress_retry_count < max_progress_retries:
            # 如果是重试，再发送一次心跳
            if progress_retry_count > 0:
                try:
                    self.logger.info(f"重试前再次发送心跳...")
                    self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id,
                                                         duration=0, current_time=0)
                    time.sleep(1)
                except Exception as e:
                    self.logger.warning(f"重试心跳发送失败: {e}")

            # 获取视频进度
            res = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
            if res is not None:
                self.logger.info(f"成功获取视频进度: completed={res.get('completed', 0)}")
                break

            progress_retry_count += 1
            if progress_retry_count < max_progress_retries:
                self.logger.warning(f"获取视频进度失败，第 {progress_retry_count}/{max_progress_retries} 次重试...")
                time.sleep(2)

        if res is None:
            self.logger.error(f"获取视频进度失败超过 {max_progress_retries} 次，跳过 leaf_id={leaf_id}")
            return

        completed = res.get('completed', 0)
        if completed == 1:
            self.logger.info(f"leaf {leaf_id} 已完成，跳过")
            self._mark_leaf_completed(leaf_id)
            return

        self.logger.warning(f"leaf {leaf_id} 未完成，模拟观看中…")
        max_retry, retry = 5, 0
        video_length = None

        # 获取视频长度 - 同样添加重试和空值检查
        while retry < max_retry:
            prog = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)
            if not prog:
                self.logger.warning(f"获取视频进度失败，第 {retry + 1}/{max_retry} 次重试…")
                retry += 1
                time.sleep(1)
                continue

            video_length = prog.get("video_length")
            if video_length == 0:
                self.logger.warning(f"leaf {leaf_id} 视频失效或已截止")
                return
            if video_length:
                break

            self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id, duration=0,
                                                 current_time=0)
            retry += 1
            self.logger.warning(f"获取视频长度失败，第 {retry}/{max_retry} 次重试…")
            time.sleep(1)

        if not video_length:
            video_length = 5400
            self.logger.error(f"leaf {leaf_id} 视频长度获取失败，默认 5400s")

        HEARTBEAT_INTERVAL = config.HEARTBEAT_INTERVAL
        VIDEO_SPEED = config.VIDEO_SPEED
        video_frame, step = 0, HEARTBEAT_INTERVAL * VIDEO_SPEED * 0.8

        # 观看视频过程
        while video_frame < video_length:
            video_frame = min(video_frame + step, video_length)
            # 发送心跳前也可以添加重试
            heartbeat_success = False
            heartbeat_retries = 3
            for i in range(heartbeat_retries):
                try:
                    self.course_api.send_video_heartbeat(cid, classroom_id, leaf_id, user_id, sku_id,
                                                         duration=video_length, current_time=video_frame)
                    heartbeat_success = True
                    break
                except Exception as e:
                    if i < heartbeat_retries - 1:
                        self.logger.warning(f"发送心跳失败，第 {i + 1}/{heartbeat_retries} 次重试: {e}")
                        time.sleep(1)
                    else:
                        self.logger.error(f"发送心跳失败超过 {heartbeat_retries} 次: {e}")

            if heartbeat_success:
                self.logger.info(f"已观看 {video_frame}/{video_length} 秒（leaf_id={leaf_id}）")
            time.sleep(HEARTBEAT_INTERVAL)

        # 最终检查 - 添加重试
        max_final_retries = 3
        final = None
        for i in range(max_final_retries):
            final = self.course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)

            self.logger.debug(f"final: {final}")

            if final:
                break
            if i < max_final_retries - 1:
                self.logger.warning(f"获取最终状态失败，第 {i + 1}/{max_final_retries} 次重试")
                time.sleep(2)

        if final:
            self.logger.info(f"leaf {leaf_id} 完成状态：{final}")
            self._mark_leaf_completed(leaf_id)
        else:
            self.logger.error(f"leaf {leaf_id} 最终状态获取失败，但已尝试完成")

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
            self._process_homework(leaf_id, classroom_id)
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

                self.logger.info(f"{'│   ' * (len(current_titles) - 1)}└─ {leaf_type_name}：{leaf_title} (id={leaf_id})")
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

            if task_type == 19 and leaf_id:
                # 主目录作业处理
                self.logger.info(f"检测到主目录作业 leaf_id={leaf_id}，开始处理作业")
                self._process_homework(leaf_id, classroom_id)

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
