import asyncio
import json
import logging
from typing import Optional, Callable, Awaitable
import websockets
from websockets.client import WebSocketClientProtocol

from app.config import settings

logger = logging.getLogger(__name__)


class NapCatClient:
    """NapCat WebSocket 客户端"""

    def __init__(self):
        self.ws: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self._message_handler: Optional[Callable[[dict], Awaitable[None]]] = None
        self._echo_counter = 0
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._reconnect_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

    def set_message_handler(self, handler: Callable[[dict], Awaitable[None]]):
        """设置消息处理回调"""
        self._message_handler = handler

    async def connect(self):
        """连接到 NapCat WebSocket"""
        while True:
            try:
                url = settings.napcat_ws_url
                headers = {}
                if settings.napcat_access_token:
                    headers["Authorization"] = f"Bearer {settings.napcat_access_token}"

                logger.info(f"Connecting to NapCat: {url}")
                self.ws = await websockets.connect(url, additional_headers=headers)
                self.connected = True
                logger.info("Connected to NapCat successfully!")

                # 启动接收任务
                self._receive_task = asyncio.create_task(self._receive_loop())
                await self._receive_task

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"NapCat connection closed: {e}")
                self.connected = False
            except Exception as e:
                logger.error(f"NapCat connection error: {e}")
                self.connected = False

            # 重连延迟
            logger.info("Reconnecting to NapCat in 5 seconds...")
            await asyncio.sleep(5)

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False

    async def _handle_message(self, data: dict):
        """处理收到的消息"""
        # 处理 API 响应
        if "echo" in data:
            echo = data["echo"]
            if echo in self._pending_requests:
                self._pending_requests[echo].set_result(data)
                return

        # 处理事件
        post_type = data.get("post_type")
        if post_type == "message" and self._message_handler:
            await self._message_handler(data)
        elif post_type == "meta_event":
            logger.debug(f"Meta event: {data.get('meta_event_type')}")

    async def call_api(self, action: str, params: dict = None, timeout: float = 10.0) -> dict:
        """调用 NapCat API"""
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to NapCat")

        self._echo_counter += 1
        echo = f"mc_qq_{self._echo_counter}"

        request = {
            "action": action,
            "params": params or {},
            "echo": echo
        }

        future = asyncio.get_event_loop().create_future()
        self._pending_requests[echo] = future

        try:
            await self.ws.send(json.dumps(request))
            result = await asyncio.wait_for(future, timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"API call timeout: {action}")
            raise
        finally:
            self._pending_requests.pop(echo, None)

    async def send_group_message(self, group_id: int, message: str) -> dict:
        """发送群消息"""
        return await self.call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })

    async def send_group_message_cq(self, group_id: int, message_segments: list) -> dict:
        """发送群消息（CQ码格式）"""
        return await self.call_api("send_group_msg", {
            "group_id": group_id,
            "message": message_segments
        })

    async def get_group_member_info(self, group_id: int, user_id: int) -> dict:
        """获取群成员信息"""
        return await self.call_api("get_group_member_info", {
            "group_id": group_id,
            "user_id": user_id
        })

    async def get_stranger_info(self, user_id: int) -> dict:
        """获取陌生人信息"""
        return await self.call_api("get_stranger_info", {
            "user_id": user_id
        })

    async def close(self):
        """关闭连接"""
        self.connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()
        logger.info("NapCat client closed")


# 全局客户端实例
napcat_client = NapCatClient()

