import constantes
from items import Item 
from tanque import Tanque
import random

obstaculos = [90, 389, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 149, 150, 179, 180, 209, 210, 239, 240, 269, 270, 299, 300, 329, 330, 360, 390, 419, 420, 449, 450, 479, 480, 509, 510, 152, 123, 124, 125, 126, 127, 128, 153, 154, 155, 156, 157, 183, 184, 185, 186, 187, 134, 135, 160, 168, 172, 204, 176, 177, 206, 208, 241, 244, 246, 247, 248, 249, 256, 257, 260, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 276, 277, 278, 279, 286, 287, 295, 302, 303, 304, 306, 307, 308, 309, 313, 314, 315, 316, 317, 336, 337, 338, 339, 343, 344, 345, 368, 373, 374, 375, 393, 394, 395, 405, 423, 424, 425, 453, 454, 455, 464, 491, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 387, 388, 416, 445, 474, 504, 359]
suelo = [121, 129, 130, 131, 132, 133, 136, 137, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 151, 158, 159, 161, 162, 163, 164, 165, 166, 167, 169, 170, 171, 173, 174, 175, 181, 182, 188, 203, 205, 207, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 237, 238, 242, 243, 245, 250, 252, 253, 254, 255, 258, 259, 261, 262, 263, 264, 265, 266, 267, 268, 271, 272, 273, 274, 275, 280, 281, 282, 283, 284, 285, 288, 289, 290, 291, 292, 293, 294, 296, 297, 298, 301, 305, 310, 311, 312, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 331, 332, 333, 335, 340, 341, 346, 347, 348, 349, 351, 352, 353, 354, 355, 356, 357, 358, 362, 363, 364, 365, 366, 367, 369, 370, 371, 372, 376, 377, 378, 379, 380, 381, 382, 383, 384, 386, 389, 391, 392, 396, 397, 398, 399, 400, 401, 402, 403, 404, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 421, 422, 426, 427, 428, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 451, 456, 457, 458, 459, 460, 461, 462, 463, 465, 466, 468, 469, 470, 471, 472, 473, 481, 482, 483, 484, 485, 486, 487, 489, 490, 492, 493, 494, 496, 497, 498, 499, 500, 501, 502, 503]

class Mundo():
    def __init__(self):
        self.map_tiles = []
        self.obstaculos_tiles = []
        self.lista_items = []
        self.lista_enemigos = []
        self.posicion_tile_1 = random.choice(suelo)
        self.posicion_tile_2 = random.choice(suelo)
        self.posicion_tile_3 = random.choice(suelo)
        
    def process_data(self, data, lista_tiles, imagenes_items, animaciones_enemigos):
        self.nivel_length = len(data)
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                image = lista_tiles[tile]
                image_rect = image.get_rect()
                image_x = x * constantes.TAMAÑO_REJILLA + 16
                image_y = y * constantes.TAMAÑO_REJILLA + 16
                image_rect.center = (image_x, image_y)
                tile_data = [image, image_rect, image_x, image_y]

                #Agregar tiles a obstaculos
                if tile in obstaculos:
                    self.obstaculos_tiles.append(tile_data) 
                #Agregar items
                ##Pociones
                elif tile in [122, 342, 385]:
                    pocion = Item(image_x, image_y, 1, imagenes_items[0])
                    self.lista_items.append(pocion)
                ##Monedas
                elif tile in [178, 138, 495, 334, 350]:
                    moneda = Item(image_x, image_y, 0, imagenes_items[1])
                    self.lista_items.append(moneda)
                #Crear tanque enemigos
                ##Tanque amarillo
                elif tile == self.posicion_tile_1:
                    tanque_amarillo = Tanque(image_x, image_y, animaciones_enemigos[0], 90, 2)
                    self.lista_enemigos.append(tanque_amarillo)
                ##Tanque rojo
                elif tile == self.posicion_tile_2:
                    tanque_rojo = Tanque(image_x, image_y, animaciones_enemigos[1], 90, 2)
                    self.lista_enemigos.append(tanque_rojo)
                ##Tanque verde
                elif tile == self.posicion_tile_3:
                    tanque_verde = Tanque(image_x, image_y, animaciones_enemigos[2], 90, 2)
                    self.lista_enemigos.append(tanque_verde)

                self.map_tiles.append(tile_data)
    
    def update(self, posicion_pantalla):
        for tile in self.map_tiles:
            tile[2] += posicion_pantalla[0]
            tile[3] += posicion_pantalla[1]
            tile[1].center = (tile[2], tile[3])
        
    def dibujar(self, pantalla):
        for tile in self.map_tiles:
            pantalla.blit(tile[0], tile[1])