from utils.logger import get_logger
from utils.time import to_datetime
from api.courses import fetch_leaf_list

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
    def parse_leaf_structure(cls, leaf_res, parent_title=""):
        """
        解析下拉目录中的课件内容（当任务类型为15时）
        
        参数:
            leaf_res: 从fetch_leaf_list获取的响应数据
            parent_title: 父级任务的标题
            
        返回:
            包含所有子任务信息的列表
        """
        # 初始化保存子任务的列表
        leaf_tasks = []

        # 从响应中提取数据
        data = leaf_res.get("data", {})
        content_info = data.get("content_info", [])

        # 遍历每个章节
        for section in content_info:
            section_name = section.get("name", "未命名目录")
            logger.info(f"├─ 二级目录：{section_name}")

            # 获取该章节下的所有课件
            leaf_list = section.get("leaf_list", [])

            # 遍历每个课件
            for leaf in leaf_list:
                leaf_title = leaf.get("title", "未命名课件")
                leaf_type = leaf.get("leaf_type", -1)
                leaf_id = leaf.get("id")

                # 获取课件类型的中文名称
                leaf_type_name = cls.get_leaf_type_name(leaf_type)

                # 记录课件信息到日志
                logger.info(
                    f"│   └─ {leaf_type_name}：{leaf_title} "
                    f"(type={leaf_type}, id={leaf_id})"
                )

                # 添加课件信息到结果列表
                leaf_tasks.append({
                    "parent_title": parent_title,  # 父级任务标题
                    "section_name": section_name,  # 章节名称
                    "title": leaf_title,           # 课件标题
                    "leaf_id": leaf_id,            # 课件ID
                    "leaf_type": leaf_type,        # 课件类型
                    "leaf_type_name": leaf_type_name,  # 课件类型名称
                    "start_time": leaf.get("start_time"),  # 开始时间
                    "deadline": leaf.get("score_deadline")  # 截止时间
                })

        return leaf_tasks

    @classmethod
    def parse_tasks(cls, res, classroom_id=None):
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
            "2": [],   # 课件
            "9": [],   # 公告
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
                "id": item_id,              # 任务ID
                "type": task_type,          # 任务类型
                "type_name": type_name,     # 任务类型名称
                "title": title,             # 任务标题
                "courseware_id": courseware_id,  # 课件ID（如果有）
                "deadline": deadline,       # 截止时间
                "raw_data": item            # 原始数据
            })

            # 处理下拉目录类型的任务（类型为15）
            if task_type == 15 and courseware_id:
                logger.info(f"  → 检测到下拉目录任务，正在获取二级目录... (courseware_id={courseware_id})")

                # 获取下拉目录的内容
                leaf_res = fetch_leaf_list(courseware_id)

                # 如果获取成功，解析下拉目录中的任务
                if leaf_res:
                    leaf_tasks = cls.parse_leaf_structure(leaf_res, title)
                    stats["leaf_tasks"].extend(leaf_tasks)

        return stats


# 创建全局实例，方便其他模块直接导入使用
task_parser = TaskParser()

# 将类方法暴露为模块级别的函数，方便直接调用
parse_tasks = task_parser.parse_tasks
parse_leaf_structure = task_parser.parse_leaf_structure
