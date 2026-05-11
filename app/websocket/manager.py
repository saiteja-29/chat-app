from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket):
        connections = self.active_connections.get(user_id, [])

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(user_id, None)

    def is_user_connected(self, user_id: UUID) -> bool:
        return user_id in self.active_connections

    async def send_to_user(self, user_id: UUID, message: dict):
        connections = self.active_connections.get(user_id, [])

        for websocket in connections:
            await websocket.send_json(message)

    async def broadcast_to_users(self, user_ids: list[UUID], message: dict):
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def broadcast_all(self, message: dict):
        for connections in self.active_connections.values():
            for websocket in connections:
                await websocket.send_json(message)


manager = ConnectionManager()