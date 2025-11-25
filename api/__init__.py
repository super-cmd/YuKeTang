"""
API模块

该模块包含与雨课堂平台API交互的类和函数
"""

from .courses import CourseAPI
from .userinfo import UserAPI

__all__ = [
    'CourseAPI',
    'UserAPI',
]

__version__ = '1.0.0'
__author__ = 'YuKeTang App'
__description__ = '雨课堂API模块，提供课程和用户信息访问功能'
