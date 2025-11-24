"""
解析器模块

该模块负责解析从API获取的数据，特别是对任务点进行结构化处理和分类

模块内容:
    - TaskParser: 任务点解析器，用于解析学习日志中的任务数据
"""

from .task_parser import TaskParser, parse_tasks, parse_leaf_structure

__all__ = [
    'TaskParser',
    'parse_tasks',
    'parse_leaf_structure'
]

__version__ = '1.0.0'
__author__ = 'YuKeTang App'
__description__ = '雨课堂数据解析模块，提供任务点解析功能'