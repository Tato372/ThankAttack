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

pygame.init()

game_state = "MENU_PRINCIPAL" # "MENU_PRINCIPAL", "LOBBY", "EN_JUEGO", "GAME_OVER", "VICTORIA"
partidas_disponibles = {} # NUEVO: para guardar la lista de partidas del servidor
mi_partida_actual = {} # NUEVO: para guardar la info de la partida a la que me uní
remote_players = {}
remote_enemies = {} 
botones_partidas = []
# NUEVO: Variables para el lobby y multijugador local simulado
info_partida = {
    "nombre": "",
    "dificultad": "Facil",
    "host": "jugador1",
    "cliente": None, # Se asignará a "jugador2" cuando se una
    "estado": "ESPERANDO" # "ESPERANDO", "LISTO"
}
# Banderas para la pantalla de fin de partida
jugador1_listo = False
jugador2_listo = False

net = NetworkManager("ws://172.24.82.196:8000/ws")

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
    
    # Simplemente llamamos a iniciar_partida con la misma configuración
    return iniciar_partida(dificultad_seleccionada, jugadores_seleccionados)

# main.py

def iniciar_partida(dificultad, num_jugadores):
    """Crea y devuelve todos los objetos necesarios para una nueva partida."""
    # Limpiar listas y grupos de sprites
    tanques.clear()
    tanques_enemigos.clear()
    remote_enemies.clear()
    remote_players.clear()
    grupo_balas.empty()
    grupo_balas_enemigas.empty()
    grupo_textos_daño.empty()
    grupo_items.empty()

    mundo = Mundo()
    
    # --- CORRECCIÓN CLAVE ---
    # Solo procesamos el mundo y creamos enemigos localmente si es 1 JUGADOR
    if num_jugadores == 1:
        mundo.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad, num_jugadores)
        # Añadimos los enemigos locales a la lista de tanques para colisiones
        for enemigo in mundo.lista_enemigos:
            tanques.append(enemigo)
            tanques_enemigos.append(enemigo)
    
    # El cliente SIEMPRE crea su propio tanque
    tanques_aliados = []
    px1, py1 = mundo.posicion_spawn_jugador if num_jugadores == 1 else (5, 5) # Coords temporales para MP
    tanque_jugador1 = Tanque(
        px1 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        py1 * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        animaciones, 90, 0, constantes.VELOCIDAD, constantes.DISPARO_COOLDOWN
    )
    tanque_jugador1.id_red = mi_id_de_red
    tanques.append(tanque_jugador1)
    tanques_aliados.append(tanque_jugador1)
    
    cañon_jugador = Weapon(imagen_cañon, imagen_balas)

    # La fortaleza se crea siempre, pero sus datos vendrán del servidor en MP
    fx, fy = mundo.posicion_fortaleza if num_jugadores == 1 else (25, 45) # Coords temporales
    fortaleza = Fortaleza(
        fx * constantes.TAMAÑO_REJILLA,
        fy * constantes.TAMAÑO_REJILLA,
        imagen_fortaleza
    )
    
    muros_originales = {} # Esta lógica puede necesitar revisión para MP, pero por ahora está bien

    return mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales
# NUEVO: Pantalla para elegir entre crear o unirse
def pantalla_lobby():
    pantalla.fill(constantes.COLOR_FONDO)
    dibujar_texto("MODO DOS JUGADORES", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA / 4 - 100, 100)
    dibujar_boton_retro("Crear Partida", boton_crear_partida)
    dibujar_boton_retro("Unirse a Partida", boton_unirse_partida)
    dibujar_boton_retro("Volver", boton_volver_lobby)
    pygame.display.update()

# NUEVO: Pantalla de espera del Host
def pantalla_espera_host():
    pantalla.fill(constantes.COLOR_FONDO)
    
    # CORREGIDO: Usar 'mi_partida_actual' que contiene los datos del servidor
    nombre_partida = mi_partida_actual.get("nombre", "Cargando...")
    dificultad_partida = mi_partida_actual.get("dificultad", "")
    
    dibujar_texto(f"Partida: {nombre_partida}", fuente_inicio, constantes.BLANCO, 100, 100)
    dibujar_texto(f"Dificultad: {dificultad_partida}", fuente_inicio, constantes.BLANCO, 100, 160)
    
    # Comprobar si el cliente ya se unió (revisando si la llave 'cliente' tiene un valor)
    if mi_partida_actual.get("cliente"):
        dibujar_texto("¡Jugador 2 se ha unido!", fuente_titulo, constantes.VERDE, constantes.ANCHO_VENTANA / 4 - 200, 300)
        
        # CORREGIDO: Solo el host puede ver y presionar el botón de "Iniciar Partida"
        if mi_partida_actual.get("host") == net.player_id:
            dibujar_boton_retro("Iniciar Partida", boton_iniciar_partida)
    else:
        dibujar_texto("Esperando al Jugador 2...", fuente_titulo, constantes.AMARILLO, constantes.ANCHO_VENTANA / 4 - 150, 300)

    dibujar_boton_retro("Cancelar", boton_volver_lobby) # 'Cancelar' te llevará de vuelta al menú

# (Simularemos la pantalla de "unirse" con una lógica simple por ahora)

##Funcione para agregar y quitar la dificultad pesadilla si son 2 jugadores
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

