import random
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# 更多样化的User-Agent列表，包含不同浏览器和操作系统
USER_AGENTS: List[str] = [
    # Chrome 浏览器
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    
    # Firefox 浏览器
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:125.0) Gecko/20100101 Firefox/125.0",
    
    # Safari 浏览器
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    
    # Edge 浏览器
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    
    # Android 设备
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"
]


def random_headers(cookie: str, referer: str = "https://www.yuketang.cn/v2/web/index") -> Dict[str, str]:
    """
    生成随机的HTTP请求头，包含随机的User-Agent
    
    Args:
        cookie: 用户cookie字符串
        referer: 请求来源页面
        
    Returns:
        包含必要HTTP头的字典
    """
    user_agent = random.choice(USER_AGENTS)
    logger.debug(f"使用随机User-Agent: {user_agent[:50]}...")
    
    return {
        "xt-agent": "web",
        "referer": referer,
        "user-agent": user_agent,
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "connection": "keep-alive",
        "origin": "https://www.yuketang.cn",
        "cookie": cookie
    }


def create_custom_headers(cookie: str, **kwargs) -> Dict[str, str]:
    """
    创建自定义的HTTP请求头，允许覆盖默认值
    
    Args:
        cookie: 用户cookie字符串
        **kwargs: 要覆盖的自定义头部
        
    Returns:
        包含指定HTTP头的字典
    """
    headers = random_headers(cookie)
    # 覆盖自定义头部
    for key, value in kwargs.items():
        headers[key] = value
    
    return headers
