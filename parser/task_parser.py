import time

from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import fetch_leaf_list, course_api

from config import config

# 创建一个统一的日志记录器
logger = get_logger(__name__)


class TaskParser:
    """任务解析器类，用于解析和处理课程任务数据"""

    # 任务类型映射表：数字代码 -> 中文名称
    TASK_TYPES = {
        2: "课件",
        9: "公告",
        14: "课堂",
        15: "下拉目录",
        17: "视频",
        19: "作业",
        20: "考试"
    }

    # 课件类型映射表：数字代码 -> 中文名称
    LEAF_TYPES = {
        0: "视频",
        3: "图文",
    }

    @classmethod
    def get_task_type_name(cls, task_type):
        """获取任务类型的中文名称"""
        return cls.TASK_TYPES.get(task_type, f"未知类型({task_type})")

    @classmethod
    def get_leaf_type_name(cls, leaf_type):
        """获取课件类型的中文名称"""
        return cls.LEAF_TYPES.get(leaf_type, f"未知类型({leaf_type})")

    @classmethod
    def parse_leaf_structure(cls, leaf_res, parent_title="", classroom_id=None, cid=None):

        leaf_tasks = []

        data = leaf_res.get("data", {})
        content_info = data.get("content_info", [])

        for chapter in content_info:
            chapter_name = chapter.get("chapter", "未命名章节")
            logger.info(f"├─ 一级目录：{chapter_name}")

            for section in chapter.get("section_list", []):
                section_name = section.get("name", "未命名小节")
                logger.info(f"│   ├─ 二级目录：{section_name}")

                for leaf in section.get("leaf_list", []):
                    leaf_title = leaf.get("title", "未命名课件")
                    leaf_type = leaf.get("leaf_type", -1)
                    leaf_id = leaf.get("id")
                    leaf_type_name = cls.get_leaf_type_name(leaf_type)

                    logger.info(
                        f"│   │   └─ {leaf_type_name}：{leaf_title} "
                        f"(type={leaf_type}, id={leaf_id})"
                    )

                    # 视频类型（leaf_type == 0）
                    if leaf_type == 0:

                        # 获取 leaf 的 user_id、sku_id
                        result = course_api.fetch_leaf_info(classroom_id, leaf_id)
                        user_id = result["user_id"]
                        sku_id = result["sku_id"]

                        # 查询完成状态
                        completed = course_api.fetch_video_watch_progress(
                            classroom_id, user_id, cid, leaf_id
                        )

                        logger.info(f"视频 {leaf_id} 当前完成状态：{completed}")

                        # 已完成
                        if completed == 1:
                            logger.info(f"视频 {leaf_id} 已完成，跳过刷课")
                            continue

                        logger.warning(f"视频 {leaf_id} 未完成，准备模拟观看…")

                        # 获取视频总时长
                        prog = course_api.get_video_progress(classroom_id, user_id, cid, leaf_id)

                        # 若无进度数据（很常见），使用兜底逻辑
                        if not prog or "video_length" not in prog:
                            logger.warning(f"视频 {leaf_id} 无 video_length，使用默认时长 4976.5 秒")
                            video_length = 4976.5
                        else:
                            video_length = prog.get("video_length", 0)

                        logger.info(f"视频 {leaf_id} 时长：{video_length}")

                        #   开始刷课，发送心跳包
                        HEARTBEAT_INTERVAL = config.HEARTBEAT_INTERVAL
                        VIDEO_SPEED = config.VIDEO_SPEED

                        video_frame = 0
                        step = HEARTBEAT_INTERVAL * VIDEO_SPEED * 0.8

                        while video_frame < video_length:
                            video_frame = min(video_frame + step, video_length)

                            course_api.send_video_heartbeat(
                                cid, classroom_id, leaf_id, user_id, sku_id,
                                duration=video_length,
                                current_time=video_frame
                            )

                            logger.info(
                                f"已观看 {video_frame}/{video_length} 秒（leaf_id={leaf_id}）"
                            )

                            time.sleep(HEARTBEAT_INTERVAL)

                        # 再查一次完成状态
                        final = course_api.fetch_video_watch_progress(
                            classroom_id, user_id, cid, leaf_id
                        )
                        logger.info(f"视频 {leaf_id} 最终完成状态：{final}")

                    # 记录任务
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

    @classmethod
    def parse_tasks(cls, res, classroom_id=None, cid=None):
        """
        解析课程任务列表和其中的子任务
        
        参数:
            res: API返回的课程任务数据
            classroom_id: 教室ID，用于日志记录
            
        返回:
            按任务类型分类的任务统计信息
        """
        # 初始化任务统计字典，按类型存储不同的任务
        stats = {
            "2": [],  # 课件
            "9": [],  # 公告
            "14": [],  # 课堂
            "15": [],  # 下拉目录
            "17": [],  # 视频
            "19": [],  # 作业
            "20": [],  # 考试
            "other": [],  # 其他类型
            "leaf_tasks": []  # 二级目录课件
        }

        # 检查数据是否有效
        if not res or "data" not in res:
            logger.error("任务数据为空或格式错误")
            return stats

        # 获取所有任务
        activities = res["data"].get("activities", [])
        logger.info(f"检测到 {len(activities)} 个任务点（classroom_id={classroom_id}）")

        # 遍历每个任务
        for item in activities:
            # 提取任务信息
            task_type = item.get("type")
            title = item.get("title", "未命名任务")
            item_id = item.get("id", "无ID")
            courseware_id = item.get("courseware_id")

            # 获取任务截止时间
            content = item.get("content", {})
            deadline = content.get("score_d")

            # 获取任务类型的中文名称
            type_name = cls.get_task_type_name(task_type)

            # 记录任务基本信息到日志
            logger.info(
                f"任务类型：{type_name}\t任务ID:{item_id}\t标题:{title}\t截止时间:{to_datetime(deadline)}"
            )

            # 根据任务类型存储任务信息
            key = str(task_type) if task_type in cls.TASK_TYPES else "other"
            stats[key].append({
                "id": item_id,  # 任务ID
                "type": task_type,  # 任务类型
                "type_name": type_name,  # 任务类型名称
                "title": title,  # 任务标题
                "courseware_id": courseware_id,  # 课件ID（如果有）
                "deadline": deadline,  # 截止时间
                "raw_data": item  # 原始数据
            })

            # 处理下拉目录类型的任务（类型为15）
            if task_type == 15 and courseware_id:
                logger.info(f"  → 检测到下拉目录任务，正在获取二级目录... (courseware_id={courseware_id})")

                # 获取下拉目录的内容
                leaf_res = fetch_leaf_list(courseware_id)

                # 如果获取成功，解析下拉目录中的任务
                if leaf_res:
                    leaf_tasks = cls.parse_leaf_structure(leaf_res, title, classroom_id, cid)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 创建全局实例，方便其他模块直接导入使用
task_parser = TaskParser()

# 将类方法暴露为模块级别的函数，方便直接调用
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
