import re

from utils.font_decryptor import FontDecryptor
from utils.logger import get_logger
from utils.request_helper import make_request
from utils.helpers import extract_csrf_token

logger = get_logger(__name__)


class HomeworkAPI:
    """作业相关API操作类"""

    TYPE_MAP = {
        "SingleChoice": 0,  # 单选
        "MultipleChoice": 1,  # 多选
        "FillBlank": 2,  # 填空
        "Judgement": 3,  # 判断
        "Essay": 4  # 简答
    }

    def __init__(self, cookie: str):
        self.cookie = cookie

    def get_exercise_list(self, classroom_id, homework_id):
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

        # 优化：字体只下载一次，生成 mapping
        font_mapping = decryptor.decrypt_font(font_url) if font_url else {}

        problems = []
        problem_ids = []
        submit_time_map = {}

        for p in homework_data.get("problems", []):
            content = p.get("content", {})
            user_info = p.get("user", {})

            problem_id = p.get("ProblemID") or p.get("problem_id")
            problem_ids.append(problem_id)

            # 获取提交时间
            submit_time_map[problem_id] = user_info.get("submit_time")

            body_html = content.get("Body", "")
            value = decryptor.decrypt_html(body_html, mapping=font_mapping) if font_mapping else body_html

            q_type_str = content.get("Type", "")
            q_type = self.TYPE_MAP.get(q_type_str, 0)

            options_list = []
            for option in content.get("Options", []):
                option_key = option.get("key", "")
                option_value_html = option.get("value", "")
                option_value = decryptor.decrypt_html(option_value_html,
                                                      mapping=font_mapping) if font_mapping else option_value_html

                options_list.append({
                    "key": option_key,
                    "value": option_value
                })

            problem = {
                "value": value,
                "type": q_type,
                "problem_id": problem_id,
                "options": options_list
            }

            problems.append(problem)

        logger.info(f"获取成功: {homework_name}, 共 {len(problems)} 道题目")
        return {
            "homework_name": homework_name,
            "font_url": font_url,
            "problems": problems,
            "problem_ids": problem_ids,
            "submit_time_map": submit_time_map
        }

    def problem_apply(self, classroom_id, problem_id, answer):
        """
        提交题目答案（POST），自动从 cookie 中提取 csrftoken
        """
        logger.info(f"正在提交题目答案… problem_id={problem_id}, answer={answer}")

        url = "/mooc-api/v1/lms/exercise/problem_apply/"

        # 从 cookie 中提取 csrftoken
        csrftoken = extract_csrf_token(self.cookie)

        extra_headers = {
            "classroom-id": str(classroom_id),
            "xtbz": "ykt",
            "Content-Type": "application/json",
        }

        # 如果有 csrftoken，添加到请求头
        if csrftoken:
            extra_headers["X-CSRFToken"] = csrftoken

        # 根据答案判断体型
        if isinstance(answer, dict):
            # 说明是填空题/简答题
            payload = {
                "classroom_id": classroom_id,
                "problem_id": problem_id,
                "answers": answer  # 注意这里是 answers
            }
        else:
            # 单选、多选、判断题
            payload = {
                "classroom_id": classroom_id,
                "problem_id": problem_id,
                "answer": answer  # 注意这里是 answer
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

