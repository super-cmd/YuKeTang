import re

from utils.font_decryptor import FontDecryptor
from utils.logger import get_logger
from utils.request_helper import make_request

logger = get_logger(__name__)


class HomeworkAPI:
    """作业相关API操作类"""

    TYPE_MAP = {
        "SingleChoice": 0,  # 单选
        "MultipleChoice": 1,  # 多选
        "Fill": 2,  # 填空
        "Judgement": 3,  # 判断
        "Essay": 4  # 简答
    }

    def __init__(self, cookie: str):
        self.cookie = cookie

    def get_exercise_list(self, classroom_id, homework_id):
        """
        获取作业题目列表
        """
        logger.info("正在获取题目列表...")
        url = f"/mooc-api/v1/lms/exercise/get_exercise_list/{homework_id}/"
        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}

        data = make_request(url, cookie=self.cookie, endpoint="获取题目列表", extra_headers=extra_headers)
        if not data or "data" not in data:
            logger.error("返回数据为空或格式错误")
            return None

        homework_data = data["data"]
        homework_name = homework_data.get("name", "未知作业")
        font_url = homework_data.get("font", "")
        decryptor = FontDecryptor()

        problems = []
        problem_ids = []
        completed_map = {}  # 记录每题是否已完成 {problem_id: True/False}

        for p in homework_data.get("problems", []):
            content = p.get("content", {})
            user_info = p.get("user", {})

            # Problem ID
            problem_id = p.get("ProblemID") or p.get("problem_id")
            problem_ids.append(problem_id)

            # 只记录是否完成
            my_count = user_info.get("my_count", 0)
            completed_map[problem_id] = my_count > 0

            # 解密题目正文
            body_html = content.get("Body", "")
            value = decryptor.decrypt_html(body_html, font_url)

            # 获取题型
            q_type_str = content.get("Type", "")
            q_type = self.TYPE_MAP.get(q_type_str, 0)

            # 处理选项 options
            options_list = []
            for option in content.get("Options", []):
                option_key = option.get("key", "")
                option_value_html = option.get("value", "")

                # 解密选项内容
                option_value = decryptor.decrypt_html(option_value_html, font_url)

                options_list.append({
                    "key": option_key,
                    "value": option_value
                })

            # ⚠ problem 现在包含四个字段
            problem = {
                "value": value,
                "type": q_type,
                "problem_id": problem_id,
                "options": options_list  # 新增字段
            }

            problems.append(problem)

        logger.info(f"获取成功: {homework_name}, 共 {len(problems)} 道题目")

        return {
            "homework_name": homework_name,
            "font_url": font_url,
            "problems": problems,
            "problem_ids": problem_ids,
            "completed_map": completed_map
        }

    def problem_apply(self, classroom_id, problem_id, answer):
        """
        提交题目答案（POST），自动从 cookie 中提取 csrftoken
        """
        logger.info(f"正在提交题目答案… problem_id={problem_id}, answer={answer}")

        url = "/mooc-api/v1/lms/exercise/problem_apply/"

        # 从 cookie 中提取 csrftoken
        csrftoken = None
        if self.cookie:
            match = re.search(r'csrftoken=([a-zA-Z0-9]+)', self.cookie)
            if match:
                csrftoken = match.group(1)

        extra_headers = {
            "classroom-id": str(classroom_id),
            "xtbz": "ykt",
            "Content-Type": "application/json",
        }

        # 如果有 csrftoken，添加到请求头
        if csrftoken:
            extra_headers["X-Csrftoken"] = csrftoken

        payload = {
            "classroom_id": classroom_id,
            "problem_id": problem_id,
            "answer": answer,
        }

        res = make_request(
            url=url,
            cookie=self.cookie,
            endpoint="提交题目答案",
            extra_headers=extra_headers,
            method="POST",
            json_data=payload
        )

        if not res:
            logger.error(f"提交题目 {problem_id} 失败")
            return res

        logger.info(f"题目 {problem_id} 提交成功")
        return res

