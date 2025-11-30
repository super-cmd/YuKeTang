import websocket
import threading
import json
import ssl
import time
import random
from utils.logger import get_logger


class YKTWebSocket:
    """
    雨课堂 WebSocket 客户端（稳定版）
    - 自动关闭
    - 不重连
    - 不产生死线程
    """

    def __init__(self, cookie: str, classroom_id: int, user_id: int = None,
                 cards_id: int = None, page_count: int = None, log_file=None):
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
        self.logger = get_logger(__name__, log_file)

    # ================= WebSocket 回调 =================
    def on_open(self, ws):
        self.connected = True
        self.logger.debug("[WebSocket] 连接成功")

        # 授权
        ws.send(json.dumps({"op": "authorize", "classroom_id": self.classroom_id}))
        self.logger.debug("[WebSocket] 已发送 authorize 消息")

        # 心跳
        threading.Thread(target=self._heartbeat, daemon=True).start()

        # 模拟观看
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
        self.finished = True
        self.connected = False

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        self.logger.info(f"[WebSocket] 连接关闭: {close_status_code} {close_msg}")
        self.finished = True   # 明确告诉主线程：我是真的关闭了

    # ================= 心跳 =================
    def _heartbeat(self):
        while self.connected:
            try:
                self.ws.send(json.dumps({"op": "heartbeat"}))
                time.sleep(self.heartbeat_interval)
            except:
                break

    # ================= 模拟观看 =================
    def _simulate_course_view_thread(self):
        try:
            self.logger.info(f"课件 {self.cards_id} 模拟观看中...")

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

                self.ws.send(json.dumps(payload))
                self.logger.info(f"[WebSocket] 已发送页 {i + 1}/{self.page_count} -> {stay_time}s")
                time.sleep(stay_time)

            self.logger.info(f"课件 {self.cards_id} 模拟观看完成")

        except Exception as e:
            self.logger.error(f"[WebSocket] 模拟观看异常: {e}")

        finally:
            # 自动关闭
            try:
                if self.ws:
                    self.ws.close()
            except:
                pass
            self.finished = True
            self.connected = False

    # ================= 启动连接 =================
    def run(self):
        self.finished = False
        self.connected = False

        headers = [
            f"Cookie: {self.cookie}",
            "Origin: https://www.yuketang.cn",
            "User-Agent: Mozilla/5.0"
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
