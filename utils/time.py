from typing import Optional, Union
import datetime
import time


def to_datetime(ts: Optional[int] = None) -> Optional[str]:
    """
    将毫秒时间戳转换为可读的日期时间字符串
    
    Args:
        ts: 毫秒时间戳，如果为None或0则返回None
        
    Returns:
        格式化的日期时间字符串，格式为 '%Y-%m-%d %H:%M:%S'
    """
    if not ts:
        return ""
    try:
        return datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ""


def get_current_timestamp(milliseconds: bool = True) -> Union[int, float]:
    """
    获取当前时间戳
    
    Args:
        milliseconds: 是否返回毫秒级时间戳
        
    Returns:
        时间戳，毫秒级或秒级
    """
    if milliseconds:
        return int(time.time() * 1000)
    return time.time()


def format_time_duration(seconds: Union[int, float]) -> str:
    """
    格式化时间持续时间为可读格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串，如 "2小时30分钟15秒"
    """
    if seconds < 0:
        return "0秒"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or not parts:
        parts.append(f"{secs}秒")
    
    return "".join(parts)


def parse_datetime_string(date_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime.datetime]:
    """
    将字符串解析为datetime对象
    
    Args:
        date_str: 日期时间字符串
        fmt: 字符串格式
        
    Returns:
        datetime对象，如果解析失败返回None
    """
    try:
        return datetime.datetime.strptime(date_str, fmt)
    except ValueError:
        return None


def get_time_difference(start_time: Union[int, float], end_time: Union[int, float], 
                        milliseconds: bool = True) -> Union[int, float]:
    """
    计算两个时间戳之间的差值
    
    Args:
        start_time: 开始时间戳
        end_time: 结束时间戳
        milliseconds: 是否为毫秒级时间戳
        
    Returns:
        时间差值
    """
    if milliseconds:
        return end_time - start_time
    return end_time - start_time
