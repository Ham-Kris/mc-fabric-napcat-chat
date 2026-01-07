"""玩家缓存 - 用于存储当前在线玩家信息"""
import asyncio
from typing import List, Dict
from datetime import datetime


class PlayerCache:
    """玩家信息缓存"""
    
    def __init__(self):
        self._players: List[str] = []
        self._max_players: int = 20
        self._online_count: int = 0
        self._last_update: datetime = datetime.now()
        self._lock = asyncio.Lock()
    
    async def update(self, players: List[str], max_players: int = 20):
        """更新玩家列表"""
        async with self._lock:
            self._players = players
            self._online_count = len(players)
            self._max_players = max_players
            self._last_update = datetime.now()
    
    def get_players(self) -> Dict:
        """获取玩家信息"""
        return {
            "players": self._players,
            "online_count": self._online_count,
            "max_players": self._max_players,
            "last_update": self._last_update.isoformat()
        }


# 全局实例
player_cache = PlayerCache()

