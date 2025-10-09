# server.py (código completo y corregido)

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
conexiones = {}
partidas = {}

# --- Clases para representar el estado del juego ---
class ItemState:
    def __init__(self, item_id, tipo, x, y):
        self.id, self.tipo, self.x, self.y = item_id, tipo, x, y
        self.rect = pygame.Rect(0, 0, 32, 32) # Tamaño del item
        self.rect.center = (x, y)
class PlayerState:
    def __init__(self, player_id, x, y):
        self.id, self.x, self.y = player_id, x, y
        self.spawn_x, self.spawn_y = x, y
        self.hp, self.vidas, self.rot = 90, 3, 0
        self.inputs = []
        self.ultimo_disparo = 0
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (x, y)
        self.escudo_hasta = 0
        self.potenciado_hasta = 0
        self.boost_hasta = 0 

class EnemyState:
    def __init__(self, id, tipo, x, y):
        self.id, self.tipo, self.x, self.y = id, tipo, x, y
        stats = constantes.TANQUE_STATS[tipo]
        self.hp = stats["vida"]
        self.rot = 90
        self.speed = stats["velocidad"] * 2.5 
        self.ultimo_disparo = 0
        self.cooldown_disparo = stats["cooldown_disparo"]
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (x, y)

class BulletState:
    def __init__(self, id, owner_id, x, y, rot, dano):
        self.id, self.owner_id = id, owner_id
        self.x, self.y, self.rot = x, y, rot
        self.dano = dano
        self.dx = math.cos(math.radians(rot)) * constantes.VELOCIDAD_BALA
        self.dy = -math.sin(math.radians(rot)) * constantes.VELOCIDAD_BALA

class GameState:
    def __init__(self, partida_info):
        self.id = partida_info["id"]
        self.players = {}
        self.enemies = {}
        self.bullets = {}
        self.items = {}
        self.ultimo_spawn_convencional = time.time()
        self.ultimo_spawn_especial = time.time()
        self.reloj_hasta = 0 
        self.fortaleza_escudo_hasta = 0
        self.fortress_hp = 200
        self.obstaculos = []
        for o in partida_info["obstaculos"]:
            rect = pygame.Rect(o[0], o[1], o[2], o[3])
            vida = o[4] if len(o) > 4 else -1
            destruible = vida > 0
            tipo = o[5] if len(o) > 5 else 5   # 👈 agrega el tipo (4 = árbol, 5 = pared)
            self.obstaculos.append({"rect": rect, "vida": vida, "destruible": destruible, "tipo": tipo})
        self.enemy_spawn_list = partida_info["lista_enemigos"]
        self.enemy_spawn_points = partida_info["spawns_enemigos"]
        self.fortress_rect = pygame.Rect(0, 0, constantes.TAMAÑO_REJILLA * 7, constantes.TAMAÑO_REJILLA * 7)
        self.fortress_rect.center = (25 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA * 3.5),
                             45 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA * 3.5))
        self.tiempo_ultima_oleada = time.time()
        self.oleada_activa = False
        if partida_info.get("host"):
            px1, py1 = partida_info["spawn_p1"]
            self.players[partida_info["host"]] = PlayerState(partida_info["host"], px1, py1)
        if partida_info.get("cliente"):
            px2, py2 = partida_info["spawn_p2"]
            self.players[partida_info["cliente"]] = PlayerState(partida_info["cliente"], px2, py2)

def es_visible_servidor(punto_origen, rect_objetivo, obstaculos):
    linea_vision = (punto_origen, rect_objetivo.center)
    for obs in obstaculos:
        if obs["rect"].clipline(linea_vision):  # ✅ usar obs["rect"]
            return False
    return True

async def notificar_a_jugador(player_id, mensaje):
    if player_id in conexiones:
        await conexiones[player_id].send_text(json.dumps(mensaje))

async def notificar_a_partida(id_partida, mensaje):
    if id_partida in partidas and "game_state" in partidas[id_partida]:
        for pid in partidas[id_partida]["game_state"].players:
            await notificar_a_jugador(pid, mensaje)

async def transmitir_lista_partidas():
    lista = {pid: {"id": pid, "nombre": p["nombre"], "dificultad": p["dificultad"], "llena": p.get("cliente") is not None} for pid, p in partidas.items() if p.get("estado") == "esperando"}
    mensaje = {"type": "actualizar_lista_partidas", "partidas": lista}
    for ws in conexiones.values():
        await ws.send_text(json.dumps(mensaje))

