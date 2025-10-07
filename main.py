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

pygame.init()

pantalla = pygame.display.set_mode((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA))
pygame.display.set_caption("Tank-Atackk")

#Funciones:
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
def vida_jugador():
    c_mitad_dibujado = False
    for i in range(3):
        if tanque_jugador.energia >= ((i+1)*30):
            pantalla.blit(corazon_completo, (5+i*30, 5))
        elif tanque_jugador.energia % 30 > 0 and c_mitad_dibujado == False:
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

def iniciar_partida(dificultad, num_jugadores):
    """Crea y devuelve todos los objetos necesarios para una nueva partida."""
    # Crear listas y grupos de sprites vacíos
    tanques = []
    tanques_enemigos = []
    grupo_balas = pygame.sprite.Group()
    grupo_balas_enemigas = pygame.sprite.Group()
    grupo_textos_daño = pygame.sprite.Group()
    grupo_items = pygame.sprite.Group()

    # Crear el mundo usando la dificultad y jugadores seleccionados
    mundo = Mundo()
    mundo.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos, dificultad, num_jugadores)

    # Crear tanque del jugador
    px, py = mundo.posicion_spawn_jugador
    tanque_jugador = Tanque(
        px * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        py * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
        animaciones, 900, 0, constantes.VELOCIDAD, constantes.DISPARO_COOLDOWN
    )
    tanques.append(tanque_jugador)
    
    #Crear el arma del tanque del jugador
    cañon_jugador = Weapon(imagen_cañon, imagen_balas)

    # Crear la fortaleza
    fx, fy = mundo.posicion_fortaleza
    fortaleza = Fortaleza(
        fx * constantes.TAMAÑO_REJILLA,
        fy * constantes.TAMAÑO_REJILLA,
        imagen_fortaleza
    )
    fortaleza_obstaculo = [
        fortaleza.image,
        fortaleza.rect,
        fortaleza.rect.centerx,
        fortaleza.rect.centery,
        fortaleza.energia # La "vida" del obstáculo es la energía de la fortaleza
    ]
    mundo.obstaculos_tiles.append(fortaleza_obstaculo)
    
    mundo.crear_grid_navegacion()

    # Crear tanques enemigos
    for enemigo in mundo.lista_enemigos:
        enemigo.animacion_muerte = animacion_muerte
        enemigo.cañon = Weapon(imagen_cañon, imagen_balas)
        tanques_enemigos.append(enemigo)
        tanques.append(enemigo)
    
    # Crear items
    for item in mundo.lista_items:
        grupo_items.add(item)
    
    # Devolver todos los objetos creados
    return mundo, tanque_jugador, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items

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
    
#Variables
nivel = 1
oleada_actual = 1
tanques = []
vidas_jugador = 3

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
###Pocion
pocion = pygame.image.load("assets//images//items//pocion.png")
pocion = escalar_img(pocion, constantes.ESCALA_POCION, constantes.ESCALA_POCION)

###Moneda
imagenes_moneda= []
ruta_moneda_img = "assets//images//items//moneda"
num_moneda_img = contar_elementos(ruta_moneda_img)

for i in range(num_moneda_img):
    img_moneda = pygame.image.load(f"{ruta_moneda_img}//moneda_{i}.png")
    img_moneda = escalar_img(img_moneda, constantes.ESCALA_MONEDA, constantes.ESCALA_MONEDA)
    imagenes_moneda.append(img_moneda)
    
imagenes_items = [imagenes_moneda, [pocion]] 

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

#Definir variables de movimiento del tanque
mover_arriba = False
mover_abajo = False
mover_izquierda = False
mover_derecha = False

#Controlar framerate
reloj = pygame.time.Clock()

mostrar_inicio = True

