import pygame
import constantes
from tanque import Tanque
from weapon import Weapon
from textos import DamageText
from fortaleza import Fortaleza
from items import Item
from mundo import Mundo
import os
import csv
import random 
from network import NetworkManager
import math
import time

pygame.init()

game_state = "MENU_PRINCIPAL" # "MENU_PRINCIPAL", "LOBBY", "EN_JUEGO", "GAME_OVER", "VICTORIA"
partidas_disponibles = {} 
mi_partida_actual = {}
remote_players = {}
remote_enemies = {} 
remote_bullets = {}
remote_items = {}
botones_partidas = []
info_partida = {
    "nombre": "",
    "dificultad": "Facil",
    "host": "jugador1",
    "cliente": None, 
    "estado": "ESPERANDO" 
}
jugador1_listo = False
jugador2_listo = False

net = NetworkManager("ws://172.24.86.164:8000/ws")

pantalla = pygame.display.set_mode((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA))
pygame.display.set_caption("Tank-Atackk")

#Funciones:

def pantalla_lista_partidas():
    global botones_partidas
    pantalla.fill(constantes.COLOR_FONDO)
    dibujar_texto("PARTIDAS DISPONIBLES", fuente_titulo, constantes.BLANCO, 150, 50)
    
    botones_partidas = []
    y_pos = 150
    if not partidas_disponibles:
        dibujar_texto("No hay partidas, ¡crea una!", fuente_inicio, constantes.AMARILLO, 300, 300)
    else:
        for id_partida, info in partidas_disponibles.items():
            if not info["llena"]:
                texto = f"{info['nombre']} - {info['dificultad']}"
                rect = pygame.Rect(300, y_pos, 600, 50)
                botones_partidas.append((id_partida, rect))
                dibujar_boton_retro(texto, rect)
                y_pos += 70

    dibujar_boton_retro("Refrescar", boton_refrescar_partidas)
    dibujar_boton_retro("Volver", boton_volver_lobby)
    pygame.display.update()
    
#Funcion para dibujar botones
def dibujar_boton_retro(texto, rect, seleccionado=False):
    # Dibujar fondo
    if texto == "Jugar":
        pygame.draw.rect(pantalla, constantes.VERDE, rect)
    elif texto == "Salir":
        pygame.draw.rect(pantalla, constantes.ROJO, rect)
    elif texto == "Reiniciar" and rect == boton_reinicio:
        pygame.draw.rect(pantalla, constantes.ROJO, rect)
    elif texto == "Reiniciar":
        pygame.draw.rect(pantalla, constantes.VERDE, rect)
    elif texto == "Menu Principal" and rect == boton_volver_menu:
        pygame.draw.rect(pantalla, constantes.GRIS, rect)
    elif texto == "Menu Principal":
        pygame.draw.rect(pantalla, constantes.GRIS, rect)
    elif texto == "Siguiente Dificultad":
        pygame.draw.rect(pantalla, constantes.GRIS, rect)
    
    # Dibujar borde pixelado
    for i in range(3):  # grosor del borde
        if seleccionado:
            pygame.draw.rect(pantalla, constantes.COLOR_BORDE_SEL, rect.inflate(i*2, i*2), 1)
        else:
            pygame.draw.rect(pantalla, constantes.COLOR_BORDE, rect.inflate(i*2, i*2), 1)

    # Renderizar texto pixelado centrado
    img_texto = fuente_inicio.render(texto, True, constantes.COLOR_TEXTO)
    text_rect = img_texto.get_rect(center=rect.center)
    pantalla.blit(img_texto, text_rect)
    
##Funcion para escalar imagenes
def escalar_img(img, escala_ancho, escala_alto):
    width = img.get_width()
    height = img.get_height()
    nueva_img = pygame.transform.scale(img, (int(width * escala_ancho), int(height * escala_alto)))
    return nueva_img

##Funcion para contar elementos
def contar_elementos(directorio):
    return len(os.listdir(directorio))

#Funcion para mostrar la vida del jugaor
def vida_jugador(jugador):
    c_mitad_dibujado = False
    for i in range(3):
        if jugador.energia >= ((i+1)*30):
            pantalla.blit(corazon_completo, (5+i*30, 5))
        elif jugador.energia % 30 > 0 and c_mitad_dibujado == False:
            pantalla.blit(corazon_mitad, (5+i*30, 5))
            c_mitad_dibujado = True
        else:
            pantalla.blit(corazon_vacio, (5+i*30, 5))
            

##Funcion para listar los nombres de los elementos
def nombre_carpetas(directorio):
    return os.listdir(directorio)

##Funcion para dibujar Rejilla
def dibujar_rejilla():
    for x in range(30):
        pygame.draw.line(pantalla, constantes.BLANCO, (x * constantes.TAMAÑO_REJILLA, 0), (x * constantes.TAMAÑO_REJILLA, constantes.ALTO_VENTANA))
        pygame.draw.line(pantalla, constantes.BLANCO, (0, x * constantes.TAMAÑO_REJILLA), (constantes.ANCHO_VENTANA, x * constantes.TAMAÑO_REJILLA))

##Funcion para dibujar texto
def dibujar_texto(texto, fuente, color, x, y):
    img = fuente.render(texto, True, color)
    pantalla.blit(img, (x, y))
    
##Funcion para resetear el mundo
def resetear_mundo():
    global oleada_actual, vidas_jugador
    oleada_actual = 1
    vidas_jugador = 3
    
    return iniciar_partida(dificultad_seleccionada, jugadores_seleccionados)

