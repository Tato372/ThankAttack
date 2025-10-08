# server.py (código completo y nuevo)

import asyncio
import json
import uuid
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

TICK_RATE = 20  # 20 actualizaciones por segundo

# --- Estructuras para gestionar jugadores y partidas ---
conexiones = {}  # Guarda la conexión de cada jugador por su ID {player_id: websocket}
partidas = {}    # Guarda la información de las partidas creadas {room_id: room_data}

# --- Clases para representar el estado del juego ---
class PlayerState:
    def __init__(self, player_id, x_inicial, y_inicial):
        self.id = player_id
        self.x = x_inicial
        self.y = y_inicial
        self.rot = 0 # NUEVO: Para guardar la rotación
        self.inputs = []
class GameState:
    def __init__(self, partida_info):
        self.id = partida_info["id"]
        self.estado = "en_juego"
        self.players = {}
        # Inicializar jugadores en el estado
        if partida_info.get("host"):
            # MODIFICADO: Usar las posiciones de spawn del mapa
            px1, py1 = partida_info["spawn_p1"]
            self.players[partida_info["host"]] = PlayerState(partida_info["host"], px1, py1)
        if partida_info.get("cliente"):
            px2, py2 = partida_info["spawn_p2"]
            self.players[partida_info["cliente"]] = PlayerState(partida_info["cliente"], px2, py2)

# --- Funciones de Notificación ---
async def notificar_a_jugador(player_id, mensaje):
    if player_id in conexiones:
        await conexiones[player_id].send_text(json.dumps(mensaje))

async def notificar_a_partida(id_partida, mensaje):
    if id_partida in partidas:
        partida = partidas[id_partida]
        # Si la partida ya está en juego, notificar a los jugadores del GameState
        if "game_state" in partida:
            player_ids = partida["game_state"].players.keys()
            for pid in player_ids:
                await notificar_a_jugador(pid, mensaje)
        # Si es una sala de espera, usar host/cliente
        else:
            if partida.get("host"): await notificar_a_jugador(partida["host"], mensaje)
            if partida.get("cliente"): await notificar_a_jugador(partida["cliente"], mensaje)

async def transmitir_lista_partidas():
    lista_para_clientes = {
        pid: {"id": pid, "nombre": p["nombre"], "dificultad": p["dificultad"], "llena": p.get("cliente") is not None}
        for pid, p in partidas.items() if p.get("estado") == "esperando"
    }
    mensaje = {"type": "actualizar_lista_partidas", "partidas": lista_para_clientes}
    for ws in conexiones.values():
        await ws.send_text(json.dumps(mensaje))

# --- Bucle Principal del Juego ---
async def game_loop():
    intervalo = 1.0 / TICK_RATE
    while True:
        t0 = time.time()
        for id_partida, partida in list(partidas.items()):
            if partida.get("estado") == "en_juego":
                game = partida["game_state"]
                
                speed = 4
                for player in game.players.values():
                    while player.inputs:
                        keys = player.inputs.pop(0)
                        # MODIFICADO: Actualizar rotación en el servidor
                        if keys.get("up"): 
                            player.y -= speed
                            player.rot = 270
                        if keys.get("down"): 
                            player.y += speed
                            player.rot = 90
                        if keys.get("left"): 
                            player.x -= speed
                            player.rot = 180
                        if keys.get("right"): 
                            player.x += speed
                            player.rot = 0

                # MODIFICADO: Enviar también la rotación
                snapshot = {
                    "type": "snapshot",
                    "state": {
                        "players": [{"id": p.id, "x": p.x, "y": p.y, "rot": p.rot} for p in game.players.values()]
                    }
                }
                await notificar_a_partida(id_partida, snapshot)
                
        elapsed = time.time() - t0
        await asyncio.sleep(max(0, intervalo - elapsed))

# --- Endpoint de WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    id_jugador = str(uuid.uuid4())
    conexiones[id_jugador] = ws
    print(f"🔌 Jugador conectado: {id_jugador[:8]}. Total: {len(conexiones)}")

    try:
        await notificar_a_jugador(id_jugador, {"type": "assign_id", "player_id": id_jugador})
        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            tipo_mensaje = msg.get("type")

            # --- Lógica del Lobby ---
            if tipo_mensaje == "crear_partida":
                id_partida = str(uuid.uuid4())
                partidas[id_partida] = {
                    "id": id_partida, 
                    "nombre": msg.get("nombre"), 
                    "dificultad": msg.get("dificultad"), 
                    "host": id_jugador, 
                    "cliente": None, 
                    "estado": "esperando",
                    "spawn_p1": msg.get("spawn_p1"), # NUEVO
                    "spawn_p2": msg.get("spawn_p2")  # NUEVO
                }
                await notificar_a_jugador(id_jugador, {"type": "partida_creada", "partida": partidas[id_partida]})
                await transmitir_lista_partidas()
            elif tipo_mensaje == "pedir_lista_partidas":
                await transmitir_lista_partidas()
            elif tipo_mensaje == "unirse_a_partida":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and not partidas[id_partida].get("cliente"):
                    partidas[id_partida]["cliente"] = id_jugador
                    await notificar_a_partida(id_partida, {"type": "actualizacion_partida", "partida": partidas[id_partida]})
                    await transmitir_lista_partidas()
            elif tipo_mensaje == "iniciar_juego":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and partidas[id_partida]["host"] == id_jugador:
                    # Obtenemos la partida actual
                    partida_actual = partidas[id_partida]
                    partida_actual["estado"] = "en_juego"
                    
                    # Creamos el objeto GameState para uso INTERNO del servidor
                    partida_actual["game_state"] = GameState(partida_actual)
                    print(f"🚀 ¡Iniciando partida {id_partida[:8]}!")

                    # --- INICIO DE LA CORRECCIÓN ---
                    # Creamos una copia de la información de la partida para enviar al cliente
                    info_para_cliente = partida_actual.copy()
                    # Eliminamos el objeto que no se puede enviar por la red
                    del info_para_cliente["game_state"]
                    
                    # Enviamos el diccionario limpio al cliente
                    mensaje_inicio = {"type": "iniciar_juego", "partida": info_para_cliente}
                    await notificar_a_partida(id_partida, mensaje_inicio)
                    # --- FIN DE LA CORRECCIÓN ---
                    
                    await transmitir_lista_partidas()
            
            # --- Lógica del Juego en Curso ---
            elif tipo_mensaje == "input":
                # Encontrar la partida del jugador y añadir su input
                for partida in partidas.values():
                    if partida.get("estado") == "en_juego":
                        if id_jugador in partida["game_state"].players:
                            partida["game_state"].players[id_jugador].inputs.append(msg.get("keys", {}))
                            break

    except WebSocketDisconnect:
        print(f"💔 Jugador desconectado: {id_jugador[:8]}")
        # ... (lógica de limpieza de partidas) ...
        del conexiones[id_jugador]
        await transmitir_lista_partidas()

# --- Inicio del Servidor ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)