async def game_loop():
    intervalo = 1.0 / TICK_RATE
    while True:
        t0 = time.time()
        for id_partida, partida in list(partidas.items()):
            if partida.get("estado") == "en_juego" and "game_state" in partida:
                game = partida["game_state"]
                
                # --- Lógica de Spawning de Items (Nueva y Corregida) ---
                tiempo_actual = time.time()

                # --- Bonus Convencional (cada 60 segundos) ---
                if tiempo_actual - game.ultimo_spawn_convencional > 60 and len(game.items) < 5:
                    game.ultimo_spawn_convencional = tiempo_actual
                    item_id = str(uuid.uuid4())
                    
                    tipo_item = random.choice([
                        constantes.ITEM_ESCUDO,
                        constantes.ITEM_DISPARO_POTENCIADO,
                        constantes.ITEM_RELOJ
                    ])
                    
                    while True:
                        px = random.randint(32, constantes.MAPA_ANCHO - 32)
                        py = random.randint(32, constantes.MAPA_ALTO - 32)
                        item_rect_temp = pygame.Rect(0, 0, 32, 32, center=(px, py))
                        if item_rect_temp.collidelist(game.obstaculos) == -1:
                            break
                    
                    game.items[item_id] = ItemState(item_id, tipo_item, px, py)
                    print(f"[BONUS] Apareció un item convencional: {tipo_item}")

                # --- Bonus Especial (cada 120 segundos, 50% de probabilidad) ---
                if tiempo_actual - game.ultimo_spawn_especial > 120 and len(game.items) < 5:
                    game.ultimo_spawn_especial = tiempo_actual
                    if random.random() < 0.5: # 50% de probabilidad
                        item_id = str(uuid.uuid4())
                        
                        tipo_item = random.choice([
                            constantes.ITEM_BOMBA,
                            constantes.ITEM_BOOST,
                            constantes.ITEM_ESCUDO_FORTALEZA,
                            constantes.ITEM_VIDA
                        ])
                        
                        while True:
                            px = random.randint(32, constantes.MAPA_ANCHO - 32)
                            py = random.randint(32, constantes.MAPA_ALTO - 32)
                            item_rect_temp = pygame.Rect(0, 0, 32, 32, center=(px, py))
                            if item_rect_temp.collidelist(game.obstaculos) == -1:
                                break
                        
                        game.items[item_id] = ItemState(item_id, tipo_item, px, py)
                        print(f"[BONUS] Apareció un item ESPECIAL: {tipo_item}")
                
                # --- Aparición de enemigos ---
                if not game.enemies and game.enemy_spawn_list and not game.oleada_activa:
                    game.oleada_activa = True
                    game.tiempo_ultima_oleada = time.time()
                    print("[OLEADA] Preparando siguiente oleada...")

                if game.oleada_activa and time.time() - game.tiempo_ultima_oleada > 2:  # antes era 10
                    num_a_spawnear = min(4, len(game.enemy_spawn_list))
                    print(f"[OLEADA] Spawneando {num_a_spawnear} enemigos...")
                    puntos_disponibles = random.sample(game.enemy_spawn_points, min(len(game.enemy_spawn_points), num_a_spawnear))

                    for i in range(num_a_spawnear):
                        tipo_enemigo = game.enemy_spawn_list.pop(0)
                        spawn_point = puntos_disponibles[i]
                        x = spawn_point[0] * constantes.TAMAÑO_REJILLA + 16
                        y = spawn_point[1] * constantes.TAMAÑO_REJILLA + 16
                        enemy_id = str(uuid.uuid4())
                        game.enemies[enemy_id] = EnemyState(enemy_id, tipo_enemigo, x, y)
                        print(f"[SPAWN] Enemigo tipo {tipo_enemigo} en {spawn_point}")

                    game.oleada_activa = False

                all_player_rects = {pid: p.rect for pid, p in game.players.items()}
                all_enemy_rects = {eid: e.rect for eid, e in game.enemies.items()}

                # --- IA DE ENEMIGOS ---
                reloj_activo = game.reloj_hasta > time.time()
                if not reloj_activo:
                    for enemy_id, enemy in game.enemies.items():
                        if not game.players: continue
                        
                        jugadores_visibles = []
                        for player in game.players.values():
                            dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
                            if dist < constantes.RANGO_AGGRO_JUGADOR and es_visible_servidor(enemy.rect.center, player.rect, game.obstaculos):
                                jugadores_visibles.append((dist, player))
                        
                        objetivo_movimiento = game.fortress_rect
                        if jugadores_visibles:
                            jugadores_visibles.sort(key=lambda item: item[0])
                            objetivo_movimiento = jugadores_visibles[0][1].rect

                        dx_ideal, dy_ideal = 0, 0
                        if math.hypot(enemy.x - objetivo_movimiento.centerx, enemy.y - objetivo_movimiento.centery) > enemy.rect.width:
                            if abs(enemy.x - objetivo_movimiento.centerx) > abs(enemy.y - objetivo_movimiento.centery):
                                dx_ideal = enemy.speed if objetivo_movimiento.centerx > enemy.x else -enemy.speed
                            else:
                                dy_ideal = enemy.speed if objetivo_movimiento.centery > enemy.y else -enemy.speed

                        mov_x, mov_y = dx_ideal, dy_ideal
                        sensor = enemy.rect.copy()
                        sensor.move_ip(mov_x, mov_y)

                        # Recolectar todos los rects válidos de obstáculos y entidades
                        todos_los_obstaculos_rects = [obs["rect"] for obs in game.obstaculos] \
                                                    + list(all_enemy_rects.values()) \
                                                    + list(all_player_rects.values()) \
                                                    + [game.fortress_rect]

                        # Detectar colisión del sensor con cualquier obstáculo
                        colision = any(obs_rect != enemy.rect and sensor.colliderect(obs_rect) for obs_rect in todos_los_obstaculos_rects)

                        if colision:
                            if dx_ideal != 0:
                                mov_x, mov_y = 0, enemy.speed if objetivo_movimiento.centery > enemy.y else -enemy.speed
                            else:
                                mov_y, mov_x = 0, enemy.speed if objetivo_movimiento.centerx > enemy.x else -enemy.speed

                        # Movimiento y corrección final por colisión real
                        original_ex, original_ey = enemy.x, enemy.y

                        enemy.x += mov_x
                        enemy.rect.centerx = int(enemy.x)
                        for obs_rect in todos_los_obstaculos_rects:
                            if obs_rect != enemy.rect and enemy.rect.colliderect(obs_rect):
                                enemy.x = original_ex
                                enemy.rect.centerx = int(original_ex)
                                break

                        enemy.y += mov_y
                        enemy.rect.centery = int(enemy.y)
                        for obs_rect in todos_los_obstaculos_rects:
                            if obs_rect != enemy.rect and enemy.rect.colliderect(obs_rect):
                                enemy.y = original_ey
                                enemy.rect.centery = int(original_ey)
                                break
                            
                        if mov_x > 0: enemy.rot = 0
                        elif mov_x < 0: enemy.rot = 180
                        elif mov_y > 0: enemy.rot = 90
                        elif mov_y < 0: enemy.rot = 270

                        if time.time() * 1000 - enemy.ultimo_disparo > enemy.cooldown_disparo:
                            objetivo_disparo = None
                            if jugadores_visibles: objetivo_disparo = jugadores_visibles[0][1].rect
                            elif es_visible_servidor(enemy.rect.center, game.fortress_rect, game.obstaculos): objetivo_disparo = game.fortress_rect

                            if objetivo_disparo:
                                dx_shot = objetivo_disparo.centerx - enemy.x
                                dy_shot = objetivo_disparo.centery - enemy.y
                                enemy.rot = math.degrees(math.atan2(-dy_shot, dx_shot))
                                bullet_id = str(uuid.uuid4())
                                game.bullets[bullet_id] = BulletState(bullet_id, enemy_id, enemy.x, enemy.y, enemy.rot, 10)
                                enemy.ultimo_disparo = time.time() * 1000

                # --- Mover Jugadores ---
                for player in game.players.values():
                    # Recoger items
                    for item_id, item in list(game.items.items()):
                        if player.rect.colliderect(item.rect):
                            if item.tipo == constantes.ITEM_ESCUDO: player.escudo_hasta = time.time() + constantes.DURACION_BONUS / 1000
                            elif item.tipo == constantes.ITEM_DISPARO_POTENCIADO: player.potenciado_hasta = time.time() + constantes.DURACION_BONUS / 1000
                            elif item.tipo == constantes.ITEM_VIDA: player.vidas = min(player.vidas + 1, 3)
                            elif item.tipo == constantes.ITEM_BOOST: player.boost_hasta = time.time() + constantes.DURACION_BONUS / 1000
                            elif item.tipo == constantes.ITEM_RELOJ: game.reloj_hasta = time.time() + constantes.DURACION_RELOJ / 1000
                            elif item.tipo == constantes.ITEM_BOMBA: game.enemies.clear()
                            elif item.tipo == constantes.ITEM_ESCUDO_FORTALEZA: game.fortaleza_escudo_hasta = time.time() + constantes.DURACION_ESCUDO_FORTALEZA / 1000
                            del game.items[item_id]; break
                    
                    # Procesar inputs de movimiento
                    while player.inputs:
                        keys = player.inputs.pop(0)
                        original_x, original_y = player.x, player.y
                        
                        es_boosteado = player.boost_hasta > time.time()
                        velocidad = constantes.VELOCIDAD * 1.5 if es_boosteado else constantes.VELOCIDAD

                        if keys.get("left"): player.x -= velocidad; player.rot = 180
                        elif keys.get("right"): player.x += velocidad; player.rot = 0
                        elif keys.get("up"): player.y -= velocidad; player.rot = 270
                        elif keys.get("down"): player.y += velocidad; player.rot = 90
                            
                        player.rect.center = (int(player.x), int(player.y))
                        
                        # Recolectar todos los rects válidos
                        todos_rects = [obs["rect"] for obs in game.obstaculos] + list(all_enemy_rects.values()) + [game.fortress_rect]
                        colision_jugador = False
                        
                        for rect in todos_rects:
                            if player.rect.colliderect(rect):
                                colision_jugador = True
                                break

                        if colision_jugador:
                            player.x, player.y = original_x, original_y
                            player.rect.center = (int(original_x), int(original_y))
                    
                    # Limitar al mapa
                    player.rect.left = max(0, player.rect.left)
                    player.rect.right = min(constantes.MAPA_ANCHO, player.rect.right)
                    player.rect.top = max(0, player.rect.top)
                    player.rect.bottom = min(constantes.MAPA_ALTO, player.rect.bottom)
                    player.x, player.y = player.rect.centerx, player.rect.centery

                # --- Actualizar Balas ---
                for bullet_id, bullet in list(game.bullets.items()):
                    # <<<<<<<<<<<<<<< CORRECCIÓN #1: INICIALIZAR 'hit' >>>>>>>>>>>>>>>
                    hit = False 

                    bullet.x += bullet.dx
                    bullet.y += bullet.dy
                    bullet_rect = pygame.Rect(0, 0, 6, 6)
                    bullet_rect.center = (int(bullet.x), int(bullet.y))
                    
                    if not (0 < bullet.x < constantes.MAPA_ANCHO and 0 < bullet.y < constantes.MAPA_ALTO):
                        del game.bullets[bullet_id]; continue
                    
                    colisionado = None
                    for obs in list(game.obstaculos):
                        if bullet_rect.colliderect(obs["rect"]):
                            colisionado = obs
                            break
                    if colisionado:
                        del game.bullets[bullet_id]
                        if colisionado["destruible"]:
                            colisionado["vida"] -= 1
                            if colisionado["vida"] <= 0:
                                game.obstaculos.remove(colisionado)
                        continue

                    fortaleza_escudada = game.fortaleza_escudo_hasta > time.time()
                    if not fortaleza_escudada and bullet_rect.colliderect(game.fortress_rect):
                        game.fortress_hp = max(0, game.fortress_hp - bullet.dano)
                        del game.bullets[bullet_id]; continue

                    if bullet.owner_id in game.enemies:
                        for pid, player in game.players.items():
                            es_escudado = player.escudo_hasta > time.time()
                            if not es_escudado and bullet_rect.colliderect(player.rect.inflate(-8, -8)):
                                player.hp = max(0, player.hp - bullet.dano)
                                del game.bullets[bullet_id]
                                hit = True; break
                    elif bullet.owner_id in game.players:
                        # <<<<<<<<<<<<<<< CORRECCIÓN #2: ITERAR SOBRE LOS OBJETOS ENEMIGO REALES >>>>>>>>>>>>>>>
                        for eid, enemy in list(game.enemies.items()):
                            if bullet_rect.colliderect(enemy.rect): # Usar enemy.rect
                                enemy.hp = max(0, enemy.hp - bullet.dano)
                                if enemy.hp <= 0: del game.enemies[eid]
                                del game.bullets[bullet_id]
                                hit = True; break
                    
                    if hit: continue
                
                # --- Lógica de Muerte y Respawn ---
                for player in game.players.values():
                    if player.hp <= 0 and player.vidas > 0:
                        player.vidas -= 1
                        if player.vidas > 0:
                            player.hp = 90
                            player.x, player.y = player.spawn_x, player.spawn_y

                # --- Enviar Snapshot ---
                snapshot = {"type": "snapshot", "state": {
                    "players": [{"id": p.id, "x": p.x, "y": p.y, "rot": p.rot, "hp": p.hp, "vidas": p.vidas,
                                "escudo_hasta": p.escudo_hasta, "potenciado_hasta": p.potenciado_hasta,
                                "boost_hasta": p.boost_hasta} for p in game.players.values()],
                    "enemies": [{"id": e.id, "tipo": e.tipo, "x": e.x, "y": e.y, "rot": e.rot, "hp": e.hp} for e in game.enemies.values()],
                    "bullets": [{"id": b.id, "x": b.x, "y": b.y} for b in game.bullets.values()],
                    "items": [{"id": i.id, "x": i.x, "y": i.y, "tipo": i.tipo} for i in game.items.values()],
                    "fortress_hp": game.fortress_hp,
                    "fortaleza_escudo_hasta": game.fortaleza_escudo_hasta,
                    "reloj_activo": game.reloj_hasta > time.time(),
                    "obstaculos": [
                        {"x": o["rect"].x, "y": o["rect"].y, "w": o["rect"].width, "h": o["rect"].height, 
                        "vida": o["vida"], "tipo": o["tipo"]}
                        for o in game.obstaculos
                    ]
                }}
                await notificar_a_partida(id_partida, snapshot)
                
        elapsed = time.time() - t0
        await asyncio.sleep(max(0, intervalo - elapsed))

