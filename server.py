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
        # Damos un offset inicial para que los jugadores no spawneen exactamente en el mismo lugar
        self.x += len(room.players) * 50 
        self.y += len(room.players) * 50
        self.vx = 0
        self.vy = 0
        self.hp = 100
        self.inputs = []  # cola de inputs
        self.last_input_seq = 0
        self.last_seen = time.time()
        print(f"[DEBUG-Player] Creado nuevo Player ID: {self.id[:8]} en ({self.x}, {self.y})")


class GameRoom:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.enemies = []  
        self.bullets = []
        self.tick = 0
        self.lock = asyncio.Lock()
        print("[DEBUG-Room] Sala de juego inicializada.")

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
        
        player_count = len(self.players)
        if player_count > 0 and self.tick % TICK_RATE == 0: # Imprimir cada segundo
             print(f"[DEBUG-Snap] Tick: {self.tick}, Players: {player_count}, Pos Jugadores: {[f'{p.id[:4]}:({int(p.x)},{int(p.y)})' for p in self.players.values()]}")

        data = json.dumps(snapshot)
        webs = [p.ws.send_text(data) for p in self.players.values()]
        if webs:
            await asyncio.gather(*webs, return_exceptions=True)

    async def step(self):
        # Procesar inputs
        async with self.lock:
            for p in self.players.values():
                input_count = 0
                while p.inputs:
                    inp = p.inputs.pop(0)
                    input_count += 1
                    keys = inp.get("keys", {})
                    speed = 4  # Velocidad del servidor
                    
                    # Calcular el movimiento
                    vx = 0
                    vy = 0
                    if keys.get("up"): vy = -speed
                    if keys.get("down"): vy = speed
                    if keys.get("left"): vx = -speed
                    if keys.get("right"): vx = speed
                    
                    # Aplicar el movimiento
                    p.x += vx
                    p.y += vy
                    p.last_input_seq = inp.get("seq", p.last_input_seq)
                
                if input_count > 0:
                    print(f"[DEBUG-Input] Jugador {p.id[:8]} procesó {input_count} inputs. Nueva pos: ({int(p.x)}, {int(p.y)})")
                    
            self.tick += 1

room = GameRoom()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    
    # 1. Conexión Establecida
    player = Player(ws)
    room.players[player.id] = player
    addr = ws.client.host
    print(f"[DEBUG-Connect] 🔌 **NUEVO JUGADOR CONECTADO** (ID: {player.id[:8]}) desde {addr}. Total: {len(room.players)}")
    
    try:
        # Assign ID to client
        await ws.send_text(json.dumps({"type":"assign_id","player_id": player.id}))
        print(f"[DEBUG-ID] ID {player.id[:8]} ASIGNADO al cliente.")
        
        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            player.last_seen = time.time()
            
            if msg["type"] == "join":
                player.name = msg.get("name","Player")
                print(f"[DEBUG-Join] Jugador {player.id[:8]} se unió como: '{player.name}'")
                
            elif msg["type"] == "input":
                # Encolar input
                async with room.lock:
                    player.inputs.append(msg)
                    
            # Si el juego es estable, puedes activar este print para ver CADA input
            # print(f"[DEBUG-Input-Raw] {player.id[:8]} envió input. Total en cola: {len(player.inputs)}")
            
    except WebSocketDisconnect:
        # 2. Desconexión
        print(f"[DEBUG-Disconnect] 💔 JUGADOR DESCONECTADO (ID: {player.id[:8]} - '{player.name}').")
        del room.players[player.id]
        print(f"[DEBUG-Disconnect] Jugadores activos restantes: {len(room.players)}")
        
    except Exception as e:
        print(f"[ERROR-WS] Error inesperado en el loop del WS para ID {player.id[:8]}: {e}")
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
            print(f"[ERROR-Loop] Error en el game loop: {e}")
        elapsed = time.time() - t0
        await asyncio.sleep(max(0, interval - elapsed))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(game_loop())
    print("------------------------------------------------------------------")
    print(f"🚀 Servidor de Juego Tank-Attackk iniciado en ws://0.0.0.0:8000/ws")
    print(f"Tasa de Actualización (TICK_RATE): {TICK_RATE} ticks/seg")
    print("------------------------------------------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=8000)
