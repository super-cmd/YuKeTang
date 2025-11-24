def parse_course_selection(input_str: str, max_index: int) -> list:
    """
    解析用户输入的课程选择字符串，支持格式：
    - "5"
    - "2-6"
    - "1,3,5"
    - "1,3-6,8"

    返回0-based索引列表
    """
    if not input_str:
        return []

    result = set()
    parts = input_str.split(",")

    for part in parts:
        part = part.strip()

        # 1. 单个数字
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < max_index:
                result.add(idx)
            continue

        # 2. 范围格式 x-y
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                if start_str.isdigit() and end_str.isdigit():
                    start = int(start_str) - 1
                    end = int(end_str) - 1

                    if start > end:
                        start, end = end, start  # 自动矫正 x-y 或 y-x

                    for i in range(start, end + 1):
                        if 0 <= i < max_index:
                            result.add(i)
            except:
                continue

    return sorted(result)
