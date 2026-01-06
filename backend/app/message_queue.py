import asyncio
import logging
from collections import deque
from typing import Optional
from datetime import datetime

from app.models import QqMessage

logger = logging.getLogger(__name__)


class MessageQueueManager:
    """消息队列管理器 - 用于 MC mod 轮询"""

    def __init__(self, max_size: int = 1000):
        self._queue: deque[QqMessage] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()

    async def push(self, message: QqMessage):
        """添加消息到队列"""
        async with self._lock:
            self._queue.append(message)
            logger.debug(f"Message queued: {message.content[:50]}")

    async def poll(self, max_count: int = 50) -> list[QqMessage]:
        """获取并清空队列中的消息"""
        async with self._lock:
            messages = []
            count = min(len(self._queue), max_count)
            for _ in range(count):
                messages.append(self._queue.popleft())
            return messages

    async def size(self) -> int:
        """获取队列大小"""
        async with self._lock:
            return len(self._queue)


# 全局消息队列
message_queue = MessageQueueManager()

