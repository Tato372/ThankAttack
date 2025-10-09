import constantes
from items import Item 
from tanque import Tanque
import random

destruibles = [4]
no_destruibles = [5]
arbustos = [6]
suelo = [0, 1, 2, 3]
jugador_spawn_tile = 7
jugador2_spawn_tile = 10
enemigo_spawn_tile = 8
fortaleza_tile = 9

class Mundo():
    def __init__(self):
        self.map_tiles = []
        self.obstaculos_tiles = []
        self.arbustos = []
        self.lista_enemigos = []
        self.posiciones_spawn_enemigos = []
        self.posicion_spawn_jugador = None
        self.posicion_spawn_jugador2 = None
        self.posicion_fortaleza = None
        self.tanques_restantes = []

    def cargar_mapa_visual(self, data_suelo, data_objetos, lista_tiles):
        """NUEVA FUNCIÓN: Carga solo los elementos visuales y de colisión del mapa."""
        self.map_tiles.clear()
        self.obstaculos_tiles.clear()
        self.arbustos.clear()
        self.posiciones_spawn_enemigos.clear()

        # --- Suelo ---
        for y, row in enumerate(data_suelo):
            for x, tile in enumerate(row):
                image = lista_tiles[tile]
                rect = image.get_rect(center=(x * constantes.TAMAÑO_REJILLA + 16, y * constantes.TAMAÑO_REJILLA + 16))
                self.map_tiles.append([image, rect, rect.centerx, rect.centery])

        # --- Objetos, Spawns y Fortaleza ---
        for y, row in enumerate(data_objetos):
            for x, tile in enumerate(row):
                if tile == -1: continue
                
                if tile == constantes.jugador_spawn_tile:
                    self.posicion_spawn_jugador = (x, y)
                    continue
                elif tile == constantes.jugador2_spawn_tile:
                    self.posicion_spawn_jugador2 = (x, y)
                    continue
                elif tile == constantes.enemigo_spawn_tile:
                    self.posiciones_spawn_enemigos.append((x, y))
                    continue
                elif tile == constantes.fortaleza_tile:
                    self.posicion_fortaleza = (x, y)
                    continue
                
                image = lista_tiles[tile]
                rect = image.get_rect(center=(x * constantes.TAMAÑO_REJILLA + 16, y * constantes.TAMAÑO_REJILLA + 16))
                tile_data = [image, rect, rect.centerx, rect.centery]

                if tile in constantes.destruibles:
                    tile_data.append(4) # Vida del obstáculo
                    self.obstaculos_tiles.append(tile_data)
                elif tile in constantes.no_destruibles:
                    tile_data.append(-1)
                    self.obstaculos_tiles.append(tile_data)
                elif tile in constantes.arbustos:
                    self.arbustos.append(tile_data)
    
    def generar_enemigos(self, dificultad, num_jugadores, animaciones_enemigos):
        """Prepara la lista de enemigos a generar y spawnea los primeros."""
        self.lista_enemigos.clear()
        self.tanques_restantes.clear()
        
        config = constantes.CONFIG_TANQUES[num_jugadores][dificultad]
        lista_tanques = []
        for tipo_str, cantidad in config.items():
            tipo = int(tipo_str)
            lista_tanques.extend([tipo] * cantidad)
        random.shuffle(lista_tanques)
        self.tanques_restantes = lista_tanques
        
        # Spawnea los primeros enemigos para el modo 1P
        self.spawn_enemigos(animaciones_enemigos, cantidad=4)

    def spawn_enemigos(self, animaciones_enemigos, cantidad=4):
        """Genera enemigos para el modo de 1 jugador."""
        nuevos_tanques = []
        puntos_disponibles = random.sample(self.posiciones_spawn_enemigos, len(self.posiciones_spawn_enemigos))

        for _ in range(min(cantidad, len(self.tanques_restantes))):
            if not puntos_disponibles: break 

            tipo_tanque = self.tanques_restantes.pop(0)
            x_tile, y_tile = puntos_disponibles.pop()
            stats = constantes.TANQUE_STATS[tipo_tanque]
            
            tanque = Tanque(
                x_tile * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
                y_tile * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
                animaciones_enemigos[tipo_tanque - 1],
                stats["vida"], tipo_tanque, stats["velocidad"], stats["cooldown_disparo"]
            )
            self.lista_enemigos.append(tanque)
            nuevos_tanques.append(tanque)
        return nuevos_tanques
                
    def process_data(self, data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad_seleccionada, jugadores_seleccionados):
        """Función original, ahora solo se usa para el modo de 1 jugador."""
        self.cargar_mapa_visual(data_suelo, data_objetos, lista_tiles)
        self.generar_enemigos(dificultad_seleccionada, jugadores_seleccionados, animaciones_enemigos)

    def dibujar(self, pantalla, posicion_camara):
        cam_x, cam_y = posicion_camara
        for tile in self.map_tiles:
            pantalla.blit(tile[0], (tile[1].x - cam_x, tile[1].y - cam_y))
        for obstaculo in self.obstaculos_tiles:
            pantalla.blit(obstaculo[0], (obstaculo[1].x - cam_x, obstaculo[1].y - cam_y))