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
    支持多种答案格式
    """
    q_type = problem.get("type")
    options = problem.get("options", [])

    # 处理 raw_answer
    if isinstance(raw_answer, list):
        answer_items = raw_answer
    else:
        answer_str = str(raw_answer).strip()

        # 1. 多选题：用逗号分割 "A,B,C,D" -> ["A","B","C","D"]
        if "," in answer_str:
            answer_items = [item.strip() for item in answer_str.split(",") if item.strip()]
        # 2. 连续字母 "ABCD" -> ["A","B","C","D"]
        elif answer_str.isalpha() and len(answer_str) > 1:
            answer_items = list(answer_str)
        # 3. 单个答案
        else:
            answer_items = [answer_str]

    # 单选题 (type=0)
    if q_type == 0:
        if not answer_items:
            return []

        answer_text = answer_items[0]

        # 情况1：已经是字母
        if len(answer_text) == 1 and answer_text in ["A", "B", "C", "D", "E", "F"]:
            return [answer_text]

        # 情况2：匹配选项内容
        for option in options:
            option_value = option.get("value", "")
            # 完全匹配
            if answer_text == option_value:
                return [option.get("key", "")]
            # 去掉空格等符号后匹配（如 "HouseofCommons" 匹配 "House of Commons"）
            clean_answer = answer_text.replace(" ", "").lower()
            clean_option = option_value.replace(" ", "").lower()
            if clean_answer == clean_option:
                return [option.get("key", "")]

        return []

    # 多选题 (type=1)
    elif q_type == 1:
        submit_answers = []

        for answer_item in answer_items:
            # 如果已经是字母
            if len(answer_item) == 1 and answer_item in ["A", "B", "C", "D", "E", "F"]:
                submit_answers.append(answer_item)
                continue

            # 查找匹配的选项
            for option in options:
                option_value = option.get("value", "")
                # 完全匹配
                if answer_item == option_value:
                    submit_answers.append(option.get("key", ""))
                    break
                # 模糊匹配
                clean_answer = answer_item.replace(" ", "").lower()
                clean_option = option_value.replace(" ", "").lower()
                if clean_answer == clean_option:
                    submit_answers.append(option.get("key", ""))
                    break

        return submit_answers

    # 判断题 (type=3)
    elif q_type == 3:
        if not answer_items:
            return []

        answer_text = answer_items[0]
        if answer_text in ["正确", "true"]:
            return ["true"]
        elif answer_text in ["错误", "false"]:
            return ["false"]
        else:
            return [answer_text]

    # 其他题型
    else:
        return answer_items


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
