# network.py
import asyncio
import json
import threading
import time
import queue
import uuid
import websockets  # pip install websockets

class NetworkManager:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.send_q = queue.Queue()   # enviar al servidor
        self.recv_q = queue.Queue()   # mensajes recibidos del servidor
        self.player_id = None
        self.loop = None
        self.ws = None
        self.running = False
        self.thread = threading.Thread(target=self._start_loop, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()

    def _start_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run())

    async def _run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.ws = websocket
                # start background tasks
                recv_task = asyncio.create_task(self._recv_loop())
                send_task = asyncio.create_task(self._send_loop())
                # keep running until cancelled
                await asyncio.gather(recv_task, send_task)
        except Exception as e:
            print("network connection error:", e)
            self.running = False

    async def _recv_loop(self):
        while self.running and self.ws:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                # guardar en cola para hilo principal
                self.recv_q.put(data)
                # process assign id
                if data.get("type") == "assign_id":
                    self.player_id = data.get("player_id")
            except Exception as e:
                print("recv loop error", e)
                break

    async def _send_loop(self):
        while self.running and self.ws:
            try:
                try:
                    item = self.send_q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue
                await self.ws.send(json.dumps(item))
            except Exception as e:
                print("send loop error", e)
                break

    # API para el hilo principal:
    def send_input(self, seq, keys):
        self.send_q.put({"type":"input","seq": seq, "keys": keys, "timestamp": time.time()})

    def join(self, name="Player"):
        self.send_q.put({"type":"join","name": name})

    def poll(self):
        """Devuelve una lista de mensajes recibidos (vací­a la cola)"""
        items = []
        while True:
            try:
                items.append(self.recv_q.get_nowait())
            except queue.Empty:
                break
        return items

    def stop(self):
        self.running = False