def iniciar_partida(dificultad, num_jugadores):
    tanques, tanques_enemigos, tanques_aliados = [], [], []
    grupo_balas, grupo_balas_enemigas = pygame.sprite.Group(), pygame.sprite.Group()
    grupo_textos_daño, grupo_items = pygame.sprite.Group(), pygame.sprite.Group()

    mundo = Mundo()
    mundo.cargar_mapa_visual(data_suelo, data_objetos, lista_tiles)
    
    if num_jugadores == 1:
        mundo.generar_enemigos(dificultad, num_jugadores, animaciones_enemigos)
        for enemigo in mundo.lista_enemigos:
            tanques.append(enemigo)
            tanques_enemigos.append(enemigo)
    
    px1, py1 = mundo.posicion_spawn_jugador if mundo.posicion_spawn_jugador else (5,5)
    tanque_jugador1 = Tanque(
        px1 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        py1 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        animaciones, 90, 0, constantes.VELOCIDAD, constantes.DISPARO_COOLDOWN
    )
    tanque_jugador1.id_red = mi_id_de_red
    tanques.append(tanque_jugador1)
    tanques_aliados.append(tanque_jugador1)
    
    cañon_jugador = Weapon(imagen_cañon, imagen_balas)

    fx, fy = mundo.posicion_fortaleza if mundo.posicion_fortaleza else (25, 45)
    fortaleza = Fortaleza(
        fx * constantes.TAMAÑO_REJILLA,
        fy * constantes.TAMAÑO_REJILLA,
        imagen_fortaleza
    )
    
    muros_originales = {} 

    return mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales

def pantalla_lobby():
    pantalla.fill(constantes.COLOR_FONDO)
    dibujar_texto("MODO DOS JUGADORES", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA / 4 - 100, 100)
    dibujar_boton_retro("Crear Partida", boton_crear_partida)
    dibujar_boton_retro("Unirse a Partida", boton_unirse_partida)
    dibujar_boton_retro("Volver", boton_volver_lobby)
    pygame.display.update()

def pantalla_espera_host():
    pantalla.fill(constantes.COLOR_FONDO)
    
    nombre_partida = mi_partida_actual.get("nombre", "Cargando...")
    dificultad_partida = mi_partida_actual.get("dificultad", "")
    
    dibujar_texto(f"Partida: {nombre_partida}", fuente_inicio, constantes.BLANCO, 100, 100)
    dibujar_texto(f"Dificultad: {dificultad_partida}", fuente_inicio, constantes.BLANCO, 100, 160)
    
    if mi_partida_actual.get("cliente"):
        dibujar_texto("¡Jugador 2 se ha unido!", fuente_titulo, constantes.VERDE, constantes.ANCHO_VENTANA / 4 - 200, 300)
        
        if mi_partida_actual.get("host") == net.player_id:
            dibujar_boton_retro("Iniciar Partida", boton_iniciar_partida)
    else:
        dibujar_texto("Esperando al Jugador 2...", fuente_titulo, constantes.AMARILLO, constantes.ANCHO_VENTANA / 4 - 150, 300)

    dibujar_boton_retro("Cancelar", boton_volver_lobby)

