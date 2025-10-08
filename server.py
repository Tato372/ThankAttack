# server.py (código completo y nuevo)
import asyncio
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# --- NUEVO: Estructuras para gestionar jugadores y partidas ---
conexiones = {} # Guarda la conexión de cada jugador por su ID
partidas = {}   # Guarda la información de las partidas creadas

# --- Funciones de ayuda para notificar a los jugadores ---
async def notificar_a_jugador(id_jugador, mensaje):
    if id_jugador in conexiones:
        await conexiones[id_jugador].send_text(json.dumps(mensaje))

async def notificar_a_partida(id_partida, mensaje):
    if id_partida in partidas:
        partida = partidas[id_partida]
        host = partida["host"]
        cliente = partida.get("cliente")
        if host:
            await notificar_a_jugador(host, mensaje)
        if cliente:
            await notificar_a_jugador(cliente, mensaje)

async def transmitir_lista_partidas():
    lista_para_clientes = {
        pid: {"id": pid, "nombre": p["nombre"], "dificultad": p["dificultad"], "llena": "cliente" in p}
        for pid, p in partidas.items()
    }
    mensaje = {"type": "actualizar_lista_partidas", "partidas": lista_para_clientes}
    for ws in conexiones.values():
        await ws.send_text(json.dumps(mensaje))

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    id_jugador = str(uuid.uuid4())
    conexiones[id_jugador] = ws
    print(f"🔌 Jugador conectado: {id_jugador[:8]}. Total: {len(conexiones)}")

    try:
        # Asignar ID al cliente
        await notificar_a_jugador(id_jugador, {"type": "assign_id", "player_id": id_jugador})

        while True:
            text = await ws.receive_text()
            msg = json.loads(text)
            tipo_mensaje = msg.get("type")

            if tipo_mensaje == "crear_partida":
                id_partida = str(uuid.uuid4())
                partidas[id_partida] = {
                    "id": id_partida,
                    "nombre": msg.get("nombre", "Partida sin nombre"),
                    "dificultad": msg.get("dificultad", "Facil"),
                    "host": id_jugador,
                    "cliente": None,
                    "estado": "esperando"
                }
                print(f"🚪 Partida creada por {id_jugador[:8]} -> ID: {id_partida[:8]}")
                await notificar_a_jugador(id_jugador, {"type": "partida_creada", "partida": partidas[id_partida]})
                await transmitir_lista_partidas()

            elif tipo_mensaje == "pedir_lista_partidas":
                await transmitir_lista_partidas()

            elif tipo_mensaje == "unirse_a_partida":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and not partidas[id_partida].get("cliente"):
                    partidas[id_partida]["cliente"] = id_jugador
                    partidas[id_partida]["estado"] = "lista"
                    print(f"🤝 Jugador {id_jugador[:8]} se unió a {id_partida[:8]}")
                    await notificar_a_partida(id_partida, {"type": "actualizacion_partida", "partida": partidas[id_partida]})
                    await transmitir_lista_partidas()

            elif tipo_mensaje == "iniciar_juego":
                id_partida = msg.get("id_partida")
                if id_partida in partidas and partidas[id_partida]["host"] == id_jugador:
                    print(f"🚀 ¡Iniciando partida {id_partida[:8]}!")
                    partidas[id_partida]["estado"] = "en_juego"
                    await notificar_a_partida(id_partida, {"type": "iniciar_juego", "partida": partidas[id_partida]})
                    # Opcional: eliminar la partida de la lista pública
                    # del partidas[id_partida]
                    await transmitir_lista_partidas()

    except WebSocketDisconnect:
        print(f"💔 Jugador desconectado: {id_jugador[:8]}")
        # Lógica para limpiar partidas si un jugador se desconecta
        partida_a_eliminar = None
        for pid, p in partidas.items():
            if p["host"] == id_jugador:
                partida_a_eliminar = pid
                break
            if p.get("cliente") == id_jugador:
                p["cliente"] = None # El cliente se fue, la partida vuelve a estar abierta
                await notificar_a_jugador(p["host"], {"type": "actualizacion_partida", "partida": p})

        if partida_a_eliminar:
            del partidas[partida_a_eliminar]
        
        del conexiones[id_jugador]
        await transmitir_lista_partidas()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)