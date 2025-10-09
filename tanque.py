import math
import pygame
import constantes
import random

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
        print(f"Tanque CREADO -> Tipo: {tipo_tanque}, Velocidad Asignada: {self.velocidad}")
        self.modo_evasion = 0
        # <-- CAMBIO: Atributos para gestionar efectos de bonus -->
        # Para el jugador
        self.escudo_activo = False
        self.escudo_tiempo_final = 0
        self.potenciado_activo = False
        self.potenciado_tiempo_final = 0
        self.boost_activo = False
        self.boost_tiempo_final = 0
        # Para enemigos (afectados por el reloj)
        self.ralentizado = False
        self.ralentizado_tiempo_final = 0
        # Atributos para la interpolación del movimiento en red
        self.target_pos = (x, y)
        self.last_pos = (x, y)
        self.last_update_time = pygame.time.get_ticks()
        
    def es_visible(self, objetivo, arbustos, obstaculos):
        """Comprueba si un objetivo es visible, considerando arbustos y muros."""
        
        # Corrección: Usar el rectángulo correcto (.forma para tanques, .rect para fortaleza)
        rect_objetivo = getattr(objetivo, 'forma', getattr(objetivo, 'rect', None))
        if not rect_objetivo:
            return False

        # 1. Comprobar si el objetivo está en un arbusto
        objetivo_en_arbusto = None
        for arbusto in arbustos:
            if arbusto[1].colliderect(rect_objetivo):
                objetivo_en_arbusto = arbusto
                break
        
        if objetivo_en_arbusto:
            if not self.forma.colliderect(objetivo_en_arbusto[1]):
                return False

        # 2. Comprobar línea de visión a través de muros indestructibles
        campo_vision = ((self.forma.centerx, self.forma.centery), (rect_objetivo.centerx, rect_objetivo.centery))
        for obs in obstaculos:
            if obs[4] <= 0 and obs[1].clipline(campo_vision):
                return False
        
        return True

    def actualizar_ia_pixel(self, jugador, fortaleza, obstaculos, todos_los_tanques, arbustos, balas_enemigas):
        """IA definitiva con movimiento fluido por píxeles y lógica de evasión."""

        if self.explosion:
            return

        # CORREGIDO: Usar 'velocidad_actual' en toda la función para respetar las stats y bonus
        velocidad_actual = self.velocidad / 2 if self.ralentizado else self.velocidad
        cooldown_actual = self.disparo_cooldown * 2 if self.ralentizado else self.disparo_cooldown

        objetivo_movimiento = fortaleza.rect
        dist_jugador = math.sqrt((self.forma.centerx - jugador.forma.centerx)**2 + (self.forma.centery - jugador.forma.centery)**2)
        if dist_jugador < constantes.RANGO_AGGRO_JUGADOR and self.es_visible(jugador, arbustos, obstaculos):
            objetivo_movimiento = jugador.forma

        bloqueos = 0
        direcciones = [(0, -velocidad_actual), (0, velocidad_actual), (-velocidad_actual, 0), (velocidad_actual, 0)]
        for dx, dy in direcciones:
            sensor = self.forma.copy()
            sensor.move_ip(dx, dy)
            if any(obs[1].colliderect(sensor) for obs in obstaculos) or \
                any(t is not self and t.forma.colliderect(sensor) for t in todos_los_tanques):
                bloqueos += 1
        
        if bloqueos >= 3:
            delta_x, delta_y = 0, 0
            if self.rotate == 0:
                delta_x = -velocidad_actual
            elif self.rotate == 180:
                delta_x = velocidad_actual
            elif self.rotate == 90:
                delta_y = -velocidad_actual
            elif self.rotate == 270:
                delta_y = velocidad_actual
            
            self.movimiento(delta_x, delta_y, obstaculos, todos_los_tanques)
            return

        delta_x, delta_y = 0, 0
        dx_ideal, dy_ideal = 0, 0
        
        if math.sqrt((self.forma.centerx - objetivo_movimiento.centerx)**2 + (self.forma.centery - objetivo_movimiento.centery)**2) > self.forma.width:
            if abs(self.forma.centerx - objetivo_movimiento.centerx) > abs(self.forma.centery - objetivo_movimiento.centery):
                if self.forma.centerx > objetivo_movimiento.centerx: dx_ideal = -velocidad_actual # CORREGIDO
                elif self.forma.centerx < objetivo_movimiento.centerx: dx_ideal = velocidad_actual  # CORREGIDO
            elif abs(self.forma.centery - objetivo_movimiento.centery) > 0:
                if self.forma.centery > objetivo_movimiento.centery: dy_ideal = -velocidad_actual # CORREGIDO
                elif self.forma.centery < objetivo_movimiento.centery: dy_ideal = velocidad_actual  # CORREGIDO
        
        sensor = self.forma.copy()
        sensor.move_ip(dx_ideal, dy_ideal)
        
        obstaculo_en_frente = next((obs for obs in obstaculos if sensor.colliderect(obs[1])), None)
        
        if obstaculo_en_frente:
            if dx_ideal != 0:
                if self.forma.centery > objetivo_movimiento.centery: delta_y = -velocidad_actual # CORREGIDO
                else: delta_y = velocidad_actual # CORREGIDO
            else:
                if self.forma.centerx > objetivo_movimiento.centerx: delta_x = -velocidad_actual # CORREGIDO
                else: delta_x = velocidad_actual # CORREGIDO
        else:
            delta_x, delta_y = dx_ideal, dy_ideal

        objetivo_disparo = None
        if dist_jugador < constantes.RANGO_DISPARO and self.es_visible(jugador, arbustos, obstaculos):
            objetivo_disparo = jugador.forma
        else:
            dist_fortaleza = math.sqrt((self.forma.centerx - fortaleza.rect.centerx)**2 + (self.forma.centery - fortaleza.rect.centery)**2)
            if dist_fortaleza < constantes.RANGO_DISPARO and self.es_visible(fortaleza, [], obstaculos):
                objetivo_disparo = fortaleza.rect

        if objetivo_disparo and (pygame.time.get_ticks() - self.ultimo_ataque) >= cooldown_actual:
            dx_shot = objetivo_disparo.centerx - self.forma.centerx
            dy_shot = objetivo_disparo.centery - self.forma.centery
            if abs(dx_shot) > abs(dy_shot): self.rotate = 0 if dx_shot > 0 else 180
            else: self.rotate = 90 if dy_shot > 0 else 270

            bala = self.cañon.update(self, 2, True)
            if bala:
                balas_enemigas.add(bala)
                self.ultimo_ataque = pygame.time.get_ticks()
        
        if delta_x != 0 or delta_y != 0:
            sensor = self.forma.copy()
            sensor.move_ip(delta_x, delta_y)
            if any(t is not self and t.tipo_tanque >= 1 and sensor.colliderect(t.forma) for t in todos_los_tanques):
                delta_x, delta_y = 0, 0

        self.movimiento(delta_x, delta_y, obstaculos, todos_los_tanques)
    
    # <-- CAMBIO: Nuevo método para actualizar los efectos de los bonus -->
    def actualizar_efectos_bonus(self):
        tiempo_actual = pygame.time.get_ticks()
        # Escudo del jugador
        if self.escudo_activo and tiempo_actual > self.escudo_tiempo_final:
            self.escudo_activo = False
        # Disparo potenciado del jugador
        if self.potenciado_activo and tiempo_actual > self.potenciado_tiempo_final:
            self.potenciado_activo = False
        # Boost del jugador
        if self.boost_activo and tiempo_actual > self.boost_tiempo_final:
            self.boost_activo = False
            self.velocidad = self.velocidad_original
            # Restaurar tamaño
            centro = self.forma.center
            self.animaciones = self.animaciones_originales
            self.imagen = self.animaciones[self.frame_index]
            self.forma = self.imagen.get_rect(center=centro)
        # Ralentización del enemigo
        if self.ralentizado and tiempo_actual > self.ralentizado_tiempo_final:
            self.ralentizado = False
            
    def update(self):
        self.actualizar_efectos_bonus()
        
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
        
        # <-- CAMBIO: Dibujar un efecto visual para el escudo -->
        if self.escudo_activo:
            escudo_surf = pygame.Surface(rect_rotado.size, pygame.SRCALPHA)
            pygame.draw.circle(escudo_surf, (100, 100, 255, 90), (rect_rotado.width // 2, rect_rotado.height // 2), rect_rotado.width // 2)
            pantalla.blit(escudo_surf, rect_rotado.topleft)

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

    # --- PEGA EL NUEVO MÉTODO COMPLETO AQUÍ ---
    def interpolate_position(self):
        # Interpolar suavemente hacia la posición objetivo del servidor
        interp_time = 100 # ms, un poco más que el intervalo del servidor (1000/20 = 50ms)
        
        tiempo_desde_update = pygame.time.get_ticks() - self.last_update_time
        t = min(1.0, tiempo_desde_update / interp_time)

        # Interpolar linealmente (Lerp)
        new_x = self.last_pos[0] + (self.target_pos[0] - self.last_pos[0]) * t
        new_y = self.last_pos[1] + (self.target_pos[1] - self.last_pos[1]) * t
        
        self.forma.center = (new_x, new_y)