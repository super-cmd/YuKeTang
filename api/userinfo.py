from utils.logger import get_logger
from utils.request_helper import make_request

logger = get_logger(__name__)


class UserAPI:
    """用户相关API操作类"""

    def __init__(self, cookie: str):
        """初始化用户API类，设置配置信息"""
        self.cookie = cookie

    def fetch_user_info(self):
        logger.info("正在获取用户信息...")
        url = "/v2/api/web/userinfo"
        data = make_request(url, cookie=self.cookie, endpoint="获取用户信息")
        if data:
            user_list = data.get("data", [])
            if isinstance(user_list, list) and user_list:
                first_user = user_list[0]
                logger.info(
                    f"登录成功: 用户ID: {first_user.get('user_id')}, 用户名: {first_user.get('name')}"
                )
                return data
            else:
                logger.error("用户信息为空或格式错误")
        return None

    def fetch_user_id(self, classroom_id, cid):
        url = f"/v2/api/web/topic_robot_config/{cid}/{classroom_id}"
        data = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取 topic_robot_config 用户ID classroom_id={classroom_id} cid={cid}"
        )
        user_id = data.get("data", {}).get("user_id") if data else None
        if user_id:
            logger.info(f"成功获取用户ID: {user_id}")
            return str(user_id)
        logger.warning("未获取到用户ID")
        return None

    def fetch_entity_agents(self, entity_id):
        """获取课件资源并提取 login_user_id"""
        logger.info(f"正在获取课件资源 entity_id={entity_id}")
        url = (
            "/c27/online_courseware/agent/entity_agents/"
            f"?entity_type=1&entity_id={entity_id}&category=1&has_role=1"
        )
        extra_headers = {"Xt-Agent": "web", "Xtbz": "ykt"}
        data = make_request(
            url,
            cookie=self.cookie,
            endpoint=f"获取课件资源 entity_id={entity_id}",
            extra_headers=extra_headers
        )

        if not data:
            logger.warning(f"获取课件资源失败: entity_id={entity_id}")
            return None

        login_user_id = data.get("data", {}).get("login_user_id")
        logger.info(f"获取 login_user_id: {login_user_id}")
        return login_user_id
