import asyncio
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket


class StaffNotifier:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, guild_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[guild_id].add(websocket)

    async def disconnect(self, guild_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(guild_id)
            if connections and websocket in connections:
                connections.remove(websocket)

    async def broadcast(self, guild_id: str, payload: dict) -> None:
        async with self._lock:
            connections = list(self._connections.get(guild_id, []))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                await self.disconnect(guild_id, websocket)


staff_notifier = StaffNotifier()
