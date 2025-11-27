import os
import json
import brotli
import zlib
from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)

COOKIE_DIR = "cookies"
COOKIE_MAP_FILE = os.path.join(COOKIE_DIR, "cookie_user_map.json")


def ensure_directory(path: str) -> None:
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(path, exist_ok=True)
        logger.debug(f"确保目录存在: {path}")
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        raise


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """保存数据为 JSON 文件"""
    ensure_directory(os.path.dirname(os.path.abspath(file_path)))
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"数据已成功保存到 {file_path}")
    except Exception as e:
        logger.error(f"保存JSON文件失败: {str(e)}")
        raise


def load_cookie(file_path: str) -> str:
    """读取 Cookie 文件，兼容多种格式"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"未找到 {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # 尝试解析 JSON
    try:
        data = json.loads(content)
        # 新版 dict 格式 {"cookie": "..."}
        if isinstance(data, dict) and "cookie" in data:
            return data["cookie"]
        # dict 或 list
        if isinstance(data, dict):
            return "; ".join(f"{k}={v}" for k, v in data.items())
        if isinstance(data, list):
            cookie_dict = {item["name"]: item["value"] for item in data if "name" in item}
            return "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
    except json.JSONDecodeError:
        pass

    # 文件就是纯字符串
    return content


def smart_decompress(data: bytes) -> str:
    """自动解压 br/gzip/deflate 或直接返回文本"""
    try:
        return brotli.decompress(data).decode("utf-8")
    except:
        pass
    if data[:2] == b"\x1f\x8b":
        try:
            return zlib.decompress(data, 16 + zlib.MAX_WBITS).decode("utf-8")
        except:
            pass
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS).decode("utf-8")
    except:
        pass
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin1", errors="ignore")


def choose_cookie_with_username(cookie_dir: str = COOKIE_DIR) -> str:
    """
    列出 cookie 文件 + 用户名，留空输入新 Cookie 并保存。
    返回选择的 cookie 文件完整路径。
    """
    from api.userinfo import UserAPI  # 延迟导入，避免循环导入

    ensure_directory(cookie_dir)
    # 加载 cookie_user_map
    if os.path.exists(COOKIE_MAP_FILE):
        try:
            with open(COOKIE_MAP_FILE, "r", encoding="utf-8") as f:
                cookie_user_map = json.load(f)
        except:
            cookie_user_map = {}
    else:
        cookie_user_map = {}

    files = [f for f in os.listdir(cookie_dir) if f.endswith(".json") and f != "cookie_user_map.json"]

    # 更新未知用户
    for f in files:
        name = os.path.splitext(f)[0]
        if name not in cookie_user_map or cookie_user_map[name] == "未知用户":
            try:
                cookie_data = load_cookie(os.path.join(cookie_dir, f))
                user_api = UserAPI(cookie=cookie_data)
                user_info = user_api.fetch_user_info()
                username = "未知用户"
                user_list = user_info.get("data", [])
                if user_list and isinstance(user_list, list):
                    username = user_list[0].get("name", "未知用户")
                cookie_user_map[name] = username
            except:
                cookie_user_map[name] = "未知用户"

    save_json(cookie_user_map, COOKIE_MAP_FILE)

    # 显示列表
    if files:
        print("已检测到以下 Cookie 文件：")
        for idx, f in enumerate(files, start=1):
            name = os.path.splitext(f)[0]
            username = cookie_user_map.get(name, "未知用户")
            print(f"{idx}. {name} - 用户: {username}")

    choice = input("请选择序号，或留空输入新的 Cookie: ").strip()
    if not choice:
        cookie_str = input("请输入新的 Cookie 字符串: ").strip()
        file_name = input("请输入保存的文件名（不带后缀）: ").strip()
        file_path = os.path.join(cookie_dir, f"{file_name}.json")
        save_json({"cookie": cookie_str}, file_path)

        # 获取用户名
        try:
            user_api = UserAPI(cookie=cookie_str)
            user_info = user_api.fetch_user_info()
            username = "未知用户"
            user_list = user_info.get("data", [])
            if user_list and isinstance(user_list, list):
                username = user_list[0].get("name", "未知用户")
        except:
            username = "未知用户"

        cookie_user_map[file_name] = username
        save_json(cookie_user_map, COOKIE_MAP_FILE)
        print(f"已保存 Cookie 文件: {file_path}，用户名: {username}")
        return file_path

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(files):
            selected_file = os.path.join(cookie_dir, files[choice_idx])
            print(f"已选择: {selected_file}")
            return selected_file
        else:
            print("选择超出范围，将重新输入")
            return choose_cookie_with_username(cookie_dir)
    except ValueError:
        print("输入无效，将重新输入")
        return choose_cookie_with_username(cookie_dir)
