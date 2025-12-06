# utils/request_helper.py
import json
import random
import time
import requests
from .logger import get_logger
from .helpers import smart_decompress
from .headers import random_headers
from config import config

logger = get_logger(__name__)

def make_request(
    url: str,
    cookie: str = None,
    endpoint: str = "",
    extra_headers: dict = None,
    method: str = "GET",
    json_data: dict = None,
    timeout: float = None,
    request_delay: float = None
):
    """
    通用请求方法，支持 GET / POST

    参数:
        url: 完整URL或相对于 base_url 的路径
        cookie: 可选 cookie
        endpoint: 请求描述，用于日志
        extra_headers: dict，临时 header
        method: "GET" 或 "POST"
        json_data: POST 请求时的 JSON 数据
        timeout: 请求超时时间
        request_delay: 请求前等待时间

    返回:
        dict: JSON 解析结果
    """
    if not timeout:
        timeout = config.API_TIMEOUT
    if request_delay is None:
        request_delay = random.uniform(5.0, 10.0)

    full_url = url if url.startswith("http") else f"{config.API_BASE_URL}{url}"
    headers = random_headers(cookie)
    if extra_headers:
        headers.update(extra_headers)

    try:
        if request_delay > 0:
            logger.info(f"请求前等待 {request_delay:.2f} 秒: {endpoint or full_url}")
            time.sleep(request_delay)

        if method.upper() == "GET":
            res = requests.get(full_url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            res = requests.post(full_url, headers=headers, json=json_data, timeout=timeout)
        else:
            raise ValueError(f"不支持的请求方法: {method}")

        # 尝试解析内容，无论 HTTP 状态码
        text = smart_decompress(res.content)
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = text  # 返回原始内容

        # 检查 HTTP 状态码，如果不是 2xx 打日志但仍返回内容
        if not res.ok:
            status_code = res.status_code
            logger.warning(f"{endpoint} 返回非成功状态码 {status_code}, 内容: {result}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"{endpoint} 请求发生错误: {str(e)}")
        return None
