import os
import json
import brotli
import zlib
from typing import Dict, Union, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def choose_cookie(cookie_dir: str = "cookies") -> str:
    """
    列出指定目录下的所有 cookie 文件，让用户选择一个。

    Args:
        cookie_dir: cookie 文件夹路径（默认根目录下 cookies）

    Returns:
        选择的 cookie 文件完整路径
    """
    import os

    # 确保目录存在
    if not os.path.exists(cookie_dir):
        raise FileNotFoundError(f"{cookie_dir} 文件夹不存在，请先创建并放入 cookie 文件")

    # 列出所有 json 文件
    files = [f for f in os.listdir(cookie_dir) if f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"{cookie_dir} 文件夹下没有找到任何 .json 文件")

    # 打印可选择的 cookie 列表
    print("找到以下 Cookie 文件：")
    for i, f in enumerate(files, start=1):
        print(f"{i}. {f}")

    # 用户选择
    while True:
        try:
            choice = int(input("请选择需要使用的 Cookie (输入数字): ").strip())
            if 1 <= choice <= len(files):
                selected_file = os.path.join(cookie_dir, files[choice - 1])
                print(f"已选择: {selected_file}")
                return selected_file
            else:
                print(f"请输入 1-{len(files)} 的数字")
        except ValueError:
            print("输入无效，请输入数字")


def load_cookie(file_path: str = None) -> str:
    """
    读取 cookie 文件并返回 Cookie 字符串
    
    Args:
        file_path: cookie文件路径，如果为None则从配置文件中读取
        
    Returns:
        格式化的Cookie字符串
        
    Raises:
        FileNotFoundError: 当cookie文件不存在时
        json.JSONDecodeError: 当JSON解析失败时
        ValueError: 当cookie格式不正确时
    """
    # 如果未指定路径，从配置中获取
    if file_path is None:
        from config import config
        file_path = config.COOKIE_FILE_PATH
    
    if not os.path.exists(file_path):
        logger.error(f"未找到 {file_path}，请放在脚本同目录")
        raise FileNotFoundError(f"未找到 {file_path}，请放在脚本同目录")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 处理不同格式的cookie数据
        if isinstance(data, list):
            # Chrome DevTools导出的格式
            cookie_dict = {item.get("name", ""): item.get("value", "") for item in data if "name" in item}
        elif isinstance(data, dict):
            # 直接的键值对格式
            cookie_dict = data
        else:
            raise ValueError("Cookie文件格式不正确，应为字典或字典列表")

        # 过滤无效的cookie项
        valid_cookies = [(k, v) for k, v in cookie_dict.items() if k and v]
        if not valid_cookies:
            raise ValueError("Cookie文件中没有有效的cookie数据")

        return "; ".join([f"{k}={v}" for k, v in valid_cookies])
    
    except json.JSONDecodeError as e:
        logger.error(f"Cookie文件JSON解析失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"加载Cookie失败: {str(e)}")
        raise


def smart_decompress(data: bytes) -> str:
    """
    自动解压 br/gzip/deflate 压缩的数据或直接返回文本
    
    Args:
        data: 待解压的字节数据
        
    Returns:
        解压后的文本字符串
    """
    # 首先尝试brotli解压
    try:
        result = brotli.decompress(data).decode("utf-8")
        logger.debug("使用brotli成功解压数据")
        return result
    except (brotli.error, UnicodeDecodeError):
        pass

    # 尝试gzip解压 (gzip文件以\x1f\x8b开头)
    if data[:2] == b"\x1f\x8b":
        try:
            result = zlib.decompress(data, 16 + zlib.MAX_WBITS).decode("utf-8")
            logger.debug("使用gzip成功解压数据")
            return result
        except (zlib.error, UnicodeDecodeError):
            pass

    # 尝试deflate解压
    try:
        result = zlib.decompress(data, -zlib.MAX_WBITS).decode("utf-8")
        logger.debug("使用deflate成功解压数据")
        return result
    except (zlib.error, UnicodeDecodeError):
        pass

    # 尝试直接解码为UTF-8
    try:
        result = data.decode("utf-8")
        logger.debug("数据无需解压，直接解码为UTF-8")
        return result
    except UnicodeDecodeError:
        # 最后尝试latin1解码（可解码任何字节序列但可能产生乱码）
        logger.warning("无法使用标准编码解码数据，尝试使用latin1")
        return data.decode("latin1", errors="ignore")


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 保存路径
        indent: 缩进空格数
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        
        logger.info(f"数据已成功保存到 {file_path}")
    except Exception as e:
        logger.error(f"保存JSON文件失败: {str(e)}")
        raise


def ensure_directory(path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.debug(f"确保目录存在: {path}")
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        raise
