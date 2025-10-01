import pygame
import constantes
from tanque import Tanque
from weapon import Weapon
from textos import DamageText
from items import Item
from mundo import Mundo
import os
import csv

pygame.init()

pantalla = pygame.display.set_mode((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA))
pygame.display.set_caption("Tank-Atackk")

#Funciones:
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
    global grupo_balas, grupo_balas_enemigas, grupo_textos_daño, grupo_items
    
    # Vaciar los grupos de sprites
    grupo_balas.empty()
    grupo_balas_enemigas.empty()
    grupo_textos_daño.empty()
    grupo_items.empty()

    # Vaciar y recargar los datos del mundo
    data_suelo = []
    data_objetos = []

    for fila in range(constantes.FILAS):
        fila_suelo = [0] * constantes.COLUMNAS
        data_suelo.append(fila_suelo)

        fila_objetos = [-1] * constantes.COLUMNAS
        data_objetos.append(fila_objetos)

    # Cargar archivos CSV
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
    
    # Crear el mundo
    mundo = Mundo()
    mundo.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos)
    
    # Crear tanque del jugador
    tanque_jugador = Tanque(144, 240, animaciones, 90, 1)
    tanques = [tanque_jugador]
    
    # Crear tanques enemigos
    tanques_enemigos = []
    for i in mundo.lista_enemigos:
        i.animacion_muerte = animacion_muerte
        tanques_enemigos.append(i)
        tanques.append(i)

    # Crear items
    for item in mundo.lista_items:
        grupo_items.add(item)
    
    return mundo, tanque_jugador, tanques, tanques_enemigos

##Funcion para mostrar la pantalla de inicio
def pantalla_inicio():
    #Cargar y escalar la imagen de inicio
    inicio_image = pygame.image.load("assets//images//pantallas//pantalla_inicio.png")
    inicio_image = escalar_img(inicio_image, constantes.ANCHO_VENTANA / inicio_image.get_width(), constantes.ALTO_VENTANA / inicio_image.get_height())
    pantalla.blit(inicio_image, (0, 0))
    #Dibujar el texto del titulo
    dibujar_texto("TANK ATTACK", fuente_titulo, constantes.BLANCO, constantes.ANCHO_VENTANA / 4 - 120, constantes.ALTO_VENTANA / 4)
    #Dibujar el boton de jugar
    pygame.draw.rect(pantalla, constantes.VERDE, boton_jugar)
    pantalla.blit(texto_boton_jugar, (boton_jugar.x + 5, boton_jugar.y + 5))
    #Dibujar el boton de salir
    pygame.draw.rect(pantalla, constantes.ROJO_TRANSPARENTE, boton_salir)
    pantalla.blit(texto_boton_salir, (boton_salir.x + 15, boton_salir.y + 10))
    
    pygame.display.update()
    
#Variables
nivel = 1
tanques = []

#Importar fuentes
fuente = pygame.font.Font("assets//fuentes//fibberish.ttf", 25)
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

##Tanques
###Jugador
animaciones = []
for i in range(2):
    img = pygame.image.load("assets//images//tanque//tanque_" + str(i) + ".png")
    img = escalar_img(img, constantes.ESCALA_TANQUE_ANCHO, constantes.ESCALA_TANQUE_ALTO)
    animaciones.append(img)

###Enemigos
directorio__tanques_enemigos = "assets//images//tanques_enemigos//"
tipo_enemigos = nombre_carpetas(directorio__tanques_enemigos)
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
    
imagenes_items = [[pocion], imagenes_moneda] 

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


#Crear el mundo
mundo = Mundo()
mundo.process_data(data_suelo, data_objetos, lista_tiles, imagenes_items, animaciones_enemigos)

#Crear tanque
tanque_jugador = Tanque(144, 240, animaciones, 90, 1)
tanques.append(tanque_jugador)
#Crear tanques enemigos
##Crear lista de tanques enemigos
tanques_enemigos = []
for i in mundo.lista_enemigos:
    i.animacion_muerte = animacion_muerte
    i.cañon = Weapon(imagen_cañon, imagen_balas)
    tanques_enemigos.append(i)
    tanques.append(i)

#Crear el arma del tanque del jugador
cañon_jugador = Weapon(imagen_cañon, imagen_balas)


#Crear un grupo de sprites
##Grupo de balas
grupo_balas = pygame.sprite.Group()
##Grupo de balas enemigas
grupo_balas_enemigas = pygame.sprite.Group()
##Grupo de textos de daño
grupo_textos_daño = pygame.sprite.Group()
##Grupo de items
grupo_items = pygame.sprite.Group()

