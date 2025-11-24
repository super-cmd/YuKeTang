from typing import Dict, List, Any, Optional
from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import fetch_leaf_list

logger = get_logger(__name__)


class TaskParser:
    """任务解析器类，用于解析和处理课程任务数据"""

    # 任务类型映射到中文名称
    TASK_TYPES: Dict[int, str] = {
        2: "课件",
        9: "公告",
        14: "课堂",
        15: "下拉目录",
        19: "作业",
        20: "考试"
    }

    @classmethod
    def get_task_type_name(cls, task_type: int) -> str:
        return cls.TASK_TYPES.get(task_type, f"未知类型({task_type})")

    # ------------------- 二级目录解析 ----------------------
    @classmethod
    def parse_leaf_structure(
            cls,
            res: Optional[Dict[str, Any]],
            parent_title: str
    ) -> List[Dict[str, Any]]:

        parsed_leaves = []

        if not res or "data" not in res:
            logger.error("二级任务点数据为空或格式错误")
            return parsed_leaves

        content_info = res["data"].get("content_info", [])
        if not content_info:
            logger.warning(f"任务点 '{parent_title}' 无 content_info")
            return parsed_leaves

        for block in content_info:
            section_list = block.get("section_list", [])
            for section in section_list:

                section_name = section.get("name", "未命名章节")
                logger.info(f"  ├─ 二级目录：{section_name}")

                leaf_list = section.get("leaf_list", [])
                for leaf in leaf_list:
                    title = leaf.get("title", "未命名内容")
                    leaf_id = leaf.get("id", "无ID")
                    start_time = leaf.get("start_time")
                    score_deadline = leaf.get("score_deadline")

                    leaf_info = {
                        "title": title,
                        "leaf_id": leaf_id,
                        "start_time": start_time,
                        "deadline": score_deadline,
                        "section_name": section_name,
                        "parent_title": parent_title
                    }

                    logger.info(
                        f"       └─ 课件：{title} (leaf_id:{leaf_id}) "
                        f"开始时间:{to_datetime(start_time)}  截止时间:{to_datetime(score_deadline)}"
                    )

                    parsed_leaves.append(leaf_info)

        return parsed_leaves

    # ----------------------- 一级任务解析 -------------------------
    @classmethod
    def parse_tasks(cls, res: Optional[Dict[str, Any]], classroom_id: Optional[int] = None):
        """
        解析课堂任务点（含 type=15 的二级结构）
        兼容 main.py 的：parse_tasks(self.learn_log, classroom_id)
        """
        stats: Dict[str, List[Dict[str, Any]]] = {
            "2": [],
            "9": [],
            "14": [],
            "15": [],
            "19": [],
            "20": [],
            "other": [],
            "leaf_tasks": []
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
            if not isinstance(content, dict):
                content = {}

            deadline = content.get("score_d")
            type_name = cls.get_task_type_name(task_type)

            # ★ 日志展示（带中文类型 + 边界保护）
            logger.info(
                f"任务类型：{type_name}\t任务ID:{item_id}\t标题:{title}\t截止时间:{to_datetime(deadline)}"
            )

            # 分类加入
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

            # ---------------- 解析二级目录 ----------------
            if task_type == 15 and courseware_id:
                logger.info(f"  → 检测到下拉目录任务，正在请求二级内容... (courseware_id={courseware_id})")

                leaf_res = fetch_leaf_list(courseware_id)
                if leaf_res:
                    leaf_tasks = cls.parse_leaf_structure(leaf_res, title)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 全局实例（保持你原来的用法）
task_parser = TaskParser()
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
