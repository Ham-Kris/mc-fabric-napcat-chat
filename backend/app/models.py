from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class McMessage(BaseModel):
    """来自 Minecraft 的消息"""
    type: Literal["player_chat", "system", "player_join", "player_leave", "death", "achievement"]
    player: Optional[str] = None
    message: Optional[str] = None


class QqMessage(BaseModel):
    """发送到 Minecraft 的消息"""
    type: str = "chat"
    nickname: str
    qq: str
    content: str
    description: Optional[str] = None
    face_name: Optional[str] = None


class MessageQueue(BaseModel):
    """消息队列响应"""
    messages: List[QqMessage]


class SendResponse(BaseModel):
    """发送响应"""
    success: bool
    message: str


class HealthCheck(BaseModel):
    """健康检查"""
    status: str
    napcat_connected: bool
    timestamp: datetime


class PlayerListUpdate(BaseModel):
    """玩家列表更新"""
    players: List[str]
    max_players: int = 20

