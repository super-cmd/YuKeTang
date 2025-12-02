# utils/request_helper.py
import json
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
        JSON 解析结果或 None
    """
    if not timeout:
        timeout = config.API_TIMEOUT
    if request_delay is None:
        request_delay = config.API_REQUEST_DELAY

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

        res.raise_for_status()
        text = smart_decompress(res.content)

        if res.headers.get("Content-Type", "").startswith("application/json"):
            return res.json()
        else:
            return json.loads(text)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "未知"
        logger.error(f"{endpoint} 请求失败: HTTP错误 {status_code}")
        return None
    except json.JSONDecodeError:
        logger.error(f"{endpoint} 返回的数据不是有效的 JSON 格式")
        return None
    except Exception as e:
        logger.error(f"{endpoint} 请求发生错误: {str(e)}")
        return None
