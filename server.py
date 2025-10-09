# server.py (código completo y nuevo)

import asyncio
import json
import uuid
import time
import random
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import pygame
import constantes

app = FastAPI()

TICK_RATE = 20  # 20 actualizaciones por segundo

# --- Estructuras para gestionar jugadores y partidas ---
conexiones = {}  # Guarda la conexión de cada jugador por su ID {player_id: websocket}
partidas = {}    # Guarda la información de las partidas creadas {room_id: room_data}

# --- Clases para representar el estado del juego ---
class PlayerState:
    def __init__(self, player_id, x, y):
        self.id, self.x, self.y = player_id, x, y
        self.spawn_x, self.spawn_y = x, y
        self.hp, self.vidas, self.rot = 90, 3, 0
        self.inputs = []

class EnemyState:
    def __init__(self, id, tipo, x, y):
        self.id, self.tipo, self.x, self.y = id, tipo, x, y
        stats = constantes.TANQUE_STATS[tipo]
        self.hp, self.rot = stats["vida"], 90
        self.speed = stats["velocidad"]

class GameState:
    def __init__(self, partida_info):
        self.id = partida_info["id"]
        self.players = {}
        self.enemies = {}
        self.fortress_hp = 200
        self.obstaculos = [pygame.Rect(o[0], o[1], o[2], o[3]) for o in partida_info["obstaculos"]]
        self.enemy_spawn_list = partida_info["lista_enemigos"]
        self.enemy_spawn_points = partida_info["spawns_enemigos"]
        
        if partida_info.get("host"):
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
            if partida.get("estado") == "en_juego" and "game_state" in partida:
                game = partida["game_state"]
                
                # --- 1. Spawnear Nuevos Enemigos ---
                if len(game.enemies) < 4 and game.enemy_spawn_list:
                    tipo_enemigo = game.enemy_spawn_list.pop(0)
                    if game.enemy_spawn_points:
                        spawn_point = random.choice(game.enemy_spawn_points)
                        x = spawn_point[0] * constantes.TAMAÑO_REJILLA + 16
                        y = spawn_point[1] * constantes.TAMAÑO_REJILLA + 16
                        enemy_id = str(uuid.uuid4())
                        game.enemies[enemy_id] = EnemyState(enemy_id, tipo_enemigo, x, y)

                # --- 2. Actualizar IA y Movimiento de Enemigos ---
                player_size = (26, 26) # Hitbox aproximada de los tanques
                all_enemy_rects = {eid: pygame.Rect(0,0, *player_size, center=(e.x, e.y)) for eid, e in game.enemies.items()}

                for enemy in game.enemies.values():
                    if not game.players: continue # No mover si no hay jugadores

                    # A. Encontrar objetivo (jugador más cercano)
                    closest_player = min(game.players.values(), key=lambda p: math.hypot(p.x - enemy.x, p.y - enemy.y))
                    
                    # B. Calcular dirección del movimiento
                    dx, dy = closest_player.x - enemy.x, closest_player.y - enemy.y
                    dist = math.hypot(dx, dy)
                    mov_x, mov_y = 0, 0
                    if dist > player_size[0]: # Moverse solo si no está muy cerca
                        mov_x = (dx / dist) * enemy.speed
                        mov_y = (dy / dist) * enemy.speed
                    
                    # C. Comprobar colisiones del enemigo (contra obstáculos y otros tanques)
                    original_ex, original_ey = enemy.x, enemy.y
                    enemy_rect = all_enemy_rects[enemy.id]

                    # Mover y comprobar en X
                    enemy.x += mov_x
                    enemy_rect.centerx = enemy.x
                    if enemy_rect.collidelist(game.obstaculos) != -1 or \
                       any(enemy_rect.colliderect(r) for eid, r in all_enemy_rects.items() if eid != enemy.id) or \
                       any(player_rect.colliderect(enemy_rect) for player_rect in all_player_rects.values()):
                        enemy.x = original_ex

                    # Mover y comprobar en Y
                    enemy.y += mov_y
                    enemy_rect.centery = enemy.y
                    if enemy_rect.collidelist(game.obstaculos) != -1 or \
                       any(enemy_rect.colliderect(r) for eid, r in all_enemy_rects.items() if eid != enemy.id) or \
                       any(player_rect.colliderect(enemy_rect) for player_rect in all_player_rects.values()):
                        enemy.y = original_ey
                
                # --- 3. Mover Jugadores y Comprobar Colisiones ---
                all_player_rects = {pid: pygame.Rect(0,0, *player_size, center=(p.x, p.y)) for pid, p in game.players.items()}
                all_enemy_rects_list = list(all_enemy_rects.values())

                for player in game.players.values():
                    player_rect_actual = all_player_rects[player.id]
                    speed = 4
                    
                    while player.inputs:
                        keys = player.inputs.pop(0)
                        original_x, original_y = player.x, player.y

                        # Mover en X
                        if keys.get("left"): player.x -= speed; player.rot = 180
                        if keys.get("right"): player.x += speed; player.rot = 0
                        
                        player_rect_actual.centerx = player.x
                        # Comprobar colisión en X (obstáculos, otros jugadores, enemigos)
                        if player_rect_actual.collidelist(game.obstaculos) != -1 or \
                           any(player_rect_actual.colliderect(r) for pid, r in all_player_rects.items() if pid != player.id) or \
                           player_rect_actual.collidelist(all_enemy_rects_list) != -1:
                            player.x = original_x

                        # Mover en Y
                        if keys.get("up"): player.y -= speed; player.rot = 270
                        if keys.get("down"): player.y += speed; player.rot = 90

                        player_rect_actual.centery = player.y
                        # Comprobar colisión en Y (obstáculos, otros jugadores, enemigos)
                        if player_rect_actual.collidelist(game.obstaculos) != -1 or \
                           any(player_rect_actual.colliderect(r) for pid, r in all_player_rects.items() if pid != player.id) or \
                           player_rect_actual.collidelist(all_enemy_rects_list) != -1:
                            player.y = original_y
                
                # --- 4. Lógica de Muerte y Reaparición (Respawn) ---
                for player in game.players.values():
                    if player.hp <= 0 and player.vidas > 0:
                        player.vidas -= 1
                        if player.vidas > 0:
                            player.hp = 90
                            player.x, player.y = player.spawn_x, player.spawn_y # Reaparecer
                        else:
                            player.hp = 0 # Marcar como permanentemente muerto
                            # Aquí podrías añadir lógica para eliminar al jugador del juego si quieres

                # --- 5. Enviar Snapshot Completo a los Clientes ---
                snapshot = {
                    "type": "snapshot",
                    "state": { 
                        "players": [{"id": p.id, "x": p.x, "y": p.y, "rot": p.rot, "hp": p.hp, "vidas": p.vidas} for p in game.players.values()],
                        "enemies": [{"id": e.id, "tipo": e.tipo, "x": e.x, "y": e.y, "rot": e.rot, "hp": e.hp} for e in game.enemies.values()],
                        "fortress_hp": game.fortress_hp
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
                    "spawn_p2": msg.get("spawn_p2"),  # NUEVO
                    "obstaculos": msg.get("obstaculos")
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
            elif tipo_mensaje == "reportar_daño":
                for p in partidas.values():
                    if p.get("estado") == "en_juego" and id_jugador in p["game_state"].players:
                        game = p["game_state"]
                        if msg.get("es_fortaleza"):
                            game.fortress_hp = max(0, game.fortress_hp - msg.get("daño", 0))
                        else:
                            objetivo_id = msg.get("objetivo_id")
                            if objetivo_id in game.players:
                                target_player = game.players[objetivo_id]
                                target_player.hp = max(0, target_player.hp - msg.get("daño", 0))
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