#Crear items
for item in mundo.lista_items:
    grupo_items.add(item)

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

#Crear botones
##Boton de reinicio en el game over
boton_reinicio = pygame.Rect(constantes.ANCHO_VENTANA/2 - 100, constantes.ALTO_VENTANA/2 + 100, 190, 50)
##Boton de jugar
boton_jugar = pygame.Rect(constantes.ANCHO_VENTANA / 3 - 50, constantes.ALTO_VENTANA / 3 + 100, 125, 50)
##Boton de salir
boton_salir = pygame.Rect(constantes.ANCHO_VENTANA / 3 + 200, constantes.ALTO_VENTANA / 3 + 100, 125, 50)
##Boton de reinicio en la victoria
boton_reinicio_vic = pygame.Rect(constantes.ANCHO_VENTANA/2 - 100, constantes.ALTO_VENTANA/2 + 100, 190, 50)

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
                if boton_jugar.collidepoint(event.pos):
                    mostrar_inicio = False
                if boton_salir.collidepoint(event.pos):
                    run = False 
    
    else:
        pantalla.fill(constantes.COLOR_BG)
        #Dibujar la rejilla
        dibujar_rejilla()
        
        #Que vaya a 120 fps
        reloj.tick(constantes.FPS)


        if tanque_jugador.vivo:
                #Calcular movimiento del tanque
                delta_x = 0
                delta_y = 0
                
                if mover_arriba == True:
                    delta_y = -constantes.VELOCIDAD
                if mover_abajo == True:
                    delta_y = constantes.VELOCIDAD
                if mover_izquierda == True:
                    delta_x = -constantes.VELOCIDAD
                if mover_derecha == True:
                    delta_x = constantes.VELOCIDAD

                #Mover tanque
                posicion_pantalla = tanque_jugador.movimiento(delta_x, delta_y, mundo.obstaculos_tiles, tanques)
 
                #Actualizar mundo
                mundo.update(posicion_pantalla)
                
                #Actualiza estado del tanque
                tanque_jugador.update()
                
                #Actualiza estado de los tanques enemigos
                for tanque in tanques_enemigos:
                    if not tanque.update():  
                        tanques_enemigos.remove(tanque)
                        tanques.remove(tanque)
                        tanque_jugador.puntaje += 100
                    else:
                        tanque.tanques_enemigos(posicion_pantalla, mundo.obstaculos_tiles, mundo.arbustos, tanque_jugador, grupo_balas_enemigas, tanques, data_objetos)
                        tanque.update()
                
                #Actualiza estado del arma
                bala = cañon_jugador.uptade(tanque_jugador, 1, False)
                if bala:
                    grupo_balas.add(bala)
                
                for bala in grupo_balas:
                    daño, posicion_daño = bala.update(tanques_enemigos, mundo.obstaculos_tiles)
                    if daño:
                        texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(daño), fuente, constantes.ROJO)
                        grupo_textos_daño.add(texto_daño)
                
                #Actualiza el estado del arma de los tanques enemigos
                for tanque in tanques_enemigos:
                    if tanque.cañon:
                        tanque.update_cañon_enemigo(tanque, tanque.cañon, mundo.obstaculos_tiles, mundo.arbustos, tanque_jugador, grupo_balas_enemigas)

                for bala_enemiga in grupo_balas_enemigas:
                    daño, posicion_daño = bala_enemiga.update([tanque_jugador], mundo.obstaculos_tiles)
                    if daño:
                        texto_daño = DamageText(posicion_daño[0], posicion_daño[1], str(daño), fuente, constantes.ROJO)
                        grupo_textos_daño.add(texto_daño)
                        
                #Actualizar los textos de daño
                grupo_textos_daño.update(posicion_pantalla)
                
                #Actualizar los items
                grupo_items.update(posicion_pantalla, tanque_jugador)
            
        #Dibujar el mundo
        mundo.dibujar(pantalla, tanque_jugador, posicion_pantalla)
        
        cam_x, cam_y = posicion_pantalla
        cam_x = tanque_jugador.forma.centerx - constantes.ANCHO_VENTANA
        cam_y = tanque_jugador.forma.centery - constantes.ALTO_VENTANA
        # Limitar cámara para que no se salga del mapa
        cam_x = max(0, min(cam_x, constantes.MAPA_ANCHO - constantes.ANCHO_VENTANA))
        cam_y = max(0, min(cam_y, constantes.MAPA_ALTO - constantes.ALTO_VENTANA))
        posicion_pantalla = [cam_x, cam_y]
        
        #Dibujar a los tanques enemigos
        # Tanques enemigos
        for tanque in tanques_enemigos:
            if tanque.cañon:
                tanque.dibujar(pantalla, posicion_pantalla)
                tanque.cañon.dibujar(pantalla, posicion_pantalla)

        # Tanque jugador
        tanque_jugador.dibujar(pantalla, posicion_pantalla)
        cañon_jugador.dibujar(pantalla, posicion_pantalla)
        
        #Dibujar las balas
        for bala in grupo_balas:
            bala.dibujar(pantalla, posicion_pantalla)
        
        #Dibujar las balas enemigas
        for bala_enemiga in grupo_balas_enemigas:
            bala_enemiga.dibujar(pantalla, posicion_pantalla)

        #Dibujar los corazones
        vida_jugador()
        
        #Dibujar textos
        ##Dibujar los textos de daño
        grupo_textos_daño.draw(pantalla)
        ##Dibujar texto de nivel
        dibujar_texto(f"Nivel: " + str(nivel), fuente, constantes.BLANCO, constantes.ANCHO_VENTANA - 165 , 20)
        ##Dibujar texto de puntaje
        dibujar_texto(f"Puntaje: " + str(tanque_jugador.puntaje), fuente, constantes.AZUL_CIELO_VIVO, constantes.ANCHO_VENTANA - 190 , 50)
        
        #Dibujar los items
        for item in grupo_items:
           pantalla.blit(item.image, (item.rect.x - posicion_pantalla[0], item.rect.y - posicion_pantalla[1]))

        
        if tanque_jugador.vivo == False:
            #Cargar y escalar la imagen de game over
            game_over_image = pygame.image.load("assets//images//pantallas//pantalla_game_over.png")
            game_over_image = escalar_img(game_over_image, constantes.ANCHO_VENTANA / game_over_image.get_width(), constantes.ALTO_VENTANA / game_over_image.get_height())
            pantalla.blit(game_over_image, (0, 0))
            
            #Crear una superficie roja transparente
            overlay = pygame.Surface((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA))
            overlay.set_alpha(128)  # Ajustar la transparencia (0-255)
            overlay.fill(constantes.ROJO_OSCURO)  # Rellenar con color rojo oscuro
            pantalla.blit(overlay, (0, 0))
            
            #Dibujar el texto de game over
            text_rect = game_over_text.get_rect(center=(constantes.ANCHO_VENTANA/2, constantes.ALTO_VENTANA/2))
            pantalla.blit(game_over_text, text_rect)
            
            #Dibujar el boton de reinicio
            pygame.draw.rect(pantalla, constantes.ROJO, boton_reinicio) 
            pantalla.blit(texto_boton_reinicio, (boton_reinicio.x + 10, boton_reinicio.y + 10))
        
        if tanques_enemigos == []:        
            #Crear una superficie verde transparente
            overlay = pygame.Surface((constantes.ANCHO_VENTANA, constantes.ALTO_VENTANA))
            overlay.set_alpha(128)  # Ajustar la transparencia (0-255)
            overlay.fill(constantes.VERDE)  # Rellenar con color rojo oscuro
            pantalla.blit(overlay, (0, 0))
            
            #Dibujar el texto de game over
            text_rect = texto_victoria.get_rect(center=(constantes.ANCHO_VENTANA/2, constantes.ALTO_VENTANA/2))
            pantalla.blit(texto_victoria, text_rect)
            
            #Dibujar el boton de reinicio
            pygame.draw.rect(pantalla, constantes.VERDE_OSCURO, boton_reinicio_vic) 
            pantalla.blit(texto_boton_reinicio_vic, (boton_reinicio_vic.x + 10, boton_reinicio_vic.y + 10))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                if mover_arriba == False and mover_abajo == False:
                    if event.key == pygame.K_a:
                        mover_izquierda = True
                    if event.key == pygame.K_d:
                        mover_derecha = True
                if mover_derecha == False and mover_izquierda == False:
                    if event.key == pygame.K_w:
                        mover_arriba = True
                    if event.key == pygame.K_s:
                        mover_abajo = True
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    mover_izquierda = False
                if event.key == pygame.K_d:
                    mover_derecha = False
                if event.key == pygame.K_w:
                    mover_arriba = False
                if event.key == pygame.K_s:
                    mover_abajo = False
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if (boton_reinicio.collidepoint(event.pos) and tanque_jugador.vivo == False) or (boton_reinicio_vic.collidepoint(event.pos) and not tanques_enemigos):
                    #Reiniciar el juego
                    tanques = []
                    mundo, tanque_jugador, tanques, tanques_enemigos = resetear_mundo()

        pygame.display.update()

pygame.quit()