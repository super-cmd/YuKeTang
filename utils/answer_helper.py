from typing import List, Union


def get_submit_answer(problem: dict, raw_answer: Union[str, List[str]]) -> List[str]:
    """
    根据题型返回可直接提交的答案列表
    """

    # 强制转换为 int —— ★ 最重要修复点 ★
    try:
        q_type = int(problem.get("type"))
    except:
        q_type = problem.get("type")

    options = problem.get("options", [])

    # 处理 raw_answer 标准化为列表
    if isinstance(raw_answer, list):
        answer_items = raw_answer
    else:
        answer_items = [str(raw_answer).strip()]

    answer_text = answer_items[0]

    # 判断题 (type = 3)
    if q_type == 3:

        # 常规匹配
        if answer_text in ["正确", "对", "是", "true", "True", "TRUE"]:
            return ["true"]

        if answer_text in ["错误", "错", "否", "false", "False", "FALSE"]:
            return ["false"]

        # 模糊匹配 options
        for opt in options:
            clean_in = answer_text.replace(" ", "").lower()
            clean_opt = opt["value"].replace(" ", "").lower()

            if clean_in in clean_opt:
                return [opt["key"]]

        # fallback：返回原文
        return [answer_text]

    # 单选题 (type = 0)
    if q_type == 0:

        # 字母项直接返回
        if len(answer_text) == 1 and answer_text.upper() in "ABCDEF":
            return [answer_text.upper()]

        # 匹配选项内容
        for opt in options:
            ov = opt.get("value", "")

            if answer_text == ov:
                return [opt.get("key", "")]

            # 模糊匹配
            if answer_text.replace(" ", "").lower() == ov.replace(" ", "").lower():
                return [opt.get("key", "")]

        return []

    # 多选题 (type = 1)
    if q_type == 1:
        # 支持： "A,B,C" / "ABC" / ["A","B"]
        if "," in answer_text:
            answer_items = [x.strip() for x in answer_text.split(",") if x.strip()]

        elif answer_text.isalpha() and len(answer_text) > 1:
            answer_items = list(answer_text)

        submit_answers = []

        for item in answer_items:
            # A/B/C 字母
            if len(item) == 1 and item.upper() in "ABCDEF":
                submit_answers.append(item.upper())
                continue

            # 文本匹配 options
            for opt in options:
                ov = opt.get("value", "")

                if item == ov:
                    submit_answers.append(opt.get("key", ""))
                    break

                # 模糊匹配
                if item.replace(" ", "").lower() == ov.replace(" ", "").lower():
                    submit_answers.append(opt.get("key", ""))
                    break

        return submit_answers

    # 填空题 / 简答题 / 其他
    return answer_items
