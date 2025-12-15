import requests
from typing import List, Union, Dict, Any, Optional
import re

from utils.logger import get_logger

logger = get_logger(__name__)


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


def query_question_bank(question_data: Dict[str, Any], authorization: str = "3d749979-90d1-4751-a10a-8c4e755aed1a") -> Optional[str]:
    """
    向题库后端查询题目答案
    
    Args:
        question_data: 包含题目信息的字典，应包含value和type字段，可选options字段
        authorization: 题库接口认证token
        
    Returns:
        题目答案，如果查询失败则返回None
    """
    headers = {
        "Authorization": authorization
    }
    
    try:
        logger.progress(f"正在发送数据到题库后端: \n\n\n{question_data}\n\n\n")
        res = requests.post("https://frpclient04.xhyonline.com:9310/api/questions/search", 
                           json=question_data, headers=headers)
        response_data = res.json()
        raw_answer = response_data.get("data", {}).get("answer") if response_data.get("data") else None
        return raw_answer
    except Exception as e:
        logger.error(f"获取题库答案失败: {str(e)}")
        return None


def prepare_question_data(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    准备发送给题库的数据
    
    Args:
        problem: 包含题目信息的字典
        
    Returns:
        准备好的题库请求数据
    """
    # 构造发送给题库的数据
    question_data = {
        "value": problem.get("value", ""),
        "type": problem.get("type", 0)
    }
    
    # 处理选项数据 - 只对选择题处理选项
    q_type = problem.get("type", 0)
    # 如果是单选题或多选题，但没有选项，则认为是简答题
    problem_options = problem.get("options", [])
    if q_type in [0, 1] and (not problem_options or len(problem_options) == 0):
        # 当单选题/多选题没有选项时，认为是简答题
        question_data["type"] = 4  # 简答题
    elif q_type in [0, 1]:  # 只有单选题和多选题才需要选项
        options = {}
        if isinstance(problem_options, list):
            # 如果选项是列表形式 [{key: "A", value: "选项A"}, ...]
            for opt in problem_options:
                options[opt.get("key")] = opt.get("value")
        elif isinstance(problem_options, dict):
            # 如果选项已经是字典形式 {"A": "选项内容", ...}
            options = problem_options
        
        question_data["options"] = options
        
    return question_data