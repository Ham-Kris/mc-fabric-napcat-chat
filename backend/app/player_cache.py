"""玩家缓存 - 用于存储当前在线玩家信息"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# 缓存过期时间（秒）- MC mod 每5秒更新一次，30秒没更新说明服务器可能离线
CACHE_EXPIRE_SECONDS = 30


class PlayerCache:
    """玩家信息缓存"""
    
    def __init__(self):
        self._players: List[str] = []
        self._max_players: int = 20
        self._online_count: int = 0
        self._last_update: Optional[datetime] = None  # 初始为None表示从未收到数据
        self._lock = asyncio.Lock()
    
    async def update(self, players: List[str], max_players: int = 20):
        """更新玩家列表"""
        async with self._lock:
            self._players = players
            self._online_count = len(players)
            self._max_players = max_players
            self._last_update = datetime.now()
    
    def is_stale(self) -> bool:
        """检查缓存是否过期（服务器可能已离线）"""
        if self._last_update is None:
            return True  # 从未收到过数据
        return datetime.now() - self._last_update > timedelta(seconds=CACHE_EXPIRE_SECONDS)
    
    def get_players(self) -> Dict:
        """获取玩家信息"""
        # 如果缓存过期，返回空列表表示服务器可能离线
        if self.is_stale():
            return {
                "players": [],
                "online_count": 0,
                "max_players": self._max_players,
                "last_update": self._last_update.isoformat() if self._last_update else None,
                "stale": True  # 标记数据已过期
            }
        
        return {
            "players": self._players,
            "online_count": self._online_count,
            "max_players": self._max_players,
            "last_update": self._last_update.isoformat(),
            "stale": False
        }


# 全局实例
player_cache = PlayerCache()

