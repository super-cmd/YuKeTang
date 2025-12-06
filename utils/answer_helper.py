# utils/answer_helper.py
"""
答案处理工具
提供统一的 answer 格式化方法，将各种形式的答案转换为列表，
并根据题型返回可直接提交的答案（选择题返回选项字母，判断题返回 ["true"/"false"]）
"""

from typing import List, Union


def normalize_answer(answer: Union[str, List[str], None]) -> List[str]:
    """
    将各种 answer 格式统一为列表形式
    """
    if not answer:
        return []

    # 如果已经是列表，直接返回
    if isinstance(answer, list):
        return answer

    answer = str(answer).strip()

    # 特殊值判断
    if answer in ["正确", "true"]:
        return ["true"]
    if answer in ["错误", "false"]:
        return ["false"]

    # 常用分隔符
    for sep in [",", "#", "|"]:
        if sep in answer:
            parts = [x.strip() for x in answer.split(sep) if x.strip()]
            # 如果分割后有多个部分，返回分割结果
            if len(parts) > 1:
                return parts

    # 连续字母形式，比如 "ABCD"（必须是纯字母）
    if answer.isalpha() and len(answer) > 1:
        return list(answer)

    # 单个字符或其他文本 - 返回整个字符串作为列表的一个元素
    return [answer]


def get_submit_answer(problem: dict, raw_answer: Union[str, List[str]]) -> List[str]:
    """
    根据题型返回可直接提交的答案列表
    针对单选题/多选题，返回选项字母
    """
    q_type = problem.get("type")

    # 单选题或多选题
    if q_type in [0, 1]:
        options = problem.get("options", [])

        # raw_answer 已经是答案文本（如"重视不够"）
        answer_text = ""
        if isinstance(raw_answer, list):
            answer_text = raw_answer[0] if raw_answer else ""
        else:
            answer_text = str(raw_answer).strip()

        # 在选项中查找匹配的key
        for option in options:
            option_value = option.get("value", "")
            if answer_text == option_value:
                return [option.get("key", "")]

        # 如果没找到，返回空（或原始答案）
        return []

    # 判断题
    elif q_type == 3:
        if isinstance(raw_answer, list):
            return raw_answer[:1]
        else:
            answer = str(raw_answer).strip()
            if answer in ["正确", "true"]:
                return ["true"]
            elif answer in ["错误", "false"]:
                return ["false"]
            else:
                return [answer]

    # 其他题型
    else:
        if isinstance(raw_answer, list):
            return raw_answer
        else:
            return [str(raw_answer)]


if __name__ == "__main__":
    # 测试示例
    test_problems = [
        {"type": 0, "options": {"A": "苹果", "B": "香蕉", "C": "橙子"}},
        {"type": 1, "options": {"A": "红色", "B": "绿色", "C": "蓝色"}},
        {"type": 3},
        {"type": 4},
    ]

    test_answers = [
        "苹果",          # 单选题
        "红色#蓝色",     # 多选题
        "正确",          # 判断题
        "这是答案"       # 简答题
    ]

    for p, a in zip(test_problems, test_answers):
        print(f"题目: {p}")
        print(f"原答案: {a}")
        print(f"提交答案: {get_submit_answer(p, a)}\n")
