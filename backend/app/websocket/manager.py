from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.rooms[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        connections = self.rooms.get(room, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and room in self.rooms:
            del self.rooms[room]

    async def send_to_room(self, room: str, message: dict):
        dead: list[WebSocket] = []
        for connection in self.rooms.get(room, []):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection, room)


manager = ConnectionManager()
