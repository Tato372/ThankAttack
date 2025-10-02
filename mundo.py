import constantes
from items import Item 
from tanque import Tanque
import random

destruibles = [4]
no_destruibles = [5]
arbustos = [6]
suelo = [0, 1, 2, 3]

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
    def process_data(self, data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos):
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

        # --- Objetos ---
        for y, row in enumerate(data_objetos):
            for x, tile in enumerate(row):
                if tile == -1:
                    continue
                image = lista_tiles[tile]
                rect = image.get_rect()
                rect.center = (
                    x * constantes.TAMAÑO_REJILLA + 16,
                    y * constantes.TAMAÑO_REJILLA + 16
                )
                tile_data = [image, rect, rect.centerx, rect.centery]

                if tile in destruibles:
                    tile_data.append(2)  # 2 balas para destruirlo
                    self.obstaculos_tiles.append(tile_data)
                elif tile in no_destruibles:
                    tile_data.append(-1)  # indestructible
                    self.obstaculos_tiles.append(tile_data)
                elif tile in arbustos:
                    self.arbustos.append(tile_data)

        # --- Tiles libres ---
        tiles_libres = []
        for y, row in enumerate(data_suelo):
            for x, tile in enumerate(row):
                if tile in suelo and data_objetos[y][x] == -1:
                    tiles_libres.append((x, y))

        # --- Posiciones de tanques ---
        self.posicion_tile_1 = random.choice(tiles_libres)
        tiles_libres.remove(self.posicion_tile_1)
        self.posicion_tile_2 = random.choice(tiles_libres)
        tiles_libres.remove(self.posicion_tile_2)
        self.posicion_tile_3 = random.choice(tiles_libres)
        tiles_libres.remove(self.posicion_tile_3)

        posiciones_tanques = [self.posicion_tile_1, self.posicion_tile_2, self.posicion_tile_3]
        animaciones = animaciones_enemigos

        for idx, pos in enumerate(posiciones_tanques):
            x, y = pos
            tanque = Tanque(x * constantes.TAMAÑO_REJILLA + 16,
                            y * constantes.TAMAÑO_REJILLA + 16,
                            animaciones[idx], 90, 2)
            self.lista_enemigos.append(tanque)

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
        
    def dibujar(self, pantalla, tanque_jugador, posicion_camara):
        cam_x, cam_y = posicion_camara
        
        cam_x = tanque_jugador.forma.centerx - constantes.ANCHO_VENTANA
        cam_y = tanque_jugador.forma.centery - constantes.ALTO_VENTANA

        # Limitar cámara para que no se salga del mapa
        cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
        cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))

        for tile in self.map_tiles:
            pantalla.blit(tile[0], (tile[1].x - cam_x, tile[1].y - cam_y))

        for obstaculo in self.obstaculos_tiles:
            pantalla.blit(obstaculo[0], (obstaculo[1].x - cam_x, obstaculo[1].y - cam_y))

        for arbusto in self.arbustos:
            pantalla_y = arbusto[1].y - cam_y
            pantalla_x = arbusto[1].x - cam_x
            if not arbusto[1].colliderect(tanque_jugador.forma):
                pantalla.blit(arbusto[0], (pantalla_x, pantalla_y))