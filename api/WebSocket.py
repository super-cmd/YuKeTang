import websocket
import threading
import json
import ssl
import time
import random
from utils.logger import get_logger

class YKTWebSocket:
    """
    雨课堂 WebSocket 客户端（修正版）
    支持：
    - Cookie 授权
    - 自动心跳
    - 模拟课件观看（每页停留 1~2 秒）
    - finished 属性，用于判断观看是否完成
    """

    def __init__(self, cookie: str, classroom_id: int, user_id: int = None,
                 cards_id: int = None, page_count: int = None, log_file=None, network_log_file=None):
        self.cookie = cookie
        self.classroom_id = classroom_id
        self.user_id = user_id
        self.cards_id = cards_id
        self.page_count = page_count
        self.ws = None
        self.connected = False
        self.finished = False
        self.heartbeat_interval = 30
        self.view_thread = None
        self.logger = get_logger(__name__, log_file, network_log_file=network_log_file)
        self.network_log_file = network_log_file

    # ================= WebSocket 回调 =================
    def on_open(self, ws):
        self.connected = True
        self.logger.debug("[WebSocket] 连接成功")

        # 授权
        auth_msg = {"op": "authorize", "classroom_id": self.classroom_id}
        ws.send(json.dumps(auth_msg))
        self.logger.debug("[WebSocket] 已发送 authorize 消息")

        # 启动心跳线程
        threading.Thread(target=self._heartbeat, daemon=True).start()

        # 等待 cards_id / user_id / page_count 就绪再模拟观看
        if self.cards_id is None or self.user_id is None or self.page_count is None:
            self.logger.warning("[WebSocket] cards_id/user_id/page_count 未设置，稍后重试模拟观看")
            def delayed_view():
                while self.cards_id is None or self.user_id is None or self.page_count is None:
                    time.sleep(0.1)
                self._simulate_course_view_thread()
            threading.Thread(target=delayed_view, daemon=True).start()
        else:
            self.view_thread = threading.Thread(
                target=self._simulate_course_view_thread,
                daemon=True
            )
            self.view_thread.start()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.logger.debug(f"[WebSocket] 收到消息: {json.dumps(data, ensure_ascii=False)}")
        except Exception:
            self.logger.debug(f"[WebSocket] 收到非 JSON 消息: {message}")

    def on_error(self, ws, error):
        self.logger.error(f"[WebSocket] 错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        self.logger.debug(f"[WebSocket] 连接关闭: {close_status_code} {close_msg}")
        if not self.finished:
            self.logger.info("[WebSocket] 未完成，尝试重连...")
            time.sleep(3)
            self.run()

    # ================= 心跳 =================
    def _heartbeat(self):
        while self.connected:
            try:
                msg = {"op": "heartbeat"}
                self.ws.send(json.dumps(msg))
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"[WebSocket] 心跳失败: {e}")
                break

    # ================= 发送消息 =================
    def send_ws(self, data: dict):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                self.logger.error(f"[WebSocket] 发送失败: {e}")

    # ================= 模拟观看 =================
    def _simulate_course_view_thread(self):
        self.logger.info(f"课件 {self.cards_id} 模拟观看中...")
        try:
            data_progress = [0.0] * self.page_count
            for i in range(self.page_count):
                stay_time = round(random.uniform(1, 2), 1)
                data_progress[i] = stay_time

                payload = {
                    "op": "view_record",
                    "cardsID": self.cards_id,
                    "start_time": int(time.time()),
                    "data": data_progress.copy(),
                    "user_id": self.user_id,
                    "platform": "web",
                    "type": "cache"
                }

                self.send_ws(payload)
                self.logger.info(f"[WebSocket] 已发送页 {i + 1}/{self.page_count} -> {stay_time:.1f}s")
                time.sleep(stay_time)

            self.logger.info(f"课件 {self.cards_id} 模拟观看完成")
        except Exception as e:
            self.logger.error(f"[WebSocket] 模拟观看异常: {e}")
        finally:
            self.finished = True

    # ================= 启动连接 =================
    def run(self):
        headers = [
            f"Cookie: {self.cookie}",
            "Origin: https://www.yuketang.cn",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36"
        ]

        self.ws = websocket.WebSocketApp(
            "wss://www.yuketang.cn/ws/",
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        threading.Thread(
            target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}),
            daemon=True
        ).start()
        self.logger.debug("[WebSocket] 正在连接雨课堂...")
