# server.py
import asyncio
import json
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

TICK_RATE = 20  # ticks por segundo

class Player:
    def __init__(self, websocket: WebSocket, name="Player"):
        self.id = str(uuid.uuid4())
        self.ws = websocket
        self.name = name
        self.x = 100
        self.y = 100
        self.vx = 0
        self.vy = 0
        self.hp = 100
        self.inputs = []  # cola de inputs
        self.last_input_seq = 0
        self.last_seen = time.time()

class GameRoom:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.enemies = []  
        self.bullets = []
        self.tick = 0
        self.lock = asyncio.Lock()

    async def broadcast_snapshot(self):
        snapshot = {
            "type": "snapshot",
            "tick": self.tick,
            "state": {
                "players": [
                    {"id": p.id, "x": p.x, "y": p.y, "hp": p.hp}
                    for p in self.players.values()
                ],
                "enemies": [], "bullets": []
            }
        }
        data = json.dumps(snapshot)
        webs = [p.ws.send_text(data) for p in self.players.values()]
        if webs:
            await asyncio.gather(*webs, return_exceptions=True)

    async def step(self):
        # Procesar inputs
        async with self.lock:
            for p in self.players.values():
                while p.inputs:
                    inp = p.inputs.pop(0)
                    # inp = {"keys": {...}, "seq": ..., "t":...}
                    keys = inp.get("keys", {})
                    speed = 2
                    if keys.get("up"): p.y -= speed
                    if keys.get("down"): p.y += speed
                    if keys.get("left"): p.x -= speed
                    if keys.get("right"): p.x += speed
                    # ... disparo se maneja aquí
                    p.last_input_seq = inp.get("seq", p.last_input_seq)
            # Actualizar otras cosas (IA enemigos, bullets)
            self.tick += 1

room = GameRoom()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    player = Player(ws)
    room.players[player.id] = player
    try:
        # Assign ID to client
        await ws.send_text(json.dumps({"type":"assign_id","player_id": player.id}))
        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            player.last_seen = time.time()
            if msg["type"] == "join":
                player.name = msg.get("name","Player")
            elif msg["type"] == "input":
                # Encolar input
                async with room.lock:
                    player.inputs.append(msg)
            # else: ignore others
    except WebSocketDisconnect:
        del room.players[player.id]
    except Exception as e:
        print("error ws:", e)
        if player.id in room.players:
            del room.players[player.id]

async def game_loop():
    interval = 1.0 / TICK_RATE
    while True:
        t0 = time.time()
        try:
            await room.step()
            await room.broadcast_snapshot()
        except Exception as e:
            print("game loop error", e)
        elapsed = time.time() - t0
        await asyncio.sleep(max(0, interval - elapsed))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(game_loop())
    uvicorn.run(app, host="0.0.0.0", port=8000)
