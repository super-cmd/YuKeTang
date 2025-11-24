"""
API模块

该模块包含与雨课堂平台API交互的类和函数

模块内容:
    - CourseAPI: 课程相关API，用于获取课程列表、学习日志等
    - UserAPI: 用户信息API，用于获取当前用户信息
"""

from .courses import CourseAPI, fetch_course_list, fetch_learn_log, fetch_leaf_list
from .userinfo import UserAPI, fetch_user_info

__all__ = [
    'CourseAPI',
    'fetch_course_list', 
    'fetch_learn_log', 
    'fetch_leaf_list',
    'UserAPI',
    'fetch_user_info'
]

__version__ = '1.0.0'
__author__ = 'YuKeTang App'
__description__ = '雨课堂API模块，提供课程和用户信息访问功能'