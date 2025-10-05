import constantes
from items import Item 
from tanque import Tanque
import random

destruibles = [4]
no_destruibles = [5]
arbustos = [6]
suelo = [0, 1, 2, 3]
jugador_spawn_tile = 7
enemigo_spawn_tile = 8
fortaleza_tile = 9

class Mundo():
    def __init__(self):
        self.map_tiles = []
        self.obstaculos_tiles = []
        self.arbustos = []
        self.lista_items = []
        self.lista_enemigos = []
        self.posicion_tile_1 = random.choice(suelo)
        self.posicion_tile_2 = random.choice(suelo)
        self.posicion_tile_3 = random.choice(suelo)
        self.posiciones_spawn_enemigos = []
        self.posicion_spawn_jugador = None
        self.posicion_fortaleza = None

    def generar_enemigos(self, dificultad, num_jugadores, animaciones_enemigos):
        """Prepara la lista de enemigos a generar según dificultad y jugadores, y spawnea los primeros."""
        # 1️⃣ Obtener configuración según dificultad y número de jugadores
        config = constantes.CONFIG_TANQUES[num_jugadores][dificultad]

        # 2️⃣ Crear lista de tipos de tanques que se deben generar (ej: [1,1,1,2,3,3,4,5,...])
        lista_tanques = []
        for tipo_str, cantidad in config.items():
            tipo = int(tipo_str)  # las claves vienen como strings
            lista_tanques.extend([tipo] * cantidad)

        random.shuffle(lista_tanques)  # para que no salgan siempre en el mismo orden

        # Guardamos la lista de tanques pendientes para ir sacándolos en oleadas
        self.tanques_restantes = lista_tanques
        self.tanques_en_pantalla = []

        # 3️⃣ Spawnear los primeros 4 tanques
        self.spawn_enemigos(animaciones_enemigos, cantidad=4)

    def spawn_enemigos(self, animaciones_enemigos, cantidad=4):
        """Genera enemigos usando posiciones de spawn únicas para cada oleada."""
        nuevos_tanques = []
        # Crea una copia barajada de los puntos de spawn para no repetir en esta oleada
        puntos_disponibles = random.sample(self.posiciones_spawn_enemigos, len(self.posiciones_spawn_enemigos))

        for _ in range(min(cantidad, len(self.tanques_restantes))):
            # Si ya no quedan puntos de spawn únicos para esta oleada, nos detenemos
            if not puntos_disponibles:
                break 

            tipo_tanque = self.tanques_restantes.pop(0)
            # Extraemos un punto de spawn único de la lista temporal
            x_tile, y_tile = puntos_disponibles.pop()

            stats = constantes.TANQUE_STATS[tipo_tanque]
            animaciones = animaciones_enemigos[tipo_tanque - 1]

            tanque = Tanque(
                x_tile * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
                y_tile * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
                animaciones,
                stats["vida"],
                tipo_tanque,
                stats["velocidad"],
                stats["cooldown_disparo"]
            )
            self.lista_enemigos.append(tanque)
            nuevos_tanques.append(tanque)
                
        return nuevos_tanques
                
    def process_data(self, data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad_seleccionada, jugadores_seleccionados):
        self.nivel_length = len(data_suelo)

        # --- Suelo ---
        for y, row in enumerate(data_suelo):
            for x, tile in enumerate(row):
                image = lista_tiles[tile]
                rect = image.get_rect()
                rect.center = (
                    x * constantes.TAMAÑO_REJILLA + 16,
                    y * constantes.TAMAÑO_REJILLA + 16
                )
                self.map_tiles.append([image, rect, rect.centerx, rect.centery])

        # --- Objetos, Spawns y Fortaleza ---
        tiles_libres = []
        for y, row in enumerate(data_objetos):
            for x, tile in enumerate(row):
                if tile == -1:
                    tiles_libres.append((x, y)) # Guardamos los tiles vacíos por si los necesitamos
                    continue
                
                # --- Guardar posiciones de spawn ---
                if tile == jugador_spawn_tile:
                    self.posicion_spawn_jugador = (x, y)
                    continue # No dibujamos un objeto aquí
                elif tile == enemigo_spawn_tile:
                    self.posiciones_spawn_enemigos.append((x, y))
                    continue
                elif tile == fortaleza_tile:
                    self.posicion_fortaleza = (x, y)
                    continue
                
                # --- Procesar objetos normales (ladrillos, metal, etc.) ---
                image = lista_tiles[tile]
                rect = image.get_rect()
                rect.center = (x * constantes.TAMAÑO_REJILLA + 16, y * constantes.TAMAÑO_REJILLA + 16)
                tile_data = [image, rect, rect.centerx, rect.centery]

                if tile in destruibles:
                    tile_data.append(2)
                    self.obstaculos_tiles.append(tile_data)
                elif tile in no_destruibles:
                    tile_data.append(-1)
                    self.obstaculos_tiles.append(tile_data)
                elif tile in arbustos:
                    self.arbustos.append(tile_data)
        
        # Generar la lista de enemigos (ya no necesita tiles_libres)
        self.generar_enemigos(
            dificultad_seleccionada,
            jugadores_seleccionados,
            animaciones_enemigos
        )

        # --- Items aleatorios ---
        num_items = 10
        for _ in range(num_items):
            if not tiles_libres:
                break
            x, y = random.choice(tiles_libres)
            tiles_libres.remove((x, y))
            tipo_item = random.choice([0, 1])
            item = Item(x * constantes.TAMAÑO_REJILLA + 16,
                        y * constantes.TAMAÑO_REJILLA + 16,
                        tipo_item,
                        imagenes_items[tipo_item])
            self.lista_items.append(item)
    
    def update(self, posicion_pantalla):
        for tile in self.map_tiles:
            tile[2] += posicion_pantalla[0]
            tile[3] += posicion_pantalla[1]
            tile[1].center = (tile[2], tile[3])
        
    def dibujar(self, pantalla, posicion_camara):
        # Usa directamente la posición de la cámara que recibe como argumento
        cam_x, cam_y = posicion_camara

        # Dibuja los tiles del suelo
        for tile in self.map_tiles:
            pantalla.blit(tile[0], (tile[1].x - cam_x, tile[1].y - cam_y))

        # Dibuja los obstáculos
        for obstaculo in self.obstaculos_tiles:
            pantalla.blit(obstaculo[0], (obstaculo[1].x - cam_x, obstaculo[1].y - cam_y))
