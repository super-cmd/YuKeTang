from utils.font_decryptor import FontDecryptor
from utils.logger import get_logger
from utils.request_helper import make_request

logger = get_logger(__name__)


class HomeworkAPI:
    """用户相关API操作类"""

    def __init__(self, cookie: str):
        """初始化用户API类，设置配置信息"""
        self.cookie = cookie

    def get_exercise_list(self, classroom_id, homework_id):
        """
        获取指定考试的题目列表，并返回处理后的题目字典
        """
        logger.info("正在获取题目列表...")
        url = f"/mooc-api/v1/lms/exercise/get_exercise_list/{homework_id}/"

        logger.debug("请求URL: %s", url)

        extra_headers = {"classroom-id": str(classroom_id), "xtbz": "ykt"}

        data = make_request(url, cookie=self.cookie, endpoint="获取题目列表", extra_headers=extra_headers)
        if not data or "data" not in data:
            logger.error("返回数据为空或格式错误")
            return None

        homework_data = data["data"]
        homework_name = homework_data.get("name", "未知作业")
        font_url = homework_data.get("font", "")
        logger.debug(font_url)

        problems = []
        for p in homework_data.get("problems", []):
            content = p.get("content", {})
            print(content)
            decryptor = FontDecryptor()
            body = decryptor.decrypt_html(content, font_url)
            problem = {
                "body": body,
                "type": content.get("Type", ""),
                "options": content.get("Options", []),
            }
            problems.append(problem)

        logger.info(f"获取成功: {homework_name}, 共 {len(problems)} 道题目, 字体链接: {font_url}")

        logger.debug("题目列表: %s", problems)

        return {
            "homework_name": homework_name,
            "font_url": font_url,
            "problems": problems
        }