def agregar_dificultad_pesadilla():
    global dificultades, botones_dificultad
    if "Pesadilla" not in dificultades:
        dificultades.append("Pesadilla")
        rect = pygame.Rect(constantes.ANCHO_VENTANA // 4 - 125, botones_dificultad[-1].y + 70, 250, 50)
        botones_dificultad.append(rect)
def quitar_dificultad_pesadilla():
    global dificultades, botones_dificultad, dificultad_seleccionada
    if "Pesadilla" in dificultades:
        dificultades.remove("Pesadilla")
        botones_dificultad.pop()
        if dificultad_seleccionada == "Pesadilla":
            dificultad_seleccionada = None

def pantalla_inicio():
    inicio_image = pygame.image.load("assets//images//pantallas//pantalla_inicio.png")
    inicio_image = escalar_img(inicio_image, constantes.ANCHO_VENTANA / inicio_image.get_width(), constantes.ALTO_VENTANA / inicio_image.get_height())
    pantalla.blit(inicio_image, (0, 0))
    dibujar_texto("TANK ATTACK", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA / 4, constantes.ALTO_VENTANA / 4 - 100)
    dibujar_texto("Jugadores:", fuente_inicio, constantes.BLANCO, botones_jugadores[0].x, botones_jugadores[0].y - 50)
    for i, rect in enumerate(botones_jugadores):
        color = constantes.VERDE if jugadores_seleccionados == i + 1 else constantes.BLANCO
        pygame.draw.rect(pantalla, color, rect, 3)
        dibujar_texto(jugadores[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
    dibujar_texto("Dificultad:", fuente_inicio, constantes.BLANCO, botones_dificultad[0].x, botones_dificultad[0].y - 50)
    if jugadores_seleccionados == 2:
        agregar_dificultad_pesadilla()
        for i, rect in enumerate(botones_dificultad):
            color = constantes.VERDE if dificultad_seleccionada == dificultades[i] else constantes.BLANCO
            pygame.draw.rect(pantalla, color, rect, 3)
            dibujar_texto(dificultades[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
    else:
        quitar_dificultad_pesadilla()
        for i, rect in enumerate(botones_dificultad):
            color = constantes.VERDE if dificultad_seleccionada == dificultades[i] else constantes.BLANCO
            pygame.draw.rect(pantalla, color, rect, 3)
            dibujar_texto(dificultades[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
        
    dibujar_boton_retro("Jugar", boton_jugar)
    dibujar_boton_retro("Salir", boton_salir)
    
    pygame.display.update()

def dibujar_hud_bonus(tanque, fortaleza_protegida_hasta, reloj_activo):
    tiempo_actual_servidor = time.time()
    y_pos = 120
    
    if tanque.escudo_activo:
        tiempo_restante = tanque.escudo_hasta - tiempo_actual_servidor
        dibujar_texto(f"Escudo: {int(tiempo_restante)}s", fuente, constantes.AZUL_CIELO_VIVO, 10, y_pos)
        y_pos += 30
    if tanque.potenciado_activo:
        tiempo_restante = tanque.potenciado_hasta - tiempo_actual_servidor
        dibujar_texto(f"Doble Dano: {int(tiempo_restante)}s", fuente, constantes.ROJO, 10, y_pos)
        y_pos += 30
    if tanque.boost_activo:
        tiempo_restante = tanque.boost_hasta - tiempo_actual_servidor
        dibujar_texto(f"Boost: {int(tiempo_restante)}s", fuente, constantes.AMARILLO, 10, y_pos)
        y_pos += 30
    
    if fortaleza_protegida_hasta > tiempo_actual_servidor:
        tiempo_restante = fortaleza_protegida_hasta - tiempo_actual_servidor
        dibujar_texto(f"Escudo Fortaleza: {int(tiempo_restante)}s", fuente, constantes.GRIS, 10, y_pos)
        y_pos += 30
    if reloj_activo:
        dibujar_texto(f"TIEMPO CONGELADO", fuente, constantes.BLANCO, 10, y_pos)
        y_pos += 30
    
#Variables
nivel = 1
oleada_actual = 1
tanques = []
vidas_jugador = 3
muros_originales = {}
tiempo_inicio_partida = 0
mi_id_de_red = None
# <<<<<<<<<<<<<<<<<<< SOLUCIÓN AL NameError >>>>>>>>>>>>>>>>>>>
# Inicializamos las variables con un valor por defecto al inicio del programa.
fortaleza_protegida_hasta = 0
reloj_activo_remoto = False

dificultades = ["Facil", "Intermedio", "Dificil"]
dificultad_actual = 0

jugadores = ["Un Jugador", "Dos Jugadores"]
jugadores_actual = 0 

dificultad_seleccionada = "Facil"
jugadores_seleccionados = 1

#Importar fuentes
fuente = pygame.font.Font("assets//fuentes//fibberish.ttf", 25)
fuente_botones = pygame.font.Font("assets//fuentes//fibberish.ttf", 40)
fuente_game_over = pygame.font.Font("assets//fuentes//fibberish.ttf", 125)
fuente_reinicio = pygame.font.Font("assets//fuentes//fibberish.ttf", 50)
fuente_inicio = pygame.font.Font("assets//fuentes//fibberish.ttf", 50)
fuente_titulo = pygame.font.Font("assets//fuentes//fibberish.ttf", 125)
fuente_victoria = pygame.font.Font("assets//fuentes//fibberish.ttf", 125)

#Importar imágenes
##Tiles
lista_tiles = []
for x in range(constantes.TIPOS_TILES):
    imagen_tile = pygame.image.load(f"assets//images//tiles//{x}.jpg")
    imagen_tile = pygame.transform.scale(imagen_tile, (constantes.TAMAÑO_REJILLA, constantes.TAMAÑO_REJILLA))
    lista_tiles.append(imagen_tile)

## Fortaleza
imagen_fortaleza = pygame.image.load("assets//images//fortaleza//fortaleza.jpg")
imagen_fortaleza = pygame.transform.scale(imagen_fortaleza, (constantes.TAMAÑO_REJILLA * 7, constantes.TAMAÑO_REJILLA * 7))

##Tanques
###Jugador
animaciones = []
for i in range(2):
    img = pygame.image.load("assets//images//tanque//tanque_" + str(i) + ".png")
    img = escalar_img(img, constantes.ESCALA_TANQUE_ANCHO, constantes.ESCALA_TANQUE_ALTO)
    animaciones.append(img)

###Enemigos
directorio_tanques_enemigos = "assets//images//tanques_enemigos//"
tipo_enemigos = sorted(nombre_carpetas(directorio_tanques_enemigos))
animaciones_enemigos = []
for eni in tipo_enemigos:
    lista_temporal = []
    ruta_temporal = f"assets//images//tanques_enemigos//{eni}"
    num_animaciones = contar_elementos(ruta_temporal)
    for i in range(num_animaciones):
        img_tanque_enemigo = pygame.image.load(f"{ruta_temporal}//{eni}_{i+1}.png")
        img_tanque_enemigo = escalar_img(img_tanque_enemigo, constantes.ESCALA_TANQUE_ANCHO, constantes.ESCALA_TANQUE_ALTO)
        lista_temporal.append(img_tanque_enemigo)
    animaciones_enemigos.append(lista_temporal)

###Animacion de muerte
animacion_muerte = []
for i in range(5):
    img = pygame.image.load("assets/images/muerte/explosion_" + str(i+1) + ".png")
    img = escalar_img(img, constantes.ESCALA_TANQUE_ANCHO, constantes.ESCALA_TANQUE_ALTO)
    animacion_muerte.append(img)

imagen_cañon = pygame.Surface((constantes.ANCHO_TANQUE, constantes.ALTO_TANQUE), pygame.SRCALPHA)
imagen_cañon.fill((0, 0, 0, 0))

##Balas
imagen_balas = pygame.image.load("assets//images//cañon//bala.png")
imagen_balas = escalar_img(imagen_balas, constantes.ESCALA_ANCHO_BALA, constantes.ESCALA_ALTO_BALA) 

##Energia
corazon_vacio = pygame.image.load("assets//images//items//corazon_vacio.png")
corazon_vacio = escalar_img(corazon_vacio, constantes.ESCALA_CORAZON, constantes.ESCALA_CORAZON)
corazon_mitad = pygame.image.load("assets//images//items//corazon_mitad.png")
corazon_mitad = escalar_img(corazon_mitad, constantes.ESCALA_CORAZON, constantes.ESCALA_CORAZON)
corazon_completo = pygame.image.load("assets//images//items//corazon_completo.png")
corazon_completo = escalar_img(corazon_completo, constantes.ESCALA_CORAZON, constantes.ESCALA_CORAZON)

##Items
power_up = pygame.image.load("assets//images//items//convencionales//power_up//power_up.png")
power_up = escalar_img(power_up, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
escudo = pygame.image.load("assets//images//items//convencionales//escudo//escudo.png")
escudo = escalar_img(escudo, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
reloj = pygame.image.load("assets//images//items//convencionales//reloj//reloj.png")
reloj = escalar_img(reloj, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
bomba = pygame.image.load("assets//images//items//especiales//bomba//bomba.png")
bomba = escalar_img(bomba, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
escudo_fortaleza = pygame.image.load("assets//images//items//especiales//escudo_fortaleza//escudo_fortaleza.png")
escudo_fortaleza = escalar_img(escudo_fortaleza, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
boost = pygame.image.load("assets//images//items//especiales//boost//boost.png")
boost = escalar_img(boost, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)
vida = pygame.image.load("assets//images//items//especiales//vida//vida.png")
vida = escalar_img(vida, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

###Moneda
imagenes_moneda= []
ruta_moneda_img = "assets//images//items//moneda"
num_moneda_img = contar_elementos(ruta_moneda_img)

for i in range(num_moneda_img):
    img_moneda = pygame.image.load(f"{ruta_moneda_img}//moneda_{i}.png")
    img_moneda = escalar_img(img_moneda, constantes.ESCALA_MONEDA, constantes.ESCALA_MONEDA)
    imagenes_moneda.append(img_moneda)
    
imagenes_items = [
    imagenes_moneda,
    [power_up],
    [escudo],
    [reloj],
    [bomba],
    [escudo_fortaleza],
    [boost],
    [vida]
]

net.start()
net.join("JugadorPygame")
print("[DEBUG] Network started and join requested")

input_seq = 0

data_suelo = []
data_objetos = []

for fila in range(constantes.FILAS):
    fila_suelo = [0] * constantes.COLUMNAS
    data_suelo.append(fila_suelo)
    fila_objetos = [-1] * constantes.COLUMNAS
    data_objetos.append(fila_objetos)
    
with open("niveles//nivel1_suelo.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, fila in enumerate(reader):
        for y, columna in enumerate(fila):
            data_suelo[x][y] = int(columna)

with open("niveles//nivel1_objetos.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, fila in enumerate(reader):
        for y, columna in enumerate(fila):
            data_objetos[x][y] = int(columna)

game_over_text = fuente_game_over.render("Game Over", True, constantes.NEGRO)
texto_boton_reinicio = fuente_reinicio.render("Reiniciar", True, constantes.NEGRO)
texto_boton_reinicio_vic = fuente_reinicio.render("Reiniciar", True, constantes.BLANCO)
texto_boton_jugar = fuente_inicio.render("Jugar", True, constantes.BLANCO)
texto_boton_salir = fuente_inicio.render("Salir", True, constantes.BLANCO)
texto_victoria = fuente_victoria.render("Victoria", True, constantes.BLANCO)
texto_volver_menu = fuente_reinicio.render("Menu Principal", True, constantes.BLANCO)
texto_volver_menu_vic = fuente_reinicio.render("Menu Principal", True, constantes.BLANCO)
texto_siguiente_dificultad = fuente_reinicio.render("Siguiente Dificultad", True, constantes.BLANCO)

boton_reinicio = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 260, constantes.ALTO_VENTANA // 2 + 100, 190, 50)
boton_reinicio_vic = pygame.Rect(constantes.ANCHO_VENTANA / 2 - 90, constantes.ALTO_VENTANA / 2 + 100, 190, 50)

botones_dificultad = []
start_y_dificultad = constantes.ALTO_VENTANA // 2 - 90
for i, dif in enumerate(dificultades):
    rect = pygame.Rect(constantes.ANCHO_VENTANA // 4 - 125, start_y_dificultad + i * 70, 250, 50)
    botones_dificultad.append(rect)

botones_jugadores = []
start_y_jugadores = constantes.ALTO_VENTANA // 2 - 40
for i, jug in enumerate(jugadores):
    rect = pygame.Rect(3 * constantes.ANCHO_VENTANA // 4 - 125, start_y_jugadores + i * 70, 250, 50)
    botones_jugadores.append(rect)

boton_jugar = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 150, constantes.ALTO_VENTANA - 120, 140, 50)
boton_salir = pygame.Rect(constantes.ANCHO_VENTANA // 2 + 10, constantes.ALTO_VENTANA - 120, 140, 50)

boton_volver_menu = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 20, constantes.ALTO_VENTANA // 2 + 100, 295, 50)
boton_volver_menu_vic = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 430, constantes.ALTO_VENTANA // 2 + 100, 295, 50)

boton_crear_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2 + 100, 350, 50)
boton_unirse_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 105, constantes.ALTO_VENTANA // 2, 370, 50)
boton_volver_lobby = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 430, constantes.ALTO_VENTANA // 2 + 100, 295, 50)
boton_iniciar_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2, 390, 50)
boton_refrescar_partidas = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2 + 150, 390, 50)

mover_arriba = False
mover_abajo = False
mover_izquierda = False
mover_derecha = False
pressed = {"up":False, "down":False, "left":False, "right":False, "fire":False}
reloj = pygame.time.Clock()

mostrar_inicio = True

run = True
while run:
    reloj.tick(constantes.FPS)

    if game_state == "MENU_PRINCIPAL":
        pantalla_inicio()
    elif game_state == "LOBBY":
        pantalla_lobby()
    elif game_state == "LISTA_PARTIDAS":
        pantalla_lista_partidas()
    elif game_state == "SALA_ESPERA":
        pantalla_espera_host()
    elif game_state == "EN_JUEGO":
        tiempo_actual = pygame.time.get_ticks()

        if jugadores_seleccionados == 1:
            keys = pygame.key.get_pressed()
            delta_x, delta_y = 0, 0
            if keys[pygame.K_w]: delta_y = -constantes.VELOCIDAD
            elif keys[pygame.K_s]: delta_y = constantes.VELOCIDAD
            elif keys[pygame.K_a]: delta_x = -constantes.VELOCIDAD
            elif keys[pygame.K_d]: delta_x = constantes.VELOCIDAD
            
            if tanques_aliados:
                tanques_aliados[0].movimiento(delta_x, delta_y, mundo.obstaculos_tiles, tanques)
                tanques_aliados[0].update()

            for enemigo in list(tanques_enemigos):
                if not enemigo.update():
                    tanques_enemigos.remove(enemigo)
                    tanques.remove(enemigo)
                    if tanques_aliados: tanques_aliados[0].puntaje += 100
                else:
                    if tanques_aliados:
                        enemigo.actualizar_ia_pixel(tanques_aliados[0], fortaleza, mundo.obstaculos_tiles, tanques, mundo.arbustos, grupo_balas_enemigas)

            if tanques_aliados and tanques_aliados[0].vivo:
                bala = cañon_jugador.update(tanques_aliados[0], 1, False)
                if bala:
                    grupo_balas.add(bala)
            
            for bala in list(grupo_balas):
                enemigo_golpeado = bala.update(tanques_enemigos, mundo.obstaculos_tiles, tiempo_actual < fortaleza_protegida_hasta)
                if enemigo_golpeado:
                    enemigo_golpeado.energia -= bala.daño
                    posicion_daño = enemigo_golpeado.forma.center
                    texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(bala.daño), fuente, constantes.ROJO)
                    grupo_textos_daño.add(texto_daño)

            for bala_enemiga in list(grupo_balas_enemigas):
                jugador_golpeado = bala_enemiga.update(tanques_aliados, mundo.obstaculos_tiles, tiempo_actual < fortaleza_protegida_hasta)
                if jugador_golpeado:
                    jugador_golpeado.energia -= bala_enemiga.daño
                if fortaleza.rect.colliderect(bala_enemiga.rect):
                    fortaleza.energia -= bala_enemiga.daño
                    bala_enemiga.kill()

            if not tanques_enemigos and mundo.tanques_restantes:
                oleada_actual += 1
                nuevos_enemigos = mundo.spawn_enemigos(animaciones_enemigos, cantidad=4)
                for enemigo in nuevos_enemigos:
                    enemigo.animacion_muerte = animacion_muerte
                    enemigo.cañon = Weapon(imagen_cañon, imagen_balas)
                    tanques_enemigos.append(enemigo)
                    tanques.append(enemigo)

        elif jugadores_seleccionados > 1:
            for msg in net.poll():
                if msg["type"] == "snapshot":
                    state = msg["state"]
                    for p_data in state.get("players", []):
                        pid = p_data["id"]
                        if pid == net.player_id:
                            if tanques_aliados:
                                tanques_aliados[0].target_pos = (p_data["x"], p_data["y"])
                                tanques_aliados[0].last_pos = tanques_aliados[0].forma.center
                                tanques_aliados[0].last_update_time = pygame.time.get_ticks()
                                tanques_aliados[0].rotate = p_data.get("rot", 0)
                                tanques_aliados[0].energia = p_data.get("hp", 90)
                                tanques_aliados[0].vidas = p_data.get("vidas", 3)
                                tiempo_actual_servidor = time.time()
                                tanques_aliados[0].escudo_hasta = p_data.get("escudo_hasta", 0)
                                tanques_aliados[0].potenciado_hasta = p_data.get("potenciado_hasta", 0)
                                tanques_aliados[0].boost_hasta = p_data.get("boost_hasta", 0)
                                tanques_aliados[0].boost_activo = tanques_aliados[0].boost_hasta > tiempo_actual_servidor
                                tanques_aliados[0].escudo_activo = tanques_aliados[0].escudo_hasta > tiempo_actual_servidor
                                tanques_aliados[0].potenciado_activo = tanques_aliados[0].potenciado_hasta > tiempo_actual_servidor
                                tanques_aliados[0].update()
                        else:
                            if pid not in remote_players:
                                ghost = Tanque(p_data["x"], p_data["y"], animaciones, 90, 0, 0, 0)
                                remote_players[pid] = ghost
                            else:
                                ghost = remote_players[pid]
                            ghost.target_pos = (p_data["x"], p_data["y"])
                            ghost.last_pos = ghost.forma.center
                            ghost.last_update_time = pygame.time.get_ticks()
                            ghost.rotate = p_data.get("rot", 0)
                            ghost.energia = p_data.get("hp", 90)
                            ghost.vidas = p_data.get("vidas", 3)
                            ghost.update()
                        fortaleza.energia = state.get("fortress_hp", fortaleza.energia)
                        reloj_activo_remoto = state.get("reloj_activo", False)
                        fortaleza_protegida_hasta = state.get("fortaleza_escudo_hasta", 0)
                    
                    if "obstaculos" in state:
                        mundo.obstaculos_tiles = []
                        for o in state["obstaculos"]:
                            vida = o["vida"]
                            rect = pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                            # Podés usar la imagen correspondiente según vida o tipo
                            if vida > 0:
                                imagen_tile = lista_tiles[4]  # muro destruible
                            else:
                                imagen_tile = lista_tiles[5]  # muro no destruible
                            mundo.obstaculos_tiles.append((imagen_tile, rect, rect.centerx, rect.centery, vida))
                        
                    balas_actuales = state.get("bullets", [])
                    ids_balas_en_servidor = {b["id"] for b in balas_actuales}
                    
                    for bullet_data in balas_actuales:
                        bid = bullet_data["id"]
                        if bid not in remote_bullets:
                            bala_fantasma = pygame.sprite.Sprite()
                            bala_fantasma.image = imagen_balas
                            bala_fantasma.rect = bala_fantasma.image.get_rect()
                            remote_bullets[bid] = bala_fantasma
                        
                        remote_bullets[bid].rect.center = (bullet_data["x"], bullet_data["y"])
                        
                    for bid in list(remote_bullets.keys()):
                        if bid not in ids_balas_en_servidor:
                            del remote_bullets[bid]
                    items_actuales = state.get("items", [])
                    ids_items_en_servidor = {i["id"] for i in items_actuales}

                    for item_data in items_actuales:
                        iid = item_data["id"]
                        if iid not in remote_items:
                            item_fantasma = pygame.sprite.Sprite()
                            tipo_item = item_data["tipo"]
                            item_fantasma.image = imagenes_items[tipo_item][0] 
                            item_fantasma.rect = item_fantasma.image.get_rect()
                            remote_items[iid] = item_fantasma

                        remote_items[iid].rect.center = (item_data["x"], item_data["y"])

                    for iid in list(remote_items.keys()):
                        if iid not in ids_items_en_servidor:
                            del remote_items[iid]
        
                    enemigos_actuales = state.get("enemies", [])
                    ids_enemigos_en_servidor = {e["id"] for e in enemigos_actuales}

                    for enemy_data in enemigos_actuales:
                        eid = enemy_data["id"]
                        if eid not in remote_enemies:
                            tipo = enemy_data["tipo"]
                            ghost_enemy = Tanque(enemy_data["x"], enemy_data["y"], animaciones_enemigos[tipo-1], 100, tipo, 0, 0)
                            remote_enemies[eid] = ghost_enemy
                        else:
                            ghost_enemy = remote_enemies[eid]
                        
                        ghost_enemy.target_pos = (enemy_data["x"], enemy_data["y"])
                        ghost_enemy.last_pos = ghost_enemy.forma.center
                        ghost_enemy.last_update_time = pygame.time.get_ticks()
                        ghost_enemy.rotate = enemy_data.get("rot", 0)
                        ghost_enemy.energia = enemy_data.get("hp", 100)
                        ghost_enemy.update()

                    for eid in list(remote_enemies.keys()):
                        if eid not in ids_enemigos_en_servidor:
                            del remote_enemies[eid]
                            
                    fortaleza.energia = state.get("fortress_hp", fortaleza.energia)
            
            input_seq += 1
            net.send_input(input_seq, pressed)

        if jugadores_seleccionados > 1:
            if tanques_aliados: tanques_aliados[0].interpolate_position()
            for ghost in remote_players.values(): ghost.interpolate_position()
            for ghost_enemy in remote_enemies.values(): ghost_enemy.interpolate_position()

        posicion_pantalla = [0, 0]
        if tanques_aliados:
            cam_x = tanques_aliados[0].forma.centerx - constantes.ANCHO_VENTANA / 2
            cam_y = tanques_aliados[0].forma.centery - constantes.ALTO_VENTANA / 2
            cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
            cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))
            posicion_pantalla = [cam_x, cam_y]

        pantalla.fill(constantes.COLOR_BG)
        mundo.dibujar(pantalla, posicion_pantalla)
        fortaleza.dibujar(pantalla, posicion_pantalla)
        
        if jugadores_seleccionados == 1:
            for enemigo in tanques_enemigos:
                enemigo.dibujar(pantalla, posicion_pantalla)
        else:
            for ghost_enemy in remote_enemies.values():
                ghost_enemy.dibujar(pantalla, posicion_pantalla)

        for jugador in tanques_aliados:
            jugador.dibujar(pantalla, posicion_pantalla)
        for ghost in remote_players.values():
            ghost.dibujar(pantalla, posicion_pantalla)

        for bala in grupo_balas: bala.dibujar(pantalla, posicion_pantalla)
        
        for bala_enemiga in grupo_balas_enemigas: bala_enemiga.dibujar(pantalla, posicion_pantalla)
        
        for bala in remote_bullets.values():
            pantalla.blit(bala.image, (bala.rect.x - posicion_pantalla[0], bala.rect.y - posicion_pantalla[1]))
        for texto in grupo_textos_daño:
            pantalla.blit(texto.image, (texto.rect.x - posicion_pantalla[0], texto.rect.y - posicion_pantalla[1]))
        
        for item in remote_items.values():
            pantalla.blit(item.image, (item.rect.x - posicion_pantalla[0], item.rect.y - posicion_pantalla[1]))
    
        todos_los_jugadores_visibles = list(tanques_aliados) + list(remote_players.values())
        for arbusto_img, arbusto_rect in mundo.arbustos:
            dentro = any(arbusto_rect.colliderect(j.forma) for j in todos_los_jugadores_visibles)
            temp_img = arbusto_img.copy()
            if dentro:
                temp_img.set_alpha(150)
            pantalla.blit(temp_img, (arbusto_rect.x - cam_x, arbusto_rect.y - cam_y))
                    
        
        if tanques_aliados:
            vida_jugador(tanques_aliados[0])
            dibujar_texto(f"Puntaje: {tanques_aliados[0].puntaje}", fuente, constantes.AZUL_CIELO_VIVO, constantes.ANCHO_VENTANA - 190, 50)
            dibujar_hud_bonus(tanques_aliados[0], fortaleza_protegida_hasta, reloj_activo_remoto)
            vidas_p1 = tanques_aliados[0].vidas 
            dibujar_texto(f"Vidas P1: {vidas_p1}", fuente, constantes.BLANCO, 10, 50)
        
        for ghost in remote_players.values():
            vidas_p2 = ghost.vidas
            dibujar_texto(f"Vidas P2: {vidas_p2}", fuente, constantes.BLANCO, 10, 80)
        
        tiempo_transcurrido = (pygame.time.get_ticks() - tiempo_inicio_partida) // 1000
        minutos, segundos = divmod(tiempo_transcurrido, 60)
        texto_tiempo = f"{minutos:02}:{segundos:02}"
        dibujar_texto(texto_tiempo, fuente, constantes.BLANCO, constantes.ANCHO_VENTANA / 2 - 40, 10)
        
        if jugadores_seleccionados == 1:
            total_enemigos_restantes = len(tanques_enemigos) + len(mundo.tanques_restantes)
        else:
            total_enemigos_restantes = len(remote_enemies)
        
        dibujar_texto(f"Oleada: {oleada_actual}", fuente, constantes.BLANCO, constantes.ANCHO_VENTANA - 180, 20)
        
        aliados_vivos = sum(1 for t in tanques_aliados if t.vivo) + sum(1 for g in remote_players.values() if g.energia > 0)
        dibujar_texto(f"Enemigos Restantes: {total_enemigos_restantes}", fuente, constantes.ROJO, constantes.ANCHO_VENTANA / 2 - 150, 40)
        dibujar_texto(f"Aliados Restantes: {aliados_vivos}", fuente, constantes.VERDE, constantes.ANCHO_VENTANA / 2 - 150, 70)

        aliados_vivos_count = sum(1 for t in tanques_aliados if t.vivo)
        if jugadores_seleccionados > 1:
            aliados_vivos_count += sum(1 for g in remote_players.values() if g.energia > 0)

        if fortaleza.energia <= 0 or aliados_vivos_count == 0:
            game_state = "GAME_OVER"

        condicion_victoria = False
        if jugadores_seleccionados == 1:
            if not tanques_enemigos and not mundo.tanques_restantes:
                condicion_victoria = True
        else: 
            pass

        if condicion_victoria:
            game_state = "VICTORIA"
            
    elif game_state == "GAME_OVER":
        pantalla.fill(constantes.ROJO_OSCURO)
        dibujar_texto("Game Over", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA/4, constantes.ALTO_VENTANA/4)
        dibujar_boton_retro("Reiniciar", boton_reinicio)
        dibujar_boton_retro("Menu Principal", boton_volver_menu)
        if jugadores_seleccionados == 2:
            texto1 = "LISTO" if jugador1_listo else "Esperando..."
            texto2 = "LISTO" if jugador2_listo else "Esperando..."
            dibujar_texto(f"Jugador 1: {texto1}", fuente, constantes.BLANCO, boton_reinicio.x, boton_reinicio.y + 60)
            dibujar_texto(f"Jugador 2: {texto2}", fuente, constantes.BLANCO, boton_volver_menu.x, boton_volver_menu.y + 60)

    elif game_state == "VICTORIA":
        pantalla.fill(constantes.VERDE_OSCURO)
        dibujar_texto("Victoria", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA/3, constantes.ALTO_VENTANA/4)
        dibujar_boton_retro("Reiniciar", boton_reinicio_vic)
        if jugadores_seleccionados == 2:
            texto1 = "LISTO" if jugador1_listo else "Esperando..."
            texto2 = "LISTO" if jugador2_listo else "Esperando..."
            dibujar_texto(f"J1: {texto1}", fuente, constantes.BLANCO, boton_reinicio_vic.x, boton_reinicio_vic.y + 60)
    
    for msg in net.poll():
        tipo_mensaje = msg.get("type")
        if tipo_mensaje == "actualizar_lista_partidas":
            partidas_disponibles = msg.get("partidas", {})
        elif tipo_mensaje in ["partida_creada", "actualizacion_partida"]:
            mi_partida_actual = msg.get("partida", {})
            game_state = "SALA_ESPERA"
        elif tipo_mensaje == "iniciar_juego":
            partida_info = msg.get("partida", {})
            mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = iniciar_partida(partida_info["dificultad"], 2)
            game_state = "EN_JUEGO"
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if game_state == "EN_JUEGO":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: pressed["up"] = True
                if event.key == pygame.K_s: pressed["down"] = True
                if event.key == pygame.K_a: pressed["left"] = True
                if event.key == pygame.K_d: pressed["right"] = True
                if event.key == pygame.K_SPACE: 
                    pressed["fire"] = True
                    if jugadores_seleccionados > 1:
                        net.solicitar_disparo()
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w: pressed["up"] = False
                if event.key == pygame.K_s: pressed["down"] = False
                if event.key == pygame.K_a: pressed["left"] = False
                if event.key == pygame.K_d: pressed["right"] = False
                if event.key == pygame.K_SPACE: pressed["fire"] = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos_mouse = event.pos
            
            if game_state == "MENU_PRINCIPAL":
                if boton_jugar.collidepoint(pos_mouse) and dificultad_seleccionada:
                    if jugadores_seleccionados == 1:
                        mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = iniciar_partida(dificultad_seleccionada, 1)
                        tiempo_inicio_partida = pygame.time.get_ticks()
                        game_state = "EN_JUEGO"
                    else:
                        game_state = "LOBBY"
                elif boton_salir.collidepoint(pos_mouse):
                    run = False
                for i, rect in enumerate(botones_dificultad):
                    if rect.collidepoint(pos_mouse):
                        dificultad_seleccionada = dificultades[i]
                for i, rect in enumerate(botones_jugadores):
                    if rect.collidepoint(pos_mouse):
                        jugadores_seleccionados = i + 1

            elif game_state == "LOBBY":
                if boton_crear_partida.collidepoint(pos_mouse):
                    mundo_temporal = Mundo()
                    mundo_temporal.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad_seleccionada, 2)
                    
                    px1, py1 = mundo_temporal.posicion_spawn_jugador
                    px2, py2 = mundo_temporal.posicion_spawn_jugador2
                    spawn1_coords = (px1 * constantes.TAMAÑO_REJILLA + 16, py1 * constantes.TAMAÑO_REJILLA + 16)
                    spawn2_coords = (px2 * constantes.TAMAÑO_REJILLA + 16, py2 * constantes.TAMAÑO_REJILLA + 16)

                    lista_obstaculos = []
                    for obs in mundo_temporal.obstaculos_tiles:
                        rect = obs[1]
                        visa = obs[4]
                        lista_obstaculos.append([rect.x, rect.y, rect.width, rect.height])

                    lista_enemigos_del_nivel = mundo_temporal.tanques_restantes
                    puntos_spawn_enemigos = mundo_temporal.posiciones_spawn_enemigos

                    net.crear_partida(
                        f"Partida de {random.randint(100,999)}", 
                        dificultad_seleccionada, 
                        spawn1_coords, 
                        spawn2_coords, 
                        lista_obstaculos,
                        lista_enemigos_del_nivel,
                        puntos_spawn_enemigos
                    )
                elif boton_unirse_partida.collidepoint(pos_mouse):
                    net.pedir_lista_partidas()
                    game_state = "LISTA_PARTIDAS"
                elif boton_volver_lobby.collidepoint(pos_mouse):
                    game_state = "MENU_PRINCIPAL"

            elif game_state == "SALA_ESPERA":
                if mi_partida_actual.get("host") == net.player_id and boton_iniciar_partida.collidepoint(pos_mouse):
                    net.iniciar_juego(mi_partida_actual.get("id"))
                    
            elif game_state == "LISTA_PARTIDAS":
                if boton_volver_lobby.collidepoint(pos_mouse):
                    game_state = "LOBBY"
                if boton_refrescar_partidas.collidepoint(pos_mouse):
                    net.pedir_lista_partidas()
                for id_partida, rect in botones_partidas:
                    if rect.collidepoint(pos_mouse):
                        net.unirse_a_partida(id_partida)
                        
            elif game_state in ["GAME_OVER", "VICTORIA"]:
                if boton_volver_menu.collidepoint(pos_mouse) or boton_volver_menu_vic.collidepoint(pos_mouse):
                    game_state = "MENU_PRINCIPAL"

                if (game_state == "GAME_OVER" and boton_reinicio.collidepoint(pos_mouse)) or \
                   (game_state == "VICTORIA" and boton_reinicio_vic.collidepoint(pos_mouse)):
                    
                    if jugadores_seleccionados == 1:
                        mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = resetear_mundo()
                        game_state = "EN_JUEGO"
                    else: 
                        jugador1_listo = not jugador1_listo
                        jugador2_listo = True
                        if jugador1_listo and jugador2_listo:
                            mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = resetear_mundo()
                            game_state = "EN_JUEGO"

    pygame.display.update()

net.stop()
pygame.quit()
