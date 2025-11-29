# main.py
import json
import sys
import os
from typing import Optional

from api.WebSocket import YKTWebSocket
from api.courses import CourseAPI
from api.userinfo import UserAPI
from parser.task_parser import TaskParser
from utils.logger import get_logger, set_global_log_level
from utils.helpers import ensure_directory, load_cookie, choose_cookie_with_username
from utils.select import parse_course_selection
from config import config


class YuKeTangApp:
    """
    雨课堂应用主类
    """
    def __init__(self, log_level=None, log_file=None):
        # 先选择 Cookie 文件
        self.selected_cookie_path = choose_cookie_with_username()
        
        # 如果没有指定日志文件，则使用 cookie 文件名生成
        if log_file is None:
            # 获取 cookie 文件名（不含路径和扩展名）
            cookie_filename = os.path.basename(self.selected_cookie_path)
            cookie_name = os.path.splitext(cookie_filename)[0]
            # 生成日志文件名：logs/{cookie_name}_app.log
            log_file = os.path.join(config.DEFAULT_LOG_DIR, f"{cookie_name}_app.log")
            # 确保日志目录存在
            ensure_directory(config.DEFAULT_LOG_DIR)
            print(f"日志文件将保存到: {log_file}")
        
        # 日志级别映射
        if log_level is None:
            log_level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
            log_level = log_level_map.get(config.DEFAULT_LOG_LEVEL, 20)

        # 设置全局日志
        set_global_log_level(log_level)
        self.logger = get_logger(__name__, log_file)
        self.log_file = log_file  # 存储日志文件路径，供其他组件使用
        self.logger.success("应用初始化完成")
        
        # 加载 cookie 数据
        cookie_data = load_cookie(self.selected_cookie_path)
        self.logger.info(f"已选择: {self.selected_cookie_path}")

        self.cookie_str = cookie_data  # cookie 内容，用于 API 和 WS

        # 初始化 API 客户端
        self.user_api = UserAPI(cookie=cookie_data)
        self.course_api = CourseAPI(cookie=cookie_data)

        # 初始化任务解析器时传入 cookie_str
        self.task_parser = TaskParser(
            course_api=self.course_api,
            user_api=self.user_api,
            log_file=self.log_file,
            cookie_file=self.selected_cookie_path,
            cookie_str=self.cookie_str
        )

        # 初始化数据变量
        self.user_info = None
        self.course_list = None
        self.selected_course = None
        self.learn_log = None
        self.tasks = None

        self.logger.info(f"{config.APP_NAME} v{config.APP_VERSION} 启动")

    def fetch_user_info(self) -> bool:
        try:
            self.user_info = self.user_api.fetch_user_info()
            if not self.user_info:
                self.logger.error("获取用户信息失败")
                return False

            user_list = self.user_info.get("data", [])
            if isinstance(user_list, list) and len(user_list) > 0:
                username = user_list[0].get("name", "未知用户")
                user_id = user_list[0].get("user_id", "未知ID")
                self.logger.info(f"当前用户: {username} (ID: {user_id})")

                # 更新窗口标题为用户名
                try:
                    os.system(f"title YuKeTang - 用户: {username}")
                except Exception:
                    pass

                return True
            else:
                self.logger.error("用户信息格式错误")
                return False
        except Exception as e:
            self.logger.exception(f"获取用户信息时发生错误: {str(e)}")
            return False

    def fetch_course_list(self) -> bool:
        try:
            self.logger.progress("开始获取课程列表...")
            response_data = self.course_api.fetch_course_list()
            if not response_data:
                self.logger.error("课程列表获取失败")
                return False

            raw_data = response_data.get("data", {})
            self.course_list = []

            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    if isinstance(v, list):
                        self.course_list.extend(v)
            elif isinstance(raw_data, list):
                self.course_list = raw_data
            else:
                self.logger.error(f"未知课程列表格式: {type(raw_data).__name__}")
                return False

            self.logger.success(f"共获取到 {len(self.course_list)} 门课程")
            return True
        except Exception as e:
            self.logger.exception(f"获取课程列表时发生错误: {str(e)}")
            return False

    def print_course_list(self) -> None:
        if not self.course_list:
            self.logger.warning("课程列表为空")
            return

        self.logger.success("=== 课程列表 ===")
        for i, course in enumerate(self.course_list, start=1):
            course_info = course.get("course", {})
            course_name = course_info.get("name", "未知课程")
            teacher_info = course.get("teacher", {})
            teacher_name = teacher_info.get("name", "未知教师")
            class_name = course.get("name", "未知班级")
            self.logger.hint(f"{i}. 课程：{course_name}  |  班级：{class_name}  |  教师：{teacher_name}")

    def select_course(self, course_index: Optional[int] = None) -> bool:
        if not self.course_list:
            self.logger.error("课程列表为空")
            return False

        if course_index is None:
            course_index = config.DEFAULT_COURSE_INDEX
        if course_index >= len(self.course_list):
            self.logger.warning(f"索引 {course_index} 超出范围，使用第一个课程")
            course_index = 0
        if course_index < 0 or course_index >= len(self.course_list):
            self.logger.error(f"课程索引无效: {course_index}")
            return False

        self.selected_course = self.course_list[course_index]
        course_name = self.selected_course.get('course_name', self.selected_course.get('name', '未知课程'))
        self.logger.data(f"已选择: {course_name}")
        return True

    def fetch_learn_log(self) -> bool:
        if not self.selected_course:
            self.logger.error("未选择课程")
            return False

        classroom_id = self.selected_course.get("classroom_id")
        if not classroom_id:
            self.logger.error("课程数据中缺少 classroom_id")
            return False

        self.logger.progress(f"获取学习日志 classroom_id={classroom_id}...")
        response = self.course_api.fetch_learn_log(classroom_id, raw_response=True)
        if not response or response.status_code != 200:
            self.logger.error("学习日志接口返回失败")
            return False

        try:
            self.learn_log = response.json()
        except Exception:
            self.logger.exception("解析学习日志 JSON 失败")
            return False

        if "data" not in self.learn_log:
            self.logger.error("学习日志返回数据缺少 data")
            return False

        self.logger.success("学习日志获取成功")
        return True

    def parse_tasks(self) -> bool:
        if not self.learn_log or not self.selected_course:
            self.logger.error("学习日志或课程信息为空")
            return False
        classroom_id = self.selected_course['classroom_id']
        self.tasks = self.task_parser.parse_tasks(self.learn_log, classroom_id)
        self.logger.info("任务解析完成")
        return True

    def print_task_statistics(self) -> None:
        if not self.tasks:
            self.logger.warning("任务列表为空")
            return
        self.logger.info("任务分类统计:")
        for task_type, task_list in self.tasks.items():
            self.logger.info(f"{task_type}: {len(task_list)} 个任务")

    def run(self, save_output: bool = False) -> int:
        try:
            if not self.fetch_user_info():
                return 1
            if not self.fetch_course_list():
                return 1
            self.print_course_list()

            # 用户输入课程序号（支持 1,3,5-7 等格式）
            user_input = input(f"请输入要选择的课程序号 (1-{len(self.course_list)}，可用逗号或短横表示范围): ").strip()
            selected_indexes = parse_course_selection(user_input, len(self.course_list))
            if not selected_indexes:
                self.logger.warning("未选择有效课程，默认选择第一门课程")
                selected_indexes = [0]

            # 循环处理每门选择的课程
            for course_index in selected_indexes:
                if not self.select_course(course_index):
                    self.logger.warning(f"课程索引 {course_index + 1} 无效，跳过")
                    continue

                if not self.fetch_learn_log():
                    self.logger.warning(f"课程 {self.selected_course.get('name', '未知')} 学习日志获取失败，跳过")
                    continue

                if not self.parse_tasks():
                    self.logger.warning(f"课程 {self.selected_course.get('name', '未知')} 任务解析失败，跳过")
                    continue

                self.print_task_statistics()
                # 如果你之前启用了保存任务文件，可以在这里判断是否保存
                if save_output:
                    self.logger.info("已关闭自动保存任务文件，跳过保存")

            self.logger.info("所有选中课程处理完成")
            return 0

        except KeyboardInterrupt:
            self.logger.info("程序已被用户中断")
            return 130
        except Exception as e:
            self.logger.exception(f"运行时发生未捕获错误: {str(e)}")
            return 1


def main():
    app = YuKeTangApp()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
