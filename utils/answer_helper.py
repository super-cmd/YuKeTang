from typing import List, Union, Dict
import re


def get_submit_answer(problem: dict, raw_answer: Union[str, List[str]]) -> Union[List[str], Dict[int, str]]:
    """
    根据题型返回可直接提交的答案
    - 单选/多选/判断: 返回列表 ["A"] 或 ["true"]
    - 填空题: 返回字典 {1: "答案1", 2: "答案2"}
    - 简答题: 返回列表 ["答案文本"]
    """

    # 强制转换题型为 int
    try:
        q_type = int(problem.get("type"))
    except:
        q_type = problem.get("type")

    options = problem.get("options", [])

    # 处理 raw_answer 标准化为列表或字符串
    if isinstance(raw_answer, list):
        answer_items = raw_answer
    else:
        answer_items = [str(raw_answer).strip()]

    answer_text = answer_items[0]

    # ========================= 判断题 (type=3) =========================
    if q_type == 3:
        if answer_text in ["正确", "对", "是", "true", "True", "TRUE"]:
            return ["true"]
        if answer_text in ["错误", "错", "否", "false", "False", "FALSE"]:
            return ["false"]

        # 模糊匹配 options
        for opt in options:
            clean_in = answer_text.replace(" ", "").lower()
            clean_opt = opt.get("value", "").replace(" ", "").lower()
            if clean_in in clean_opt:
                return [opt.get("key", "")]
        return [answer_text]

    # ========================= 单选题 (type=0) =========================
    if q_type == 0:
        # 字母选项直接返回
        if len(answer_text) == 1 and answer_text.upper() in "ABCDEF":
            return [answer_text.upper()]

        # 文本匹配 options
        for opt in options:
            ov = opt.get("value", "")
            if answer_text == ov or answer_text.replace(" ", "").lower() == ov.replace(" ", "").lower():
                return [opt.get("key", "")]
        return []

    # ========================= 多选题 (type=1) =========================
    if q_type == 1:
        # 支持 "A,B,C" / "ABC" / ["A","B"]
        if "," in answer_text:
            answer_items = [x.strip() for x in answer_text.split(",") if x.strip()]
        elif answer_text.isalpha() and len(answer_text) > 1:
            answer_items = list(answer_text)

        submit_answers = []
        for item in answer_items:
            # 字母
            if len(item) == 1 and item.upper() in "ABCDEF":
                submit_answers.append(item.upper())
                continue

            # 文本匹配 options
            for opt in options:
                ov = opt.get("value", "")
                if item == ov or item.replace(" ", "").lower() == ov.replace(" ", "").lower():
                    submit_answers.append(opt.get("key", ""))
                    break
        return submit_answers

    # ========================= 填空题 (type=2) =========================
    if q_type == 2:
        # 支持 "答案1|答案2" 或 "答案1,答案2"
        if isinstance(raw_answer, str):
            split_answers = [a.strip() for a in re.split(r'\||,', raw_answer) if a.strip()]
        else:
            split_answers = raw_answer
        return {i + 1: v for i, v in enumerate(split_answers)}

    # ========================= 简答题/其他 (type=4 或默认) =========================
    return answer_items
