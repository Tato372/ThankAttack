import math
import pygame
import constantes

class Tanque():
    def __init__(self, x, y, animaciones, energia, tipo_tanque):
        self.energia = energia
        self.vivo = True
        #Imagen de la animación que se está mostrando actalmente
        self.frame_index = 0 
        #Tiempo que ha pasado desde la última actualización de la animación (en milisegundos)
        self.update_time = pygame.time.get_ticks()
        self.imagen = animaciones[self.frame_index]
        self.forma = self.imagen.get_rect()
        self.forma.center = (x, y)
        self.rotate = 0
        self.animaciones = animaciones
        self.puntaje = 0
        self.tipo_tanque = tipo_tanque
        self.atacado = False
        self.ultimo_ataque = pygame.time.get_ticks()
        self.explosion = False
        self.animacion_muerte = []
        self.frame_index_muerte = 0
    
    def tanques_enemigos(self, posicion_pantalla, obstaculos_tiles, tanque_jugador, grupo_balas_enemigas, tanques, data_mundo):
        clipped_line = ()
        delta_x = 0
        delta_y = 0
        #Reposicionar los tanques enemigos basado en la posicion de la camara
        self.forma.x += posicion_pantalla[0]
        self.forma.y += posicion_pantalla[1]
        
        #Hacer que persigan al tanque del jugador
        ##Rango de vision del tanque enemigo
        distancia = math.sqrt(((self.forma.centerx - tanque_jugador.forma.centerx)**2) + ((self.forma.centery - tanque_jugador.forma.centery)**2))
        ##Campo de vision del tanque enemigo
        campo_vision = ((self.forma.centerx, self.forma.centery), (tanque_jugador.forma.centerx, tanque_jugador.forma.centery))
        ##Comprobar si hay obstaculos en el campo de visión
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].clipline(campo_vision):
                clipped_line = obstaculo[1].clipline(campo_vision)
                
        ##Rango de distancia entre el tanque enemigo y el tanque del jugador (Campo de vision del tanque enemigo)
        if not clipped_line and distancia < constantes.RANGO_VISION:
            ## Perseguir a la derecha e izquierda
            if abs(self.forma.centerx - tanque_jugador.forma.centerx) > abs(self.forma.centery - tanque_jugador.forma.centery):
                if self.forma.centerx > tanque_jugador.forma.centerx:
                    delta_x = -constantes.VELOCIDAD_ENEMIGO
                elif self.forma.centerx < tanque_jugador.forma.centerx:
                    delta_x = constantes.VELOCIDAD_ENEMIGO
            ## Perseguir arriba y abajo
            else:
                if self.forma.centery > tanque_jugador.forma.centery:
                    delta_y = -constantes.VELOCIDAD_ENEMIGO
                elif self.forma.centery < tanque_jugador.forma.centery:
                    delta_y = constantes.VELOCIDAD_ENEMIGO
        
        self.movimiento(delta_x, delta_y, obstaculos_tiles, tanques)
        
        #Datos para dar el funcionamiento con HASKELL
        ##Obtener el tile en el que está el tanque del jugador
        ubicacion_jugador = 214 #Se inicializa en el tile de spawn
        mapa = data_mundo
        
        
        
    
    #Atacar al tanque del jugador
    def update_cañon_enemigo(self, tanque, cañon_tanque, obstaculos_tiles, tanque_jugador, grupo_balas_enemigas):
        clipped_line = ()
        #Hacer que persigan al tanque del jugador
        ##Rango de vision del tanque enemigo
        distancia = math.sqrt(((self.forma.centerx - tanque_jugador.forma.centerx)**2) + ((self.forma.centery - tanque_jugador.forma.centery)**2))
        ##Campo de vision del tanque enemigo
        campo_vision = ((self.forma.centerx, self.forma.centery), (tanque_jugador.forma.centerx, tanque_jugador.forma.centery))
        ##Comprobar si hay obstaculos en el campo de visión
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].clipline(campo_vision):
                clipped_line = obstaculo[1].clipline(campo_vision)
                
        if not clipped_line and distancia <= constantes.RANGO_DISPARO and constantes.DISPARO_COOLDOWN < (pygame.time.get_ticks() - self.ultimo_ataque):
            bala_enemiga = cañon_tanque.uptade(tanque, 2, True)
            if bala_enemiga:
                grupo_balas_enemigas.add(bala_enemiga)
        
        else:
            bala_enemiga = cañon_tanque.uptade(tanque, 2, False)
            if bala_enemiga:
                grupo_balas_enemigas.add(bala_enemiga)
    
    def update(self):
        if self.tipo_tanque == 1:
            if self.energia <= 0:
                self.energia = 0
                self.vivo = False
        
        if self.tipo_tanque == 2:
            #Si el tanque fue eliminado, se muestra primero la animación de explosión
            if self.explosion:
                cooldown_muerte = 150
                self.imagen = self.animacion_muerte[self.frame_index_muerte]
                if pygame.time.get_ticks() - self.update_time >= cooldown_muerte:
                    self.frame_index_muerte += 1
                    self.update_time = pygame.time.get_ticks()
                
                #Si la animación de muerte termina, se elimina el tanque
                if self.frame_index_muerte >= len(self.animacion_muerte):
                    return False 

            else:
                #Comprobar si el tanque esta muerto
                if self.energia <= 0 and not self.explosion:
                    self.energia = 0
                    self.vivo = False
                    self.explosion = True
                    self.frame_index_muerte = 0
                    self.update_time = pygame.time.get_ticks() 
                
                #Si el tanque no esta en explosion(cuando muere se genera primero la explosion), actualiza su animación normal
                if not self.explosion:
                    cooldown_animacion = 125
                    self.imagen = self.animaciones[self.frame_index]
                    if pygame.time.get_ticks() - self.update_time >= cooldown_animacion:
                        self.frame_index += 1
                        self.update_time = pygame.time.get_ticks()
                    if self.frame_index >= len(self.animaciones):
                        self.frame_index = 0
                
            return True
                    
    def dibujar(self, pantalla):
        imagen_rotate = pygame.transform.rotate(self.imagen, self.rotate) 
        pantalla.blit(imagen_rotate, self.forma)
        #Muestra el cuadro del tanque, funciona como hitbox
        ##pygame.draw.rect(pantalla, constantes.AMARILLO , self.forma, 1)
    
    def movimiento(self, delta_x, delta_y, obstaculos_tiles, tanques):
        posicion_pantalla = [0, 0]
        
        if delta_x > 0:
            self.rotate = 0
        if delta_x < 0:
            self.rotate = 180
        if delta_y > 0:
            self.rotate = 270
        if delta_y < 0:
            self.rotate = 90
        
        self.forma.x += delta_x
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].colliderect(self.forma):
                if delta_x > 0:
                    self.forma.right = obstaculo[1].left
                if delta_x < 0:
                    self.forma.left = obstaculo[1].right
        
        for tanque in tanques:
            if tanque != self and tanque.forma.colliderect(self.forma):
                if delta_x > 0:
                    self.forma.right = tanque.forma.left
                if delta_x < 0:
                    self.forma.left = tanque.forma.right

        self.forma.y += delta_y
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].colliderect(self.forma):
                if delta_y > 0:
                    self.forma.bottom = obstaculo[1].top
                if delta_y < 0:
                    self.forma.top = obstaculo[1].bottom
        
        for tanque in tanques:
            if tanque != self and tanque.forma.colliderect(self.forma):
                if delta_y > 0:
                    self.forma.bottom = tanque.forma.top
                if delta_y < 0:
                    self.forma.top = tanque.forma.bottom
        
        #Logica que solo aplica al tanque del jugador
        if self.tipo_tanque == 1:
            #Actualizar la pantalla segun la posicion del jugador
            #Definir una zona de tolerancia antes de mover la cámara
            margen_tolerancia = 0
        
            # Mover la cámara a la izquierda o derecha solo si se sale de la zona de tolerancia
            if self.forma.right > (constantes.ANCHO_VENTANA - constantes.LIMITE_PANTALLA - margen_tolerancia):
                posicion_pantalla[0] = (constantes.ANCHO_VENTANA - constantes.LIMITE_PANTALLA) - self.forma.right
                self.forma.right = constantes.ANCHO_VENTANA - constantes.LIMITE_PANTALLA
            elif self.forma.left < (constantes.LIMITE_PANTALLA + margen_tolerancia):
                posicion_pantalla[0] = constantes.LIMITE_PANTALLA - self.forma.left
                self.forma.left = constantes.LIMITE_PANTALLA
            
            # Mover la cámara arriba o abajo solo si se sale de la zona de tolerancia
            if self.forma.bottom > (constantes.ALTO_VENTANA - constantes.LIMITE_PANTALLA - margen_tolerancia):
                posicion_pantalla[1] = (constantes.ALTO_VENTANA - constantes.LIMITE_PANTALLA) - self.forma.bottom
                self.forma.bottom = constantes.ALTO_VENTANA - constantes.LIMITE_PANTALLA
            elif self.forma.top < (constantes.LIMITE_PANTALLA + margen_tolerancia):
                posicion_pantalla[1] = constantes.LIMITE_PANTALLA - self.forma.top
                self.forma.top = constantes.LIMITE_PANTALLA
            
            return posicion_pantalla