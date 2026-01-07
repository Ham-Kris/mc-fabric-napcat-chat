import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.config import settings
from app.models import McMessage, MessageQueue, SendResponse, HealthCheck, QqMessage, PlayerListUpdate
from app.message_queue import message_queue
from app.message_handler import message_handler
from app.napcat_client import napcat_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


async def verify_token(authorization: Optional[str] = Header(None)):
    """验证 API Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization[7:]
    if token != settings.api_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return token


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """健康检查"""
    return HealthCheck(
        status="ok",
        napcat_connected=napcat_client.connected,
        timestamp=datetime.now()
    )


@router.get("/messages/poll", response_model=MessageQueue, dependencies=[Depends(verify_token)])
async def poll_messages():
    """轮询获取 QQ 消息（供 MC mod 调用）"""
    messages = await message_queue.poll()
    return MessageQueue(messages=messages)


@router.post("/messages/send", response_model=SendResponse, dependencies=[Depends(verify_token)])
async def send_message(msg: McMessage):
    """发送消息到 QQ 群（供 MC mod 调用）"""
    logger.info(f"Received message: type={msg.type}, player={msg.player}, message={msg.message}")
    try:
        if msg.type == "player_chat":
            if msg.player and msg.message:
                await message_handler.send_to_qq(msg.player, msg.message)
                return SendResponse(success=True, message="Message sent")
            else:
                raise HTTPException(status_code=400, detail="Missing player or message")

        elif msg.type == "system":
            if msg.message:
                await message_handler.send_system_to_qq(msg.message)
                return SendResponse(success=True, message="System message sent")
            else:
                raise HTTPException(status_code=400, detail="Missing message")

        elif msg.type == "player_join":
            if msg.player:
                await message_handler.send_system_to_qq(f"📥 {msg.player} 加入了 Minecraft 服务器")
                return SendResponse(success=True, message="Join event sent")
            else:
                raise HTTPException(status_code=400, detail="Missing player")

        elif msg.type == "player_leave":
            if msg.player:
                await message_handler.send_system_to_qq(f"📤 {msg.player} 离开了 Minecraft 服务器")
                return SendResponse(success=True, message="Leave event sent")
            else:
                raise HTTPException(status_code=400, detail="Missing player")

        elif msg.type == "death":
            if msg.message:
                await message_handler.send_system_to_qq(f"💀 {msg.message}")
                return SendResponse(success=True, message="Death message sent")
            else:
                raise HTTPException(status_code=400, detail="Missing message")

        elif msg.type == "achievement":
            if msg.player and msg.message:
                await message_handler.send_system_to_qq(f"🏆 {msg.player} 获得了成就: {msg.message}")
                return SendResponse(success=True, message="Achievement sent")
            else:
                raise HTTPException(status_code=400, detail="Missing player or message")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown message type: {msg.type}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(token: str = Depends(verify_token)):
    """获取状态信息"""
    return {
        "napcat_connected": napcat_client.connected,
        "queue_size": await message_queue.size(),
        "group_id": settings.qq_group_id
    }


@router.get("/players")
async def get_players(token: str = Depends(verify_token)):
    """获取在线玩家列表（由MC服务器提供数据）"""
    from app.player_cache import player_cache
    return player_cache.get_players()


@router.post("/players/update", dependencies=[Depends(verify_token)])
async def update_players(data: PlayerListUpdate):
    """更新在线玩家列表（MC mod调用）"""
    from app.player_cache import player_cache
    await player_cache.update(data.players, data.max_players)
    return {"success": True}