# --- WebSocket Endpoint ---
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

            if tipo_mensaje == "crear_partida":
                id_partida = str(uuid.uuid4())
                partidas[id_partida] = { "id": id_partida, "nombre": msg.get("nombre"), "dificultad": msg.get("dificultad"), "host": id_jugador, "cliente": None, "estado": "esperando", "spawn_p1": msg.get("spawn_p1"), "spawn_p2": msg.get("spawn_p2"), "obstaculos": msg.get("obstaculos"), "lista_enemigos": msg.get("lista_enemigos"), "spawns_enemigos": msg.get("spawns_enemigos") }
                await notificar_a_jugador(id_jugador, {"type": "partida_creada", "partida": partidas[id_partida]})
                await transmitir_lista_partidas()
            elif tipo_mensaje == "pedir_lista_partidas":
                await transmitir_lista_partidas()
            elif tipo_mensaje == "unirse_a_partida":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and not partidas[id_partida].get("cliente"):
                    partidas[id_partida]["cliente"] = id_jugador
                    partida = partidas[id_partida]
                    await notificar_a_jugador(partida["host"], {"type": "actualizacion_partida", "partida": partida})
                    await notificar_a_jugador(partida["cliente"], {"type": "actualizacion_partida", "partida": partida})
                    await transmitir_lista_partidas()
            elif tipo_mensaje == "iniciar_juego":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and partidas[id_partida]["host"] == id_jugador:
                    partidas[id_partida]["estado"] = "en_juego"
                    partidas[id_partida]["game_state"] = GameState(partidas[id_partida])
                    print(f"🚀 ¡Iniciando partida {id_partida[:8]}!")
                    info_para_cliente = {k: v for k, v in partidas[id_partida].items() if k != "game_state"}
                    await notificar_a_partida(id_partida, {"type": "iniciar_juego", "partida": info_para_cliente})
                    await transmitir_lista_partidas()
            elif tipo_mensaje == "input":
                for p in partidas.values():
                    if p.get("estado") == "en_juego" and id_jugador in p.get("game_state", {}).players:
                        p["game_state"].players[id_jugador].inputs.append(msg.get("keys", {}))
                        break
            elif tipo_mensaje == "disparar":
                for p in partidas.values():
                    if p.get("estado") == "en_juego" and id_jugador in p.get("game_state", {}).players:
                        game = p["game_state"]
                        player = game.players[id_jugador]
                        es_potenciado = player.potenciado_hasta > time.time()
                        dano_bala = 20 if es_potenciado else 10
                        if time.time() * 1000 - player.ultimo_disparo > constantes.DISPARO_COOLDOWN:
                            bullet_id = str(uuid.uuid4())
                            game.bullets[bullet_id] = BulletState(bullet_id, id_jugador, player.x, player.y, player.rot, dano_bala)
                            player.ultimo_disparo = time.time() * 1000
                        break
    except WebSocketDisconnect:
        print(f"💔 Jugador desconectado: {id_jugador[:8]}")
        id_partida_a_limpiar = None
        for pid, p in list(partidas.items()):
            if p.get("host") == id_jugador or p.get("cliente") == id_jugador:
                id_partida_a_limpiar = pid; break
        if id_partida_a_limpiar: del partidas[id_partida_a_limpiar]; print(f"🧹 Partida {id_partida_a_limpiar[:8]} eliminada.")
        if id_jugador in conexiones: del conexiones[id_jugador]
        await transmitir_lista_partidas()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

