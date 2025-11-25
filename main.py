# main.py
import json
import sys
import argparse
from typing import Dict, Any, Optional
from api.courses import CourseAPI
from api.userinfo import UserAPI
from parser.task_parser import TaskParser
from utils.logger import get_logger, set_global_log_level
from utils.helpers import ensure_directory
from utils.select import parse_course_selection
from config import config


class YuKeTangApp:
    """
    雨课堂应用主类
    
    用于获取用户信息、课程列表、学习日志和任务点解析的核心应用类
    """
    
    def __init__(self, log_level=None, log_file=None):
        """
        初始化应用
        
        参数:
            log_level: 日志级别，如果为None则使用配置文件中的默认值
            log_file: 日志文件路径，如果为None则使用配置文件中的默认值
        """
        # 获取日志级别，如果没有指定则从配置文件获取
        if log_level is None:
            # 日志级别映射表，将字符串转换为数字
            log_level_map = {
                "DEBUG": 10,
                "INFO": 20,
                "WARNING": 30,
                "ERROR": 40,
                "CRITICAL": 50
            }
            log_level = log_level_map.get(config.DEFAULT_LOG_LEVEL, 20)
        
        # 获取日志文件路径，如果没有指定则使用配置文件中的默认值
        if log_file is None:
            log_file = config.DEFAULT_LOG_FILE
        
        # 设置全局日志级别
        set_global_log_level(log_level)
        
        # 获取带名称的logger
        self.logger = get_logger(__name__, log_file)
        
        # 初始化API客户端和解析器
        self.logger.success("应用初始化完成")
        self.user_api = UserAPI()  # 用户API客户端
        self.course_api = CourseAPI()  # 课程API客户端
        self.task_parser = TaskParser()  # 任务解析器
        
        # 初始化应用数据变量
        self.user_info = None  # 用户信息
        self.course_list = None  # 课程列表
        self.selected_course = None  # 选中的课程
        self.learn_log = None  # 学习日志
        self.tasks = None  # 解析后的任务列表
        
        # 记录应用启动信息
        self.logger.info(f"{config.APP_NAME} v{config.APP_VERSION} 启动")
    
    def fetch_user_info(self) -> bool:
        """
        获取用户信息
        
        Returns:
            bool: 是否获取成功
        """
        try:
            self.user_info = self.user_api.fetch_user_info()
            if not self.user_info:
                self.logger.error("获取用户信息失败")
                return False
            
            # 正确访问嵌套的数据结构
            user_list = self.user_info.get("data", [])
            if isinstance(user_list, list) and len(user_list) > 0:
                username = user_list[0].get("name", "未知用户")
                user_id = user_list[0].get("user_id", "未知ID")
                self.logger.info(f"当前用户: {username} (ID: {user_id})")
                return True
            else:
                self.logger.error("用户信息格式错误，无法获取用户名和ID")
                return False
        except Exception as e:
            self.logger.exception(f"获取用户信息时发生错误: {str(e)}")
            return False
    
    def fetch_course_list(self) -> bool:
        """
        获取课程列表
        
        Returns:
            bool: 是否获取成功
        """
        try:
            self.logger.progress("开始获取课程列表...")
            response_data = self.course_api.fetch_course_list()
            if not response_data:
                self.logger.error("课程列表获取失败，API返回空")
                return False
            
            # 正确提取课程列表数据
            raw_data = response_data.get("data", {})

            self.course_list = []

            # 如果 data 是 dict，则自动从其中提取所有 list
            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    if isinstance(v, list):
                        self.course_list.extend(v)
                    else:
                        self.logger.debug(f"跳过非列表字段: {k} ({type(v).__name__})")

            # 如果 data 本身就是列表（旧接口格式）
            elif isinstance(raw_data, list):
                self.course_list = raw_data

            else:
                self.logger.error(f"未能识别课程列表格式: {type(raw_data).__name__}")
                return False

            self.logger.success(f"共获取到 {len(self.course_list)} 门课程")
            return True

        except Exception as e:
            self.logger.error(f"获取课程列表时发生错误: {str(e)}")
            return False

    def print_course_list(self) -> None:
        if not self.course_list:
            self.logger.warning("课程列表为空")
            return

        self.logger.success("=== 课程列表 ===")

        for i, course in enumerate(self.course_list, start=1):
            if not isinstance(course, dict):
                self.logger.warning(f"{i}. 非字典数据: {type(course).__name__}")
                continue

            # —— 课程名称来自 course.name ——
            course_info = course.get("course", {})
            course_name = course_info.get("name", "未知课程")

            # —— 教师名称来自 teacher.name ——
            teacher_info = course.get("teacher", {})
            teacher_name = teacher_info.get("name", "未知教师")

            # —— 班级名称是当前对象的 name 字段 ——
            class_name = course.get("name", "未知班级")

            self.logger.hint(
                f"{i}. 课程：{course_name}  |  班级：{class_name}  |  教师：{teacher_name}"
            )

    def select_course(self, course_index: Optional[int] = None) -> bool:
        """
        选择课程
        
        Args:
            course_index: 课程索引，如果为None则使用配置文件中的默认索引
            
        Returns:
            bool: 是否选择成功
        """
        if not self.course_list:
            self.logger.error("课程列表为空，请先获取课程列表")
            return False
        
        # 如果没有指定索引，使用配置文件中的默认索引
        if course_index is None:
            course_index = config.DEFAULT_COURSE_INDEX
            
        # 始终检查索引是否在有效范围内
        if course_index >= len(self.course_list):
            self.logger.warning(f"索引 {course_index} 超出范围，自动使用第一个课程索引 0")
            course_index = 0
            
        # 再次检查索引，确保万无一失
        if course_index < 0 or course_index >= len(self.course_list):
            self.logger.error(f"课程索引无效: {course_index}")
            return False
        
        try:
            self.selected_course = self.course_list[course_index]
            
            # 安全地获取课程名称信息
            if isinstance(self.selected_course, dict):
                course_name = self.selected_course.get('course_name',
                                                    self.selected_course.get('name',
                                                                           '未知课程'))
                self.logger.data(f"已选择: {course_name}")
            elif isinstance(self.selected_course, list):
                self.logger.data(f"已选择索引 {course_index} 的课程，数据类型为列表")
            else:
                self.logger.data(f"已选择索引 {course_index} 的课程，数据类型为: {type(self.selected_course).__name__}")
                
            return True
        except Exception as e:
            self.logger.error(f"选择课程时发生错误: {str(e)}")
            return False

    def fetch_learn_log(self) -> bool:
        """
        获取学习日志
        """
        if not self.selected_course:
            self.logger.error("未选择课程，请先选择课程")
            return False

        try:
            # 优先从 dict 获取 classroom_id
            classroom_id = None

            if isinstance(self.selected_course, dict):
                classroom_id = self.selected_course.get('classroom_id')

            # 如果是 list，则遍历查找包含 classroom_id 的字典
            elif isinstance(self.selected_course, list):
                for item in self.selected_course:
                    if isinstance(item, dict) and 'classroom_id' in item:
                        classroom_id = item['classroom_id']
                        self.logger.data(f"从列表中找到 classroom_id: {classroom_id}")
                        break

            if not classroom_id:
                self.logger.error("无法从课程数据中找到 classroom_id")
                return False

            self.logger.progress(f"使用 classroom_id = {classroom_id} 获取学习日志...")

            # --- 请求学习日志 ---
            response = self.course_api.fetch_learn_log(classroom_id, raw_response=True)

            if not response:
                self.logger.error("学习日志接口返回空响应")
                return False

            # 打印状态码
            # self.logger.data(f"[学习日志] HTTP 状态码: {response.status_code}")

            # 打印响应原始文本内容
            # self.logger.data(f"[学习日志] 响应内容: {response.text}")

            # 若不是 200，一定失败
            if response.status_code != 200:
                self.logger.error("学习日志接口返回非 200 状态码，无法继续")
                return False

            # --- 尝试解析 JSON ---
            try:
                response_data = response.json()
            except Exception:
                self.logger.exception("学习日志 JSON 解析失败！")
                return False

            # 打印 JSON 内容
            # self.logger.data(f"[学习日志] JSON 数据: {json.dumps(response_data, ensure_ascii=False)}")

            # --- 判断是否正常 ---
            if "data" not in response_data:
                self.logger.error("学习日志接口未返回 data 字段")
                return False

            self.learn_log = response_data
            self.logger.success("学习日志获取成功")
            return True

        except Exception as e:
            self.logger.exception(f"获取学习日志时发生未捕获错误：{e}")
            return False

    def parse_tasks(self) -> bool:
        """
        解析任务点
        
        Returns:
            bool: 是否解析成功
        """
        if not self.learn_log or not self.selected_course:
            self.logger.error("学习日志或课程信息为空，无法解析任务")
            return False
        
        try:
            classroom_id = self.selected_course['classroom_id']
            # user_id = self.course_api.fetch_user_id_by_classroom(classroom_id)
            self.tasks = self.task_parser.parse_tasks(self.learn_log, classroom_id, 2824639)
            
            self.logger.info("任务解析完成")
            return True
        except Exception as e:
            self.logger.exception(f"解析任务时发生错误: {str(e)}")
            return False
    
    def print_task_statistics(self) -> None:
        """
        打印任务统计信息
        """
        if not self.tasks:
            self.logger.warning("任务列表为空")
            return
        
        self.logger.info("任务分类统计:")
        for task_type, task_list in self.tasks.items():
            self.logger.info(f"{task_type}: {len(task_list)} 个任务")
    
    def save_tasks_to_file(self, output_file: str = None) -> bool:
        """
        保存任务数据到文件
        
        Args:
            output_file: 输出文件路径，如果为None则使用配置文件中的默认值
            
        Returns:
            bool: 是否保存成功
        """
        if not self.tasks:
            self.logger.error("任务列表为空，无法保存")
            return False
        
        # 如果没有指定输出文件，使用配置文件中的默认值
        if output_file is None:
            output_file = config.DEFAULT_TASK_OUTPUT_FILE
        
        try:
            # 确保输出目录存在
            ensure_directory(output_file)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"任务数据已保存到: {output_file}")
            return True
        except Exception as e:
            self.logger.exception(f"保存任务数据时发生错误: {str(e)}")
            return False

    def run(self, course_index: Optional[int] = None, save_output: bool = False,
            output_file: str = "tasks.json") -> int:
        """
        运行应用的完整流程

        Args:
            course_index: 课程索引
            save_output: 是否保存输出
            output_file: 输出文件路径

        Returns:
            int: 退出代码，0表示成功，非0表示失败
        """
        try:
            # 1. 获取用户信息
            if not self.fetch_user_info():
                return 1

            # 2. 获取课程列表
            if not self.fetch_course_list():
                return 1

            # 3. 打印课程列表
            self.print_course_list()

            # 4. 始终让用户手动选择课程（支持多选/范围）
            try:
                self.logger.success(f"请输入要选择的课程序号 (支持 1,3-5 格式，1-{len(self.course_list)}):")
                user_input = input(">>> ").strip()

                selected_indexes = parse_course_selection(user_input, len(self.course_list))

                if not selected_indexes:
                    self.logger.warning("输入无效，默认选择第一个课程")
                    selected_indexes = [0]

                # 目前你只支持单选，所以取第一个
                course_index = selected_indexes[0]

            except Exception as e:
                self.logger.error(f"获取用户输入时发生错误: {str(e)}")
                course_index = 0

            # 5. 选择课程
            if not self.select_course(course_index):
                return 1
            # self.course_api.fetch_video_watch_progress(self.selected_course['classroom_id'], user_id, )

            # 5. 获取学习日志
            if not self.fetch_learn_log():
                return 1

            # 6. 解析任务点
            if not self.parse_tasks():
                return 1

            # 7. 打印任务统计
            self.print_task_statistics()

            # 8. 保存任务数据（如果需要）
            if save_output:
                if not self.save_tasks_to_file(output_file):
                    self.logger.warning("保存任务数据失败，但程序继续运行")

            self.logger.info("程序运行完成")
            return 0

        except KeyboardInterrupt:
            self.logger.info("程序已被用户中断")
            return 130  # SIGINT
        except Exception as e:
            self.logger.exception(f"程序运行时发生未捕获的错误: {str(e)}")
            return 1


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description=f"{config.APP_NAME} - 雨课堂数据获取和解析工具")
    
    # 课程选择参数
    parser.add_argument('-c', '--course', type=int, 
                        default=config.DEFAULT_COURSE_INDEX,
                        help=f"指定要查询的课程索引 (默认: {config.DEFAULT_COURSE_INDEX})")
    
    # 输出参数
    parser.add_argument('-o', '--output', type=str, 
                        default=config.DEFAULT_TASK_OUTPUT_FILE, 
                        help=f"任务数据输出文件路径 (默认: {config.DEFAULT_TASK_OUTPUT_FILE})")
    parser.add_argument('-s', '--save', action="store_true", 
                        default=config.AUTO_SAVE_TASKS,
                        help="保存任务数据到文件")
    
    # 日志参数
    parser.add_argument('--log-level', type=str, 
                        default=config.DEFAULT_LOG_LEVEL, 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help=f"日志级别 (默认: {config.DEFAULT_LOG_LEVEL})")
    parser.add_argument('--log-file', type=str, 
                        default=config.DEFAULT_LOG_FILE,
                        help=f"日志文件路径 (默认: {config.DEFAULT_LOG_FILE})")
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 转换日志级别字符串为logging模块的数字常量
    log_level_map = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    log_level = log_level_map[args.log_level]
    
    # 创建并运行应用
    app = YuKeTangApp(log_level=log_level, log_file=args.log_file)
    exit_code = app.run(
        course_index=args.course,
        save_output=args.save,
        output_file=args.output
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
