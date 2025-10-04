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

    def generar_enemigos(self, dificultad, num_jugadores, animaciones_enemigos, tiles_libres):
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
        self.spawn_enemigos(animaciones_enemigos, tiles_libres, cantidad=4)

    def spawn_enemigos(self, animaciones_enemigos, tiles_libres, cantidad=4):
        """Genera hasta 'cantidad' enemigos de la lista restante y los añade al juego."""
        for _ in range(min(cantidad, len(self.tanques_restantes))):
            if not tiles_libres:
                break

            tipo_tanque = self.tanques_restantes.pop(0)  # sacar el primero de la lista
            x_tile, y_tile = random.choice(tiles_libres)
            tiles_libres.remove((x_tile, y_tile))

            # 📌 Obtener stats desde constantes
            stats = constantes.TANQUE_STATS[tipo_tanque]

            # 📌 Animaciones según el tipo
            animaciones = animaciones_enemigos[tipo_tanque - 1]

            # 📌 Crear tanque
            tanque = Tanque(
                x_tile * constantes.TAMAÑO_REJILLA + 16,
                y_tile * constantes.TAMAÑO_REJILLA + 16,
                animaciones,
                stats["vida"],
                tipo_tanque,
                stats["velocidad"],
                stats["cooldown_disparo"]
            )

            self.lista_enemigos.append(tanque)
            self.tanques_en_pantalla.append(tanque)
                
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

        self.generar_enemigos(
            dificultad_seleccionada,       # <- variable global/guardada al elegir en menú
            jugadores_seleccionados,    # <- igual que arriba
            animaciones_enemigos,
            tiles_libres
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
        
    def dibujar(self, pantalla, tanque_jugador, posicion_camara):
        cam_x, cam_y = posicion_camara
        
        cam_x = tanque_jugador.forma.centerx - constantes.ANCHO_VENTANA
        cam_y = tanque_jugador.forma.centery - constantes.ALTO_VENTANA

        # --- Definir zona muerta ---
        zona_muerta_ancho = constantes.ANCHO_VENTANA // 3   # 1/3 del ancho
        zona_muerta_alto = constantes.ALTO_VENTANA // 3     # 1/3 del alto

        zona_muerta_x = (constantes.ANCHO_VENTANA - zona_muerta_ancho) // 2
        zona_muerta_y = (constantes.ALTO_VENTANA - zona_muerta_alto) // 2
        
        # Posición del tanque en coordenadas de pantalla
        tanque_x_pantalla = tanque_jugador.forma.centerx - cam_x
        tanque_y_pantalla = tanque_jugador.forma.centery - cam_y
        
        if tanque_x_pantalla < zona_muerta_x:
            cam_x -= (zona_muerta_x - tanque_x_pantalla)
        elif tanque_x_pantalla > zona_muerta_x + zona_muerta_ancho:
            cam_x += (tanque_x_pantalla - (zona_muerta_x + zona_muerta_ancho))
        
        if tanque_y_pantalla < zona_muerta_y:
            cam_y -= (zona_muerta_y - tanque_y_pantalla)
        elif tanque_y_pantalla > zona_muerta_y + zona_muerta_alto:
            cam_y += (tanque_y_pantalla - (zona_muerta_y + zona_muerta_alto))
        
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