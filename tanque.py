import math
import pygame
import constantes

class Tanque():
    def __init__(self, x, y, animaciones, energia, tipo_tanque, velocidad, disparo_cooldown):
        self.cañon = None
        self.energia = energia
        self.vivo = True
        #Imagen de la animación que se está mostrando actalmente
        self.frame_index = 0 
        #Tiempo que ha pasado desde la última actualización de la animación (en milisegundos)
        self.update_time = pygame.time.get_ticks()
        self.imagen = animaciones[self.frame_index]
        self.jugador_oculto = False
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
        self.disparo_cooldown = disparo_cooldown
        self.velocidad = velocidad
    
    # En tanque.py, reemplaza el método existente

    def tanques_enemigos(self, posicion_pantalla, obstaculos_tiles, arbustos, tanque_jugador, fortaleza, grupo_balas_enemigas, tanques, data_objetos):
        delta_x = 0
        delta_y = 0
        objetivo_actual = None
        distancia_minima = float('inf') # Empezamos con una distancia infinita

        # --- Lógica de Decisión de Objetivo ---
        
        # 1. Evaluar al jugador como posible objetivo
        # Comprobar si el jugador está oculto
        jugador_oculto = False
        for arbusto in arbustos:
            if arbusto[1].colliderect(tanque_jugador.forma):
                jugador_oculto = True
                break
        
        if not jugador_oculto:
            distancia_jugador = math.sqrt(((self.forma.centerx - tanque_jugador.forma.centerx)**2) + ((self.forma.centery - tanque_jugador.forma.centery)**2))
            # Comprobar línea de visión hacia el jugador
            if distancia_jugador < constantes.RANGO_VISION:
                campo_vision_jugador = ((self.forma.centerx, self.forma.centery), (tanque_jugador.forma.centerx, tanque_jugador.forma.centery))
                bloqueado = False
                for obstaculo in obstaculos_tiles:
                    if obstaculo[1].clipline(campo_vision_jugador):
                        bloqueado = True
                        break
                if not bloqueado:
                    objetivo_actual = tanque_jugador.forma
                    distancia_minima = distancia_jugador

        # 2. Evaluar la fortaleza como posible objetivo (siempre es visible, no se oculta)
        distancia_fortaleza = math.sqrt(((self.forma.centerx - fortaleza.rect.centerx)**2) + ((self.forma.centery - fortaleza.rect.centery)**2))
        # Comprobar línea de visión hacia la fortaleza
        if distancia_fortaleza < constantes.RANGO_VISION:
            campo_vision_fortaleza = ((self.forma.centerx, self.forma.centery), (fortaleza.rect.centerx, fortaleza.rect.centery))
            bloqueado = False
            for obstaculo in obstaculos_tiles:
                if obstaculo[1].clipline(campo_vision_fortaleza):
                    bloqueado = True
                    break
            if not bloqueado:
                # Si la fortaleza está más cerca que el jugador, se convierte en el nuevo objetivo
                if distancia_fortaleza < distancia_minima:
                    objetivo_actual = fortaleza.rect
                    distancia_minima = distancia_fortaleza

        # --- Lógica de Movimiento hacia el Objetivo ---
        if objetivo_actual:
            # Movimiento horizontal
            if abs(self.forma.centerx - objetivo_actual.centerx) > abs(self.forma.centery - objetivo_actual.centery):
                if self.forma.centerx > objetivo_actual.centerx:
                    delta_x = -self.velocidad
                elif self.forma.centerx < objetivo_actual.centerx:
                    delta_x = self.velocidad
            # Movimiento vertical
            else:
                if self.forma.centery > objetivo_actual.centery:
                    delta_y = -self.velocidad
                elif self.forma.centery < objetivo_actual.centery:
                    delta_y = self.velocidad

        # Mover el tanque (la lógica de colisiones que ya tenías funciona igual)
        self.movimiento(delta_x, delta_y, obstaculos_tiles, tanques)
            
        
        
    
    #Atacar al tanque del jugador
    def update_cañon_enemigo(self, tanque, cañon_tanque, obstaculos_tiles, arbustos, tanque_jugador, grupo_balas_enemigas):
        clipped_line = ()

        #Hacer que persigan al tanque del jugador
        for arbusto in arbustos:
            if arbusto[1].colliderect(tanque_jugador.forma):
                return  # El jugador está en arbusto, enemigo no lo ve
        ##Rango de vision del tanque enemigo
        distancia = math.sqrt(((self.forma.centerx - tanque_jugador.forma.centerx)**2) + ((self.forma.centery - tanque_jugador.forma.centery)**2))
        ##Campo de vision del tanque enemigo
        campo_vision = ((self.forma.centerx, self.forma.centery), (tanque_jugador.forma.centerx, tanque_jugador.forma.centery))
        ##Comprobar si hay obstaculos en el campo de visión
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].clipline(campo_vision):
                clipped_line = obstaculo[1].clipline(campo_vision)
                
        if not clipped_line and distancia <= constantes.RANGO_DISPARO and tanque.disparo_cooldown < (pygame.time.get_ticks() - self.ultimo_ataque):
            bala_enemiga = cañon_tanque.update(tanque, 2, True)
            if bala_enemiga:
                grupo_balas_enemigas.add(bala_enemiga)
        
        else:
            bala_enemiga = cañon_tanque.update(tanque, 2, False)
            if bala_enemiga:
                grupo_balas_enemigas.add(bala_enemiga)
    
    def update(self):
        if self.tipo_tanque == 0:
            if self.energia <= 0:
                self.energia = 0
                self.vivo = False
        
        if self.tipo_tanque >= 1:
            #Si el tanque fue eliminado, se muestra primero la animación de explosión
            if self.explosion:
                # PRIMERO, comprobamos si la animación ya terminó
                if self.frame_index_muerte >= len(self.animacion_muerte):
                    return False # Si ya terminó, avisamos para que se elimine el tanque

                # SI NO ha terminado, continuamos mostrando la animación
                cooldown_muerte = 150
                self.imagen = self.animacion_muerte[self.frame_index_muerte] # Esta línea ahora es segura
                if pygame.time.get_ticks() - self.update_time >= cooldown_muerte:
                    self.frame_index_muerte += 1
                    self.update_time = pygame.time.get_ticks()

            else:
                #Comprobar si el tanque esta muerto para iniciar la explosión
                if self.energia <= 0 and not self.explosion:
                    self.energia = 0
                    self.vivo = False
                    self.explosion = True
                    self.frame_index_muerte = 0
                    self.update_time = pygame.time.get_ticks() 
                
                #Si el tanque no esta en explosion, actualiza su animación normal
                else: # Usamos 'else' para evitar que se actualice la animación normal en el mismo frame que muere
                    cooldown_animacion = 125
                    self.imagen = self.animaciones[self.frame_index]
                    if pygame.time.get_ticks() - self.update_time >= cooldown_animacion:
                        self.frame_index += 1
                        self.update_time = pygame.time.get_ticks()
                    if self.frame_index >= len(self.animaciones):
                        self.frame_index = 0
                
            return True

    def dibujar(self, pantalla, posicion_pantalla):
        imagen_rotada = pygame.transform.rotate(self.imagen, -self.rotate)
        rect_rotado = imagen_rotada.get_rect(center=(
            self.forma.centerx - posicion_pantalla[0],
            self.forma.centery - posicion_pantalla[1]
        ))
        pantalla.blit(imagen_rotada, rect_rotado)

        # --- Dibujar el cañón si existe ---
        if self.cañon:
            # Alinear el cañón con el centro del tanque
            self.cañon.rect.center = self.forma.center
            self.cañon.dibujar(pantalla, posicion_pantalla)
    
    def movimiento(self, delta_x, delta_y, obstaculos_tiles, tanques):
        # 1. Actualizar rotación según dirección (esto se queda igual)
        if delta_x > 0:
            self.rotate = 0
        if delta_x < 0:
            self.rotate = 180
        if delta_y > 0:
            self.rotate = 90
        if delta_y < 0:
            self.rotate = 270
        
        # 2. Mover en X y resolver colisiones (esto se queda igual)
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
        
        # Límites del mapa (esto se queda igual)
        self.forma.left = max(0, self.forma.left)
        self.forma.right = min(constantes.MAPA_ANCHO, self.forma.right)
        self.forma.top = max(0, self.forma.top)
        self.forma.bottom = min(constantes.MAPA_ALTO, self.forma.bottom)