run = True
while run:
    if mostrar_inicio:
        pantalla_inicio()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # --- Botones de dificultad ---
                for i, rect in enumerate(botones_dificultad):
                    if rect.collidepoint(event.pos):
                        dificultad_seleccionada = dificultades[i]
                
                # --- Botones de jugadores ---
                for i, rect in enumerate(botones_jugadores):
                    if rect.collidepoint(event.pos):
                        jugadores_seleccionados = i + 1
                
                # --- Botones de Jugar / Salir ---
                if boton_jugar.collidepoint(event.pos):
                    mostrar_inicio = False
                    # ¡AQUÍ INICIAMOS LA PARTIDA CON LOS VALORES SELECCIONADOS!
                    mundo, tanque_jugador, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items = iniciar_partida(dificultad_seleccionada, jugadores_seleccionados)
                    # Creamos el cañón del jugador aquí también
                    cañon_jugador = Weapon(imagen_cañon, imagen_balas)
                if boton_salir.collidepoint(event.pos):
                    run = False 

    else:
        pantalla.fill(constantes.COLOR_BG)
        reloj.tick(constantes.FPS)

        # =================================================
        # SECCIÓN 1: ACTUALIZAR LÓGICA DEL JUEGO
        # =================================================
        if tanque_jugador.vivo:
            # Calcular movimiento del jugador
            delta_x = 0
            delta_y = 0
            if mover_arriba: delta_y = -constantes.VELOCIDAD
            elif mover_abajo: delta_y = constantes.VELOCIDAD
            elif mover_izquierda: delta_x = -constantes.VELOCIDAD
            elif mover_derecha: delta_x = constantes.VELOCIDAD

            # Mover tanque del jugador
            tanque_jugador.movimiento(delta_x, delta_y, mundo.obstaculos_tiles, tanques)
            
            # Actualizar estado del tanque del jugador
            tanque_jugador.update()
        
        # =================================================
        # SECCIÓN 2: CALCULAR POSICIÓN DE LA CÁMARA (¡AHORA ESTÁ ANTES!)
        # =================================================
        cam_x = tanque_jugador.forma.centerx - constantes.ANCHO_VENTANA / 2
        cam_y = tanque_jugador.forma.centery - constantes.ALTO_VENTANA / 2
        
        cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
        cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))
        posicion_pantalla = [cam_x, cam_y]

        # =================================================
        # SECCIÓN 3: ACTUALIZAR EL RESTO DE LA LÓGICA (USANDO LA CÁMARA)
        # =================================================
        if tanque_jugador.vivo:
            # Actualizar tanques enemigos (IA y estado)
            for tanque in tanques_enemigos:
                if not tanque.update():  
                    tanques_enemigos.remove(tanque)
                    tanques.remove(tanque)
                    tanque_jugador.puntaje += 100
                else:
                    tanque.actualizar_ia_pixel(tanque_jugador, fortaleza, mundo.obstaculos_tiles, tanques, mundo.arbustos, grupo_balas_enemigas)
                    
            # Actualizar arma del jugador y balas
            bala = cañon_jugador.update(tanque_jugador, 1, False)
            if bala:
                grupo_balas.add(bala)
            
            for bala in grupo_balas:
                daño, posicion_daño = bala.update(tanques_enemigos, mundo.obstaculos_tiles)
                if daño:
                    texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(daño), fuente, constantes.ROJO)
                    grupo_textos_daño.add(texto_daño)
            
            # Actualizar balas enemigas
            for bala_enemiga in grupo_balas_enemigas:
                if fortaleza.rect.colliderect(bala_enemiga.rect):
                    fortaleza.energia -= 10
                    bala_enemiga.kill()
                daño, posicion_daño = bala_enemiga.update([tanque_jugador], mundo.obstaculos_tiles)
                if daño:
                    texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(daño), fuente, constantes.ROJO)
                    grupo_textos_daño.add(texto_daño)

            # Actualizar items y textos de daño <-- MOVIDOS AQUÍ
            grupo_items.update(posicion_pantalla, tanque_jugador)
            grupo_textos_daño.update(posicion_pantalla)
            
            # --- INICIO DE LÓGICA DE OLEADAS (REFINADA) ---
            if not tanques_enemigos and mundo.tanques_restantes:
                oleada_actual += 1
                
                # La función ahora devuelve los tanques recién creados
                nuevos_enemigos = mundo.spawn_enemigos(animaciones_enemigos, cantidad=4)

                # Inicializamos y añadimos solo esos nuevos tanques a las listas del juego
                for enemigo in nuevos_enemigos:
                    enemigo.animacion_muerte = animacion_muerte
                    enemigo.cañon = Weapon(imagen_cañon, imagen_balas)
                    tanques_enemigos.append(enemigo)
                    tanques.append(enemigo)
            # --- FIN DE LÓGICA DE OLEADAS ---

        # =================================================
        # SECCIÓN 4: DIBUJAR TODO EN PANTALLA
        # =================================================
        # Mundo y Fortaleza
        mundo.dibujar(pantalla, posicion_pantalla)
        fortaleza.dibujar(pantalla, posicion_pantalla)
        
        # Items
        for item in grupo_items:
            pantalla.blit(item.image, (item.rect.x - posicion_pantalla[0], item.rect.y - posicion_pantalla[1]))
        
        # Tanques y Cañones
        for tanque in tanques_enemigos:
            tanque.dibujar(pantalla, posicion_pantalla)
        tanque_jugador.dibujar(pantalla, posicion_pantalla)
        
        for tanque in tanques_enemigos:
            if tanque.cañon:
                tanque.cañon.dibujar(pantalla, posicion_pantalla)
        cañon_jugador.dibujar(pantalla, posicion_pantalla)
        
        # Arbustos
        # Arbustos (correctamente dibujados al final para el efecto de transparencia)
        for arbusto in mundo.arbustos:
            # Dibuja el arbusto opaco siempre (esto tapará a los enemigos que estén debajo)
            pantalla.blit(arbusto[0], (arbusto[1].x - cam_x, arbusto[1].y - cam_y))
            # Si el JUGADOR está dentro, dibuja una copia transparente encima de todo
            if arbusto[1].colliderect(tanque_jugador.forma):
                temp_img = arbusto[0]
                temp_img.set_alpha(150) # Hacemos la copia transparente
                pantalla.blit(temp_img, (arbusto[1].x - cam_x, arbusto[1].y - cam_y))
                
        # Balas y textos
        for bala in grupo_balas:
            bala.dibujar(pantalla, posicion_pantalla)
        for bala_enemiga in grupo_balas_enemigas:
            bala_enemiga.dibujar(pantalla, posicion_pantalla)
        grupo_textos_daño.draw(pantalla)
        
        # HUD
        vida_jugador()
        dibujar_texto(f"Oleada: {oleada_actual}", fuente, constantes.BLANCO, constantes.ANCHO_VENTANA - 180, 20)
        dibujar_texto(f"Puntaje: {tanque_jugador.puntaje}", fuente, constantes.AZUL_CIELO_VIVO, constantes.ANCHO_VENTANA - 190, 50)
        dibujar_texto(f"Vidas: {vidas_jugador}", fuente, constantes.VERDE, constantes.ANCHO_VENTANA - 165, 80)
        
        # =================================================
        # SECCIÓN 5: LÓGICA DE FIN DE PARTIDA
        # =================================================
        if fortaleza.energia <= 0:
            tanque_jugador.vivo = False
            
        if not tanque_jugador.vivo:
            vidas_jugador -= 1
            if vidas_jugador > 0:
                tanque_jugador.energia = 90
                tanque_jugador.vivo = True
                px, py = mundo.posicion_spawn_jugador
                tanque_jugador.forma.center = (
                    px * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2),
                    py * constantes.TAMAÑO_REJILLA + (constantes.TAMAÑO_REJILLA / 2)
                )
            else:
                # Pantalla de Game Over
                game_over_image = pygame.image.load("assets//images//pantallas//pantalla_inicio.png")
                game_over_image = escalar_img(game_over_image, constantes.ANCHO_VENTANA / game_over_image.get_width(), constantes.ALTO_VENTANA / game_over_image.get_height())
                pantalla.blit(game_over_image, (0, 0))
                overlay = pygame.Surface((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA), pygame.SRCALPHA)
                overlay.fill(constantes.ROJO_TRANSPARENTE)
                pantalla.blit(overlay, (0, 0))
                text_rect = game_over_text.get_rect(center=(constantes.ANCHO_VENTANA/2, constantes.ALTO_VENTANA/2))
                pantalla.blit(game_over_text, text_rect)
                dibujar_boton_retro("Reiniciar", boton_reinicio)
                dibujar_boton_retro("Menu Principal", boton_volver_menu)
        
        if not tanques_enemigos and tanque_jugador.vivo:
            # Pantalla de Victoria
            victory_image = pygame.image.load("assets//images//pantallas//pantalla_inicio.png")
            victory_image = escalar_img(victory_image, constantes.ANCHO_VENTANA / victory_image.get_width(), constantes.ALTO_VENTANA / victory_image.get_height())
            pantalla.blit(victory_image, (0, 0))
            overlay = pygame.Surface((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA), pygame.SRCALPHA)
            overlay.fill((0, 255, 0, 70))
            pantalla.blit(overlay, (0, 0))
            text_rect = texto_victoria.get_rect(center=(constantes.ANCHO_VENTANA/2, constantes.ALTO_VENTANA/2))
            pantalla.blit(texto_victoria, text_rect)
            dibujar_boton_retro("Reiniciar", boton_reinicio_vic)
            dibujar_boton_retro("Menu Principal", boton_volver_menu_vic)
            if dificultad_seleccionada == "Facil":
                # Crear el boton de siguiente dificultad
                boton_siguiente_dificultad = pygame.Rect(constantes.ANCHO_VENTANA // 2 + 140, constantes.ALTO_VENTANA // 2 + 100, 390, 50)
                dibujar_boton_retro("Siguiente Dificultad", boton_siguiente_dificultad)
            elif dificultad_seleccionada == "Intermedio":
                # Crear el boton de siguiente dificultad
                boton_siguiente_dificultad = pygame.Rect(constantes.ANCHO_VENTANA // 2 + 140, constantes.ALTO_VENTANA // 2 + 100, 390, 50)
                dibujar_boton_retro("Siguiente Dificultad", boton_siguiente_dificultad)
            elif dificultad_seleccionada == "Dificil" and jugadores_seleccionados == 2:
                # Crear el boton de siguiente dificultad
                boton_siguiente_dificultad = pygame.Rect(constantes.ANCHO_VENTANA // 2 + 140, constantes.ALTO_VENTANA // 2 + 100, 390, 50)
                dibujar_boton_retro("Siguiente Dificultad", boton_siguiente_dificultad)

        # =================================================
        # SECCIÓN 6: MANEJO DE EVENTOS
        # =================================================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: mover_izquierda = True
                if event.key == pygame.K_d: mover_derecha = True
                if event.key == pygame.K_w: mover_arriba = True
                if event.key == pygame.K_s: mover_abajo = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a: mover_izquierda = False
                if event.key == pygame.K_d: mover_derecha = False
                if event.key == pygame.K_w: mover_arriba = False
                if event.key == pygame.K_s: mover_abajo = False
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                game_over = vidas_jugador <= 0 and not tanque_jugador.vivo
                victoria = not tanques_enemigos and tanque_jugador.vivo
                
                if game_over and boton_reinicio.collidepoint(event.pos):
                    mundo, tanque_jugador, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items = resetear_mundo()
                    cañon_jugador = Weapon(imagen_cañon, imagen_balas)
                
                if victoria and boton_reinicio_vic.collidepoint(event.pos):
                    mundo, tanque_jugador, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items = resetear_mundo()
                    cañon_jugador = Weapon(imagen_cañon, imagen_balas)
                
                if game_over and boton_volver_menu.collidepoint(event.pos):
                    mostrar_inicio = True
                    dificultad_seleccionada = "Facil"
                    jugadores_seleccionados = 1
                if victoria and boton_volver_menu_vic.collidepoint(event.pos):
                    mostrar_inicio = True
                    dificultad_seleccionada = "Facil"
                    jugadores_seleccionados = 1
                if victoria and boton_siguiente_dificultad.collidepoint(event.pos):
                    if dificultad_seleccionada == "Facil":
                        dificultad_seleccionada = "Intermedio"
                    elif dificultad_seleccionada == "Intermedio":
                        dificultad_seleccionada = "Dificil"
                    mundo, tanque_jugador, fortaleza, tanques, tanques_enemigos, grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items = resetear_mundo()
                    cañon_jugador = Weapon(imagen_cañon, imagen_balas)

        pygame.display.update()

pygame.quit()