##Funcion para mostrar la pantalla de inicio
def pantalla_inicio():
    #Cargar y escalar la imagen de inicio
    inicio_image = pygame.image.load("assets//images//pantallas//pantalla_inicio.png")
    inicio_image = escalar_img(inicio_image, constantes.ANCHO_VENTANA / inicio_image.get_width(), constantes.ALTO_VENTANA / inicio_image.get_height())
    pantalla.blit(inicio_image, (0, 0))
    #Dibujar el texto del titulo
    dibujar_texto("TANK ATTACK", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA / 4, constantes.ALTO_VENTANA / 4 - 100)
    #Dibujar selector
    # --- Selector de jugadores ---
    dibujar_texto("Jugadores:", fuente_inicio, constantes.BLANCO, botones_jugadores[0].x, botones_jugadores[0].y - 50)
    for i, rect in enumerate(botones_jugadores):
        color = constantes.VERDE if jugadores_seleccionados == i + 1 else constantes.BLANCO
        pygame.draw.rect(pantalla, color, rect, 3)  # Borde
        dibujar_texto(jugadores[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
    # --- Selector de dificultad ---
    dibujar_texto("Dificultad:", fuente_inicio, constantes.BLANCO, botones_dificultad[0].x, botones_dificultad[0].y - 50)
    if jugadores_seleccionados == 2:
        agregar_dificultad_pesadilla()
        for i, rect in enumerate(botones_dificultad):
            color = constantes.VERDE if dificultad_seleccionada == dificultades[i] else constantes.BLANCO
            pygame.draw.rect(pantalla, color, rect, 3)  # Borde
            dibujar_texto(dificultades[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
    else:
        quitar_dificultad_pesadilla()
        for i, rect in enumerate(botones_dificultad):
            color = constantes.VERDE if dificultad_seleccionada == dificultades[i] else constantes.BLANCO
            pygame.draw.rect(pantalla, color, rect, 3)  # Borde
            dibujar_texto(dificultades[i], fuente_botones, constantes.BLANCO, rect.x + 10, rect.y + 10)
        
    #Dibujar el boton de jugar
    dibujar_boton_retro("Jugar", boton_jugar)
    #Dibujar el boton de salir
    dibujar_boton_retro("Salir", boton_salir)
    
    pygame.display.update()

# <-- CAMBIO: Nueva función para mostrar el HUD de los bonus -->
def dibujar_hud_bonus(tanque, fortaleza_protegida_hasta):
    tiempo_actual = pygame.time.get_ticks()
    y_pos = 120
    
    if tanque.escudo_activo:
        tiempo_restante = (tanque.escudo_tiempo_final - tiempo_actual) // 1000
        dibujar_texto(f"Escudo: {tiempo_restante}s", fuente, constantes.AZUL_CIELO_VIVO, 10, y_pos)
        y_pos += 30
    if tanque.potenciado_activo:
        tiempo_restante = (tanque.potenciado_tiempo_final - tiempo_actual) // 1000
        dibujar_texto(f"Doble Daño: {tiempo_restante}s", fuente, constantes.ROJO, 10, y_pos)
        y_pos += 30
    if tanque.boost_activo:
        tiempo_restante = (tanque.boost_tiempo_final - tiempo_actual) // 1000
        dibujar_texto(f"Boost: {tiempo_restante}s", fuente, constantes.AMARILLO, 10, y_pos)
        y_pos += 30
    if fortaleza_protegida_hasta > tiempo_actual:
        tiempo_restante = (fortaleza_protegida_hasta - tiempo_actual) // 1000
        dibujar_texto(f"Escudo Fortaleza: {tiempo_restante}s", fuente, constantes.GRIS, 10, y_pos)
        y_pos += 30
    
#Variables
nivel = 1
oleada_actual = 1
tanques = []
vidas_jugador = 3
muros_originales = {}
tiempo_inicio_partida = 0
mi_id_de_red = None
# <-- CAMBIO: Variables para la generación de bonus -->
ultimo_spawn_convencional = pygame.time.get_ticks()
ultimo_spawn_especial = pygame.time.get_ticks()
fortaleza_protegida_hasta = 0

dificultades = ["Facil", "Intermedio", "Dificil"]
dificultad_actual = 0  # índice de la dificultad seleccionada

jugadores = ["Un Jugador", "Dos Jugadores"]
jugadores_actual = 0 

# Selección inicial (ninguna)
dificultad_seleccionada = "Facil"  # puede ser "Facil", "Intermedio", "Dificil"
jugadores_seleccionados = 1  # puede ser "Un Jugador" o "Dos Jugadores"

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
imagen_fortaleza = pygame.image.load("assets//images//fortaleza//fortaleza.jpg") # Asegúrate que la ruta sea correcta
imagen_fortaleza = pygame.transform.scale(imagen_fortaleza, (constantes.TAMAÑO_REJILLA * 7, constantes.TAMAÑO_REJILLA * 7)) # Hacemos que ocupe 5x5 tiles

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

##Cargar una imagen transparente en lugar del arma visible
imagen_cañon = pygame.Surface((constantes.ANCHO_TANQUE, constantes.ALTO_TANQUE), pygame.SRCALPHA)
##Rellenar con transparencia completa
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
###Convencionales
####Power up
power_up = pygame.image.load("assets//images//items//convencionales//power_up//power_up.png")
power_up = escalar_img(power_up, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

####Escudo
escudo = pygame.image.load("assets//images//items//convencionales//escudo//escudo.png")
escudo = escalar_img(escudo, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

####Reloj
reloj = pygame.image.load("assets//images//items//convencionales//reloj//reloj.png")
reloj = escalar_img(reloj, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

###Especiales
####Bomba
bomba = pygame.image.load("assets//images//items//especiales//bomba//bomba.png")
bomba = escalar_img(bomba, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

####Escudo para la fortaleza
escudo_fortaleza = pygame.image.load("assets//images//items//especiales//escudo_fortaleza//escudo_fortaleza.png")
escudo_fortaleza = escalar_img(escudo_fortaleza, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

####Boost
boost = pygame.image.load("assets//images//items//especiales//boost//boost.png")
boost = escalar_img(boost, constantes.ESCALA_BONUS, constantes.ESCALA_BONUS)

####Vida
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
    imagenes_moneda,          # 0: Moneda
    [power_up],               # 1: Disparo Potenciado
    [escudo],                 # 2: Escudo
    [reloj],                  # 3: Reloj
    [bomba],                  # 4: Bomba
    [escudo_fortaleza],       # 5: Escudo Fortaleza
    [boost],                  # 6: Boost
    [vida]                    # 7: Vida
]

# Iniciar red después de cargar recursos para evitar que lleguen snapshots antes de que
# las animaciones/recursos estén listos (condición de carrera).
net.start()
net.join("JugadorPygame")
print("[DEBUG] Network started and join requested")

# Secuencia de inputs del cliente
input_seq = 0

#Lista que representa y almacena los datos del mundo
data_suelo = []
data_objetos = []

for fila in range(constantes.FILAS):
    # suelo: por defecto tile 0 (ej. 1075)
    fila_suelo = [0] * constantes.COLUMNAS
    data_suelo.append(fila_suelo)

    # objetos: por defecto 0 (sin objeto)
    fila_objetos = [-1] * constantes.COLUMNAS
    data_objetos.append(fila_objetos)
    
##Cargar los archivos con el nivel
# suelo
with open("niveles//nivel1_suelo.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, fila in enumerate(reader):
        for y, columna in enumerate(fila):
            data_suelo[x][y] = int(columna)

# objetos
with open("niveles//nivel1_objetos.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, fila in enumerate(reader):
        for y, columna in enumerate(fila):
            data_objetos[x][y] = int(columna)

#Crear textos
##Texto de game over
game_over_text = fuente_game_over.render("Game Over", True, constantes.NEGRO)
##Texto del boton de reincio
texto_boton_reinicio = fuente_reinicio.render("Reiniciar", True, constantes.NEGRO)
texto_boton_reinicio_vic = fuente_reinicio.render("Reiniciar", True, constantes.BLANCO)
##Texto de los botones de inicio
texto_boton_jugar = fuente_inicio.render("Jugar", True, constantes.BLANCO)
texto_boton_salir = fuente_inicio.render("Salir", True, constantes.BLANCO)
##Texto de victoria
texto_victoria = fuente_victoria.render("Victoria", True, constantes.BLANCO)
##Texto del boton volver al menú principal
texto_volver_menu = fuente_reinicio.render("Menu Principal", True, constantes.BLANCO)
texto_volver_menu_vic = fuente_reinicio.render("Menu Principal", True, constantes.BLANCO)
##Texto del boton de siguiente dificultad
texto_siguiente_dificultad = fuente_reinicio.render("Siguiente Dificultad", True, constantes.BLANCO)

# Crear botones
## Botón de reinicio en el game over
boton_reinicio = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 260, constantes.ALTO_VENTANA // 2 + 100, 190, 50)
## Botón de reinicio en la victoria
boton_reinicio_vic = pygame.Rect(constantes.ANCHO_VENTANA / 2 - 90, constantes.ALTO_VENTANA / 2 + 100, 190, 50)

## Botones del selector de dificultad
botones_dificultad = []
start_y_dificultad = constantes.ALTO_VENTANA // 2 - 90  # empieza más arriba
for i, dif in enumerate(dificultades):
    rect = pygame.Rect(constantes.ANCHO_VENTANA // 4 - 125, start_y_dificultad + i * 70, 250, 50)
    botones_dificultad.append(rect)

## Botones del selector de jugadores
botones_jugadores = []
start_y_jugadores = constantes.ALTO_VENTANA // 2 - 40
for i, jug in enumerate(jugadores):
    rect = pygame.Rect(3 * constantes.ANCHO_VENTANA // 4 - 125, start_y_jugadores + i * 70, 250, 50)
    botones_jugadores.append(rect)

## Botones de jugar y salir (abajo)
boton_jugar = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 150, constantes.ALTO_VENTANA - 120, 140, 50)
boton_salir = pygame.Rect(constantes.ANCHO_VENTANA // 2 + 10, constantes.ALTO_VENTANA - 120, 140, 50)

##Botones de volver al menú principal
boton_volver_menu = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 20, constantes.ALTO_VENTANA // 2 + 100, 295, 50)
boton_volver_menu_vic = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 430, constantes.ALTO_VENTANA // 2 + 100, 295, 50)

##Boton crear partida, unirse partida
boton_crear_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2 + 100, 350, 50)
boton_unirse_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 105, constantes.ALTO_VENTANA // 2, 370, 50)
##Boton volver lobby
boton_volver_lobby = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 430, constantes.ALTO_VENTANA // 2 + 100, 295, 50)
##Boton iniciar partida
boton_iniciar_partida = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2, 390, 50)

boton_refrescar_partidas = pygame.Rect(constantes.ANCHO_VENTANA // 2 - 90, constantes.ALTO_VENTANA // 2 + 150, 390, 50)

#Definir variables de movimiento del tanque
mover_arriba = False
mover_abajo = False
mover_izquierda = False
mover_derecha = False
pressed = {"up":False, "down":False, "left":False, "right":False, "fire":False}
#Controlar framerate
reloj = pygame.time.Clock()

mostrar_inicio = True

run = True
while run:
    # 1. Controlar el framerate
    reloj.tick(constantes.FPS)

    # ==================================================================
    # SECCIÓN DE ESTADOS: DIBUJO Y LÓGICA PRINCIPAL DE CADA PANTALLA
    # ==================================================================

    if game_state == "MENU_PRINCIPAL":
        pantalla_inicio()
    elif game_state == "LOBBY":
        pantalla_lobby()
    elif game_state == "LISTA_PARTIDAS":
        pantalla_lista_partidas()
    elif game_state == "SALA_ESPERA":
        # Usamos la misma función de antes, pero con datos del servidor
        pantalla_espera_host() # Asegúrate que esta función ahora use 'mi_partida_actual'
    elif game_state == "EN_JUEGO":
         # --- LÓGICA DE ACTUALIZACIÓN ---

        # PASO 1: SEPARAMOS LA LÓGICA DE MOVIMIENTO PARA 1 JUGADOR Y MULTIJUGADOR
        if jugadores_seleccionados == 1:
            # ============================================
            # LÓGICA PARA 1 JUGADOR (TODO ES LOCAL)
            # ============================================
            keys = pygame.key.get_pressed()
            delta_x, delta_y = 0, 0
            if keys[pygame.K_w]: delta_y = -constantes.VELOCIDAD
            elif keys[pygame.K_s]: delta_y = constantes.VELOCIDAD
            elif keys[pygame.K_a]: delta_x = -constantes.VELOCIDAD
            elif keys[pygame.K_d]: delta_x = constantes.VELOCIDAD
            
            if tanques_aliados:
                # El jugador se mueve y colisiona con todo localmente
                tanques_aliados[0].movimiento(delta_x, delta_y, mundo.obstaculos_tiles, tanques)
                tanques_aliados[0].update()

        elif jugadores_seleccionados > 1:
            # ============================================
            # LÓGICA PARA MULTIJUGADOR (EL SERVIDOR MANDA)
            # ============================================
            # Procesar los snapshots del servidor es lo PRIMERO, para tener la posición más actualizada
            for msg in net.poll():
                if msg["type"] == "snapshot":
                    state = msg["state"]
                    for p_data in state["players"]:
                        pid = p_data["id"]
                        if pid == net.player_id:
                            tanques_aliados[0].forma.centerx = p_data["x"]
                            tanques_aliados[0].forma.centery = p_data["y"]
                            tanques_aliados[0].rotate = p_data.get("rot", 0)
                            tanques_aliados[0].update()
                            tanques_aliados[0].energia = p_data.get("hp", 90)
                            tanques_aliados[0].vidas = p_data.get("vidas", 3)
                        else:
                            if pid not in remote_players:
                                ghost = Tanque(p_data["x"], p_data["y"], animaciones, 90, 0, 0, 0)
                                remote_players[pid] = ghost
                            else:
                                ghost = remote_players[pid]
                                ghost.last_pos = ghost.forma.center
                                ghost.target_pos = (p_data["x"], p_data["y"])
                                ghost.last_update_time = pygame.time.get_ticks()
                                ghost.rotate = p_data.get("rot", 0)
                                tanques_aliados[0].energia = p_data.get("hp", 90)
                                ghost.vidas = p_data.get("vidas", 3)
                    
                    # NUEVO: Actualizar enemigos desde el servidor
                    enemigos_actuales = state.get("enemies", [])
                    ids_enemigos_en_servidor = {e["id"] for e in enemigos_actuales}

                    # Crear/actualizar enemigos que llegan del servidor
                    for enemy_data in enemigos_actuales:
                        eid = enemy_data["id"]
                        if eid not in remote_enemies:
                            # Creamos un "fantasma" de enemigo
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
                        ghost_enemy.update() # Para que se anime el sprite

                    # Limpiar enemigos que ya no existen en el servidor
                    for eid in list(remote_enemies.keys()):
                        if eid not in ids_enemigos_en_servidor:
                            del remote_enemies[eid]
                                
                    fortaleza.energia = state.get("fortress_hp", fortaleza.energia)

            input_seq += 1
            net.send_input(input_seq, pressed)

            # ESTA ES LA LÍNEA QUE TE PEDÍ AÑADIR (2.B)
            # Corrección de colisión local contra enemigos y aliados
            if tanques_aliados:
                # Pasamos una lista de obstáculos vacía ([]) para que solo revise colisiones con otros tanques.
                tanques_para_colision = tanques_enemigos + list(remote_players.values())
                tanques_aliados[0].movimiento(0, 0, [], tanques_para_colision)

        # ==============================================================
        # EL RESTO DE LA LÓGICA ES COMÚN PARA AMBOS MODOS DE JUEGO
        # ==============================================================
        for ghost in remote_players.values(): ghost.interpolate_position()
        for ghost_enemy in remote_enemies.values(): ghost_enemy.interpolate_position()
        
        # El cálculo de la cámara va aquí, DESPUÉS de que el jugador tiene su posición final
        posicion_pantalla = [0, 0]
        if tanques_aliados:
            cam_x = tanques_aliados[0].forma.centerx - constantes.ANCHO_VENTANA / 2
            cam_y = tanques_aliados[0].forma.centery - constantes.ALTO_VENTANA / 2
            cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
            cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))
            posicion_pantalla = [cam_x, cam_y]

        # Interpolar la posición de los jugadores remotos para suavizar el movimiento
        for ghost in remote_players.values():
            ghost.interpolate_position()

        # Actualizar tanques enemigos, balas, items y otros
        if any(j.vivo for j in tanques_aliados):
            # Lógica de red (enviar inputs, recibir snapshots)
            # (Se envía solo el input del jugador 1 por ahora)
            input_seq += 1
            net.send_input(input_seq, pressed)
            
            # Procesar mensajes del servidor
            for msg in net.poll():
                if tipo_mensaje == "assign_id":
                    net.player_id = msg.get("player_id")
                    mi_id_de_red = net.player_id
                if msg["type"] == "snapshot":
                    state = msg["state"]
                    for p_data in state["players"]:
                        pid = p_data["id"]
                        if pid == net.player_id:
                            # Sincronizar nuestro jugador con el servidor
                            tanques_aliados[0].forma.centerx = p_data["x"]
                            tanques_aliados[0].forma.centery = p_data["y"]
                            tanques_aliados[0].energia = p_data.get("hp", 90)
                            tanques_aliados[0].vidas = p_data.get("vidas", 3)
                        else:
                            # Crear o actualizar "fantasmas" de otros jugadores
                            if pid not in remote_players:
                                ghost = Tanque(p_data["x"], p_data["y"], animaciones, p_data.get("hp", 90), 0, 0, 0)
                                remote_players[pid] = ghost
                            else:
                                ghost = remote_players[pid]
                                ghost.forma.centerx = p_data["x"]
                                ghost.forma.centery = p_data["y"]
                                ghost.energia = p_data.get("hp", 90)
                                ghost.vidas = p_data.get("vidas", 3)
                    fortaleza.energia = state.get("fortress_hp", fortaleza.energia)
                    
                    # Eliminar fantasmas de jugadores desconectados
                    remote_ids = {p["id"] for p in state["players"]}
                    for pid in list(remote_players.keys()):
                        if pid not in remote_ids:
                            del remote_players[pid]

            # Actualizar IA de enemigos
            for enemigo in list(tanques_enemigos):
                if not enemigo.update():
                    tanques_enemigos.remove(enemigo)
                    tanques.remove(enemigo)
                    tanques_aliados[0].puntaje += 100 # El puntaje va al jugador 1
                else:
                    # La IA apunta al jugador más cercano
                    jugador_cercano = min(tanques_aliados, key=lambda j: math.hypot(j.forma.centerx - enemigo.forma.centerx, j.forma.centery - enemigo.forma.centery))
                    enemigo.actualizar_ia_pixel(jugador_cercano, fortaleza, mundo.obstaculos_tiles, tanques, mundo.arbustos, grupo_balas_enemigas)

            # Lógica de generación de bonus por tiempo...
            # (El resto de la lógica de actualización: balas, items, oleadas, etc.)
            # ==================================================================
            # INICIO DEL BLOQUE FALTANTE: LÓGICA DE ACTUALIZACIÓN DEL JUEGO
            # ==================================================================
            
            # Actualizar IA de enemigos
            for enemigo in list(tanques_enemigos):
                if not enemigo.update():  
                    tanques_enemigos.remove(enemigo)
                    tanques.remove(enemigo)
                    if tanques_aliados: tanques_aliados[0].puntaje += 100 # El puntaje va al jugador 1
                else:
                    # La IA apunta al jugador aliado más cercano que esté vivo
                    jugadores_vivos = [j for j in tanques_aliados if j.vivo]
                    if jugadores_vivos:
                        jugador_cercano = min(jugadores_vivos, key=lambda j: math.hypot(j.forma.centerx - enemigo.forma.centerx, j.forma.centery - enemigo.forma.centery))
                        enemigo.actualizar_ia_pixel(jugador_cercano, fortaleza, mundo.obstaculos_tiles, tanques, mundo.arbustos, grupo_balas_enemigas)

            # Lógica de generación de bonus por tiempo
            tiempo_actual = pygame.time.get_ticks()
            # Bonus convencionales (cada 60 segundos)
            if tiempo_actual - ultimo_spawn_convencional > 60000:
                ultimo_spawn_convencional = tiempo_actual
                if mundo.tiles_libres:
                    tipo_item = random.choice([constantes.ITEM_ESCUDO, constantes.ITEM_DISPARO_POTENCIADO, constantes.ITEM_RELOJ])
                    x_tile, y_tile = random.choice(mundo.tiles_libres)
                    item = Item(x_tile * constantes.TAMAÑO_REJILLA + 16, y_tile * constantes.TAMAÑO_REJILLA + 16, tipo_item, imagenes_items[tipo_item])
                    grupo_items.add(item)
            
            # Bonus especiales (cada 2 minutos, 50% probabilidad)
            if tiempo_actual - ultimo_spawn_especial > 120000:
                ultimo_spawn_especial = tiempo_actual
                if random.random() < 0.5 and mundo.tiles_libres:
                    tipo_item = random.choice([constantes.ITEM_BOMBA, constantes.ITEM_ESCUDO_FORTALEZA, constantes.ITEM_VIDA, constantes.ITEM_BOOST])
                    x_tile, y_tile = random.choice(mundo.tiles_libres)
                    item = Item(x_tile * constantes.TAMAÑO_REJILLA + 16, y_tile * constantes.TAMAÑO_REJILLA + 16, tipo_item, imagenes_items[tipo_item])
                    grupo_items.add(item)
                    
            # Actualizar arma del jugador y balas
            # NOTA: Por ahora, solo el Jugador 1 (con la barra espaciadora) puede disparar.
            if tanques_aliados and tanques_aliados[0].vivo:
                bala = cañon_jugador.update(tanques_aliados[0], 1, False)
                if bala:
                    grupo_balas.add(bala)
            
            # Actualizar balas de los jugadores (golpean enemigos)
            for bala in list(grupo_balas):
                enemigo_golpeado = bala.update(tanques_enemigos, mundo.obstaculos_tiles, tiempo_actual < fortaleza_protegida_hasta)
                if enemigo_golpeado:
                    # El daño a enemigos sigue siendo local por ahora
                    enemigo_golpeado.energia -= bala.daño
                    posicion_daño = enemigo_golpeado.forma.center
                    texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(bala.daño), fuente, constantes.ROJO)
                    grupo_textos_daño.add(texto_daño)

            # Actualizar balas enemigas (golpean jugadores y fortaleza)
            for bala_enemiga in list(grupo_balas_enemigas):
                # Revisamos si la bala golpeó a un jugador
                jugador_golpeado = bala_enemiga.update(tanques_aliados, mundo.obstaculos_tiles, tiempo_actual < fortaleza_protegida_hasta)
                if jugador_golpeado and jugador_golpeado.id_red:
                    net.reportar_daño(jugador_golpeado.id_red, bala_enemiga.daño)
                    continue # La bala ya se destruyó, pasamos a la siguiente

                # Si no golpeó a un jugador, revisamos si golpeó la fortaleza
                if fortaleza.rect.colliderect(bala_enemiga.rect):
                    net.reportar_daño(None, bala_enemiga.daño, es_fortaleza=True)
                    bala_enemiga.kill()

            # Lógica de recolección de items (para todos los jugadores)
            for item in list(grupo_items): # Usamos list() para poder modificar el grupo mientras se itera
                for jugador in tanques_aliados:
                    if jugador.vivo and item.rect.colliderect(jugador.forma):
                        tipo = item.tipo_item
                        
                        if tipo == constantes.ITEM_MONEDA: jugador.puntaje += 20
                        elif tipo == constantes.ITEM_VIDA: jugador.energia = 90 # Vida al máximo
                        elif tipo == constantes.ITEM_ESCUDO:
                            jugador.escudo_activo = True
                            jugador.escudo_tiempo_final = tiempo_actual + constantes.DURACION_BONUS
                        elif tipo == constantes.ITEM_DISPARO_POTENCIADO:
                            jugador.potenciado_activo = True
                            jugador.potenciado_tiempo_final = tiempo_actual + constantes.DURACION_BONUS
                        elif tipo == constantes.ITEM_BOOST:
                            # (La lógica de boost está en la clase Tanque, aquí solo se activa)
                            jugador.boost_activo = True
                            jugador.boost_tiempo_final = tiempo_actual + constantes.DURACION_BONUS
                        elif tipo == constantes.ITEM_BOMBA:
                            for enemigo in list(tanques_enemigos): enemigo.energia = 0
                        elif tipo == constantes.ITEM_RELOJ:
                            for enemigo in tanques_enemigos:
                                enemigo.ralentizado = True
                                enemigo.ralentizado_tiempo_final = tiempo_actual + constantes.DURACION_RELOJ
                        elif tipo == constantes.ITEM_ESCUDO_FORTALEZA:
                            fortaleza_protegida_hasta = tiempo_actual + constantes.DURACION_ESCUDO_FORTALEZA
                            for obs in mundo.obstaculos_tiles:
                                if len(obs) > 5 and obs[5]: obs[0] = lista_tiles[5]
                        
                        item.kill() # El item desaparece
                        break # Salimos del bucle de jugadores para que no lo tomen dos a la vez

            # Restaurar muros de fortaleza cuando el escudo expira
            if fortaleza_protegida_hasta > 0 and tiempo_actual > fortaleza_protegida_hasta:
                fortaleza_protegida_hasta = 0
                for i, obs in enumerate(mundo.obstaculos_tiles):
                    if len(obs) > 5 and obs[5]:
                         if i in muros_originales:
                            obs[0] = muros_originales[i]

            # Actualizar sprites de items y textos de daño
            grupo_items.update()
            grupo_textos_daño.update()
            
            # Lógica de oleadas
            if not tanques_enemigos and mundo.tanques_restantes:
                oleada_actual += 1
                nuevos_enemigos = mundo.spawn_enemigos(animaciones_enemigos, cantidad=4)
                for enemigo in nuevos_enemigos:
                    enemigo.animacion_muerte = animacion_muerte
                    enemigo.cañon = Weapon(imagen_cañon, imagen_balas)
                    tanques_enemigos.append(enemigo)
                    tanques.append(enemigo)

            # ==================================================================
            # FIN DEL BLOQUE FALTANTE
            # ==================================================================
            # --- DIBUJAR TODO EN PANTALLA ---
            pantalla.fill(constantes.COLOR_BG)
            
            # Cámara sigue al jugador 1
            cam_x = tanques_aliados[0].forma.centerx - constantes.ANCHO_VENTANA / 2
            cam_y = tanques_aliados[0].forma.centery - constantes.ALTO_VENTANA / 2
            cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
            cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))
            posicion_pantalla = [cam_x, cam_y]

            mundo.dibujar(pantalla, posicion_pantalla)
            fortaleza.dibujar(pantalla, posicion_pantalla)

            for item in grupo_items:
                pantalla.blit(item.image, (item.rect.x - posicion_pantalla[0], item.rect.y - posicion_pantalla[1]))
            
            for enemigo in tanques_enemigos:
                enemigo.dibujar(pantalla, posicion_pantalla)
            
            for jugador in tanques_aliados:
                jugador.dibujar(pantalla, posicion_pantalla)

            for ghost in remote_players.values():
                ghost.dibujar(pantalla, posicion_pantalla)
            
            for ghost_enemy in remote_enemies.values():
                ghost_enemy.dibujar(pantalla, posicion_pantalla)
            
            for bala in grupo_balas: bala.dibujar(pantalla, posicion_pantalla)
            for bala_enemiga in grupo_balas_enemigas: bala_enemiga.dibujar(pantalla, posicion_pantalla)
            for texto in grupo_textos_daño:
                pantalla.blit(texto.image, (texto.rect.x - posicion_pantalla[0], texto.rect.y - posicion_pantalla[1]))
            
            todos_los_aliados = tanques_aliados + list(remote_players.values())
            for arbusto in mundo.arbustos:
                # Dibujar primero el arbusto opaco
                pantalla.blit(arbusto[0], (arbusto[1].x - cam_x, arbusto[1].y - cam_y))
                
                # Revisar si algún aliado está debajo para aplicar transparencia
                for jugador in todos_los_aliados:
                    if arbusto[1].colliderect(jugador.forma):
                        # Creamos una copia temporal para no afectar la imagen original
                        temp_img = arbusto[0].copy()
                        temp_img.set_alpha(150) # Hacemos la copia transparente
                        pantalla.blit(temp_img, (arbusto[1].x - cam_x, arbusto[1].y - cam_y))
                        # Rompemos el bucle para no dibujar la transparencia varias veces si ambos están debajo
                        break 
            # HUD
            # (El HUD muestra info del jugador 1 por ahora)
            if tanques_aliados:
                vida_jugador(tanques_aliados[0])
            dibujar_texto(f"Oleada: {oleada_actual}", fuente, constantes.BLANCO, constantes.ANCHO_VENTANA - 180, 20)
            dibujar_texto(f"Puntaje: {tanques_aliados[0].puntaje}", fuente, constantes.AZUL_CIELO_VIVO, constantes.ANCHO_VENTANA - 190, 50)
            dibujar_hud_bonus(tanques_aliados[0], fortaleza_protegida_hasta)
            # NUEVO: Contador de vidas
            if tanques_aliados:
                # La vida de nuestro tanque la obtenemos del servidor
                vidas_p1 = tanques_aliados[0].vidas 
                dibujar_texto(f"Vidas P1: {vidas_p1}", fuente, constantes.BLANCO, 10, 50)
            
            # Vidas del jugador remoto
            for ghost in remote_players.values():
                vidas_p2 = ghost.vidas
                dibujar_texto(f"Vidas P2: {vidas_p2}", fuente, constantes.BLANCO, 10, 80)
            
            tiempo_transcurrido = (pygame.time.get_ticks() - tiempo_inicio_partida) // 1000
            minutos = tiempo_transcurrido // 60
            segundos = tiempo_transcurrido % 60
            texto_tiempo = f"{minutos:02}:{segundos:02}"
            dibujar_texto(texto_tiempo, fuente, constantes.BLANCO, constantes.ANCHO_VENTANA / 2 - 40, 10)
            
            total_enemigos_restantes = len(tanques_enemigos) + len(mundo.tanques_restantes)
            aliados_vivos = sum(1 for t in tanques_aliados if t.vivo)
            dibujar_texto(f"Enemigos Restantes: {total_enemigos_restantes}", fuente, constantes.ROJO, constantes.ANCHO_VENTANA / 2 - 150, 40)
            dibujar_texto(f"Aliados Restantes: {aliados_vivos}", fuente, constantes.VERDE, constantes.ANCHO_VENTANA / 2 - 150, 70)

        # --- LÓGICA DE FIN DE PARTIDA ---
        aliados_vivos_count = sum(1 for t in tanques_aliados if t.vivo)
        if fortaleza.energia <= 0 or aliados_vivos_count == 0:
            jugador1_listo = False
            jugador2_listo = False
            game_state = "GAME_OVER"

        if not tanques_enemigos and not mundo.tanques_restantes:
            jugador1_listo = False
            jugador2_listo = False
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
            # Para probar, puedes añadir un texto simple para el J2
            dibujar_texto(f"Jugador 2: {texto2}", fuente, constantes.BLANCO, boton_volver_menu.x, boton_volver_menu.y + 60)

    elif game_state == "VICTORIA":
        pantalla.fill(constantes.VERDE_OSCURO)
        dibujar_texto("Victoria", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA/3, constantes.ALTO_VENTANA/4)
        dibujar_boton_retro("Reiniciar", boton_reinicio_vic)
        # Siguiente Dificultad...
        # Volver al menú...
        if jugadores_seleccionados == 2:
            texto1 = "LISTO" if jugador1_listo else "Esperando..."
            texto2 = "LISTO" if jugador2_listo else "Esperando..."
            dibujar_texto(f"J1: {texto1}", fuente, constantes.BLANCO, boton_reinicio_vic.x, boton_reinicio_vic.y + 60)
            # ... y así sucesivamente para otros botones y estados del J2
    
    for msg in net.poll():
        tipo_mensaje = msg.get("type")
        if tipo_mensaje == "actualizar_lista_partidas":
            partidas_disponibles = msg.get("partidas", {})
        elif tipo_mensaje in ["partida_creada", "actualizacion_partida"]:
            mi_partida_actual = msg.get("partida", {})
            game_state = "SALA_ESPERA"
        elif tipo_mensaje == "iniciar_juego":
            partida_info = msg.get("partida", {})
            mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = iniciar_partida(partida_info["dificultad"], 2) # Usa los datos del servidor
            game_state = "EN_JUEGO"
    
    # ==================================================================
    # SECCIÓN DE EVENTOS: MANEJO DE INPUTS DEL USUARIO
    # ==================================================================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        # --- EVENTOS DE TECLADO (PARA MOVIMIENTO Y DISPARO) ---
        if game_state == "EN_JUEGO":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: pressed["up"] = True
                if event.key == pygame.K_s: pressed["down"] = True
                if event.key == pygame.K_a: pressed["left"] = True
                if event.key == pygame.K_d: pressed["right"] = True
                if event.key == pygame.K_SPACE: pressed["fire"] = True
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w: pressed["up"] = False
                if event.key == pygame.K_s: pressed["down"] = False
                if event.key == pygame.K_a: pressed["left"] = False
                if event.key == pygame.K_d: pressed["right"] = False
                if event.key == pygame.K_SPACE: pressed["fire"] = False
        
        # --- EVENTOS DE MOUSE (PARA BOTONES EN MENÚS) ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos_mouse = event.pos
            
            if game_state == "MENU_PRINCIPAL":
                if boton_jugar.collidepoint(pos_mouse) and dificultad_seleccionada:
                    if jugadores_seleccionados == 1:
                        # Iniciar partida para 1 jugador
                        mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = iniciar_partida(dificultad_seleccionada, 1)
                        tiempo_inicio_partida = pygame.time.get_ticks()
                        game_state = "EN_JUEGO"
                    else:
                        # Ir al lobby para 2 jugadores
                        game_state = "LOBBY"
                elif boton_salir.collidepoint(pos_mouse):
                    run = False
                # Selección de dificultad y jugadores
                for i, rect in enumerate(botones_dificultad):
                    if rect.collidepoint(pos_mouse):
                        dificultad_seleccionada = dificultades[i]
                for i, rect in enumerate(botones_jugadores):
                    if rect.collidepoint(pos_mouse):
                        jugadores_seleccionados = i + 1

            elif game_state == "LOBBY":
                if boton_crear_partida.collidepoint(pos_mouse):
                     # --- INICIO DE LA CORRECCIÓN ---
                    # 1. Cargar el mundo temporalmente para leer los datos del mapa
                    mundo_temporal = Mundo()
                    mundo_temporal.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad_seleccionada, 2)
                    
                    # 2. Extraer las coordenadas de spawn
                    px1, py1 = mundo_temporal.posicion_spawn_jugador
                    px2, py2 = mundo_temporal.posicion_spawn_jugador2
                    spawn1_coords = (px1 * constantes.TAMAÑO_REJILLA + 16, py1 * constantes.TAMAÑO_REJILLA + 16)
                    spawn2_coords = (px2 * constantes.TAMAÑO_REJILLA + 16, py2 * constantes.TAMAÑO_REJILLA + 16)

                    # 3. Extraer los obstáculos en un formato simple para enviar
                    lista_obstaculos = []
                    for obs in mundo_temporal.obstaculos_tiles:
                        rect = obs[1]
                        lista_obstaculos.append([rect.x, rect.y, rect.width, rect.height])

                    # NUEVO: Extraer la "receta" de enemigos para el servidor
                    lista_enemigos_del_nivel = mundo_temporal.tanques_restantes
                    puntos_spawn_enemigos = mundo_temporal.posiciones_spawn_enemigos

                    # Enviar todo al servidor
                    net.crear_partida(
                        f"Partida de {random.randint(100,999)}", 
                        dificultad_seleccionada, 
                        spawn1_coords, 
                        spawn2_coords, 
                        lista_obstaculos,
                        lista_enemigos_del_nivel, # NUEVO
                        puntos_spawn_enemigos    # NUEVO
                    )
                    # --- FIN DE LA CORRECCIÓN ---
                elif boton_unirse_partida.collidepoint(pos_mouse):
                    # Pedir la lista de partidas y cambiar de estado
                    net.pedir_lista_partidas()
                    game_state = "LISTA_PARTIDAS"
                elif boton_volver_lobby.collidepoint(pos_mouse):
                    game_state = "MENU_PRINCIPAL"

            elif game_state == "SALA_ESPERA":
                # Solo el host puede iniciar la partida
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
                # Volver al menú (funciona para ambos estados)
                if boton_volver_menu.collidepoint(pos_mouse) or boton_volver_menu_vic.collidepoint(pos_mouse):
                    game_state = "MENU_PRINCIPAL"

                # Lógica de Reiniciar
                if (game_state == "GAME_OVER" and boton_reinicio.collidepoint(pos_mouse)) or \
                   (game_state == "VICTORIA" and boton_reinicio_vic.collidepoint(pos_mouse)):
                    
                    if jugadores_seleccionados == 1:
                        mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = resetear_mundo() # Asumiendo que resetear_mundo existe y funciona
                        game_state = "EN_JUEGO"
                    else: # 2 Jugadores
                        jugador1_listo = not jugador1_listo
                        # Simulación: En un juego real, esperaríamos el evento del otro jugador.
                        # Para probar, puedes hacer que el J2 siempre esté listo, o vincularlo a una tecla.
                        jugador2_listo = True # ¡SOLO PARA PRUEBAS!
                        if jugador1_listo and jugador2_listo:
                            mundo, tanques_aliados, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items, cañon_jugador, muros_originales = resetear_mundo()
                            game_state = "EN_JUEGO"

    # 3. Actualizar la pantalla completa una vez al final del bucle
    pygame.display.update()

# Al salir del bucle, detener la red y cerrar pygame
net.stop()
pygame.quit()