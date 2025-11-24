from typing import Dict, List, Any, Optional
from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import fetch_leaf_list

logger = get_logger(__name__)


class TaskParser:
    """任务解析器类，用于解析和处理课程任务数据"""

    # 一级任务类型（activities 中的 type）
    TASK_TYPES: Dict[int, str] = {
        2: "课件",
        9: "公告",
        14: "课堂",
        15: "下拉目录",
        17: "视频",
        19: "作业",
        20: "考试"
    }

    # 二级课件类型 leaf_type
    LEAF_TYPES: Dict[int, str] = {
        0: "视频",
        3: "图文",
    }

    @classmethod
    def get_task_type_name(cls, task_type: int) -> str:
        return cls.TASK_TYPES.get(task_type, f"未知类型({task_type})")

    @classmethod
    def get_leaf_type_name(cls, leaf_type: int) -> str:
        return cls.LEAF_TYPES.get(leaf_type, f"未知类型({leaf_type})")

    # ------------------- 二级目录解析：解析 leaf_list ----------------------
    @classmethod
    def parse_leaf_structure(cls, leaf_res: dict, parent_title: str = "") -> list:
        """
        解析下拉目录课件（type = 15）
        leaf_list 结构：
        {
            "title": "",
            "leaf_type": 3,
            "id": 12345,
            ...
        }
        """
        leaf_tasks = []

        data = leaf_res.get("data", {})
        content_info = data.get("content_info", [])

        for section in content_info:
            section_name = section.get("name", "未命名目录")
            logger.info(f"├─ 二级目录：{section_name}")

            leaf_list = section.get("leaf_list", [])

            for leaf in leaf_list:
                leaf_title = leaf.get("title", "未命名课件")
                leaf_type = leaf.get("leaf_type", -1)
                leaf_id = leaf.get("id")

                leaf_type_name = cls.get_leaf_type_name(leaf_type)

                logger.info(
                    f"│   └─ {leaf_type_name}：{leaf_title} "
                    f"(type={leaf_type}, id={leaf_id})"
                )

                leaf_tasks.append({
                    "parent_title": parent_title,
                    "section_name": section_name,
                    "title": leaf_title,
                    "leaf_id": leaf_id,
                    "leaf_type": leaf_type,
                    "leaf_type_name": leaf_type_name,
                    "start_time": leaf.get("start_time"),
                    "deadline": leaf.get("score_deadline")
                })

        return leaf_tasks

    # ----------------------- 一级任务解析 activities -------------------------
    @classmethod
    def parse_tasks(cls, res: Optional[Dict[str, Any]], classroom_id: Optional[int] = None):
        """
        解析课堂任务（主列表 activities）以及下拉目录的课件 leaf_list
        """
        stats: Dict[str, List[Dict[str, Any]]] = {
            "2": [],   # 课件
            "9": [],   # 公告
            "14": [],  # 课堂
            "15": [],  # 下拉目录
            "17": [],  # 视频
            "19": [],  # 作业
            "20": [],  # 考试
            "other": [],
            "leaf_tasks": []  # 二级目录课件
        }

        if not res or "data" not in res:
            logger.error("任务数据为空或格式错误")
            return stats

        activities = res["data"].get("activities", [])
        logger.info(f"检测到 {len(activities)} 个任务点（classroom_id={classroom_id}）")

        for item in activities:

            task_type = item.get("type")
            title = item.get("title", "未命名任务")
            item_id = item.get("id", "无ID")
            courseware_id = item.get("courseware_id")

            content = item.get("content", {})
            deadline = content.get("score_d")

            type_name = cls.get_task_type_name(task_type)

            # 显示一级任务日志
            logger.info(
                f"任务类型：{type_name}\t任务ID:{item_id}\t标题:{title}\t截止时间:{to_datetime(deadline)}"
            )

            # 一级任务分类存储
            key = str(task_type) if task_type in cls.TASK_TYPES else "other"
            stats[key].append({
                "id": item_id,
                "type": task_type,
                "type_name": type_name,
                "title": title,
                "courseware_id": courseware_id,
                "deadline": deadline,
                "raw_data": item
            })

            # ---------------- 解析二级目录任务（下拉目录） ----------------
            if task_type == 15 and courseware_id:
                logger.info(f"  → 检测到下拉目录任务，正在获取二级目录... (courseware_id={courseware_id})")

                leaf_res = fetch_leaf_list(courseware_id)

                if leaf_res:
                    leaf_tasks = cls.parse_leaf_structure(leaf_res, title)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 全局实例（保持原调用方式）
task_parser = TaskParser()
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
