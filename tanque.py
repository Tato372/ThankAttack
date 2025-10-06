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
        self.modo_evasion = 0
        
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

        # REGLA 4: Si está explotando, no hacer nada más.
        if self.explosion:
            return

        # 1. DECIDIR OBJETIVO DE MOVIMIENTO
        objetivo_movimiento = fortaleza.rect # REGLA 1: Por defecto, ir a la fortaleza
        
        dist_jugador = math.sqrt((self.forma.centerx - jugador.forma.centerx)**2 + (self.forma.centery - jugador.forma.centery)**2)
        
        # REGLA 2 Y 3: Si el jugador es visible y está en rango, cambiar de objetivo
        if dist_jugador < constantes.RANGO_AGGRO_JUGADOR and self.es_visible(jugador, arbustos, obstaculos):
            objetivo_movimiento = jugador.forma

        # --- INICIO DEL BLOQUE: LÓGICA DE RETIRADA SI ESTÁ ATASCADO ---
        # 1. Comprobar los 4 lados para ver si estamos en un callejón sin salida
        bloqueos = 0
        direcciones = [(0, -self.velocidad*2), (0, self.velocidad*2), (-self.velocidad*2, 0), (self.velocidad*2, 0)]
        for dx, dy in direcciones:
            sensor = self.forma.copy()
            sensor.move_ip(dx, dy)
            if any(obs[1].colliderect(sensor) for obs in obstaculos) or \
               any(t is not self and t.forma.colliderect(sensor) for t in todos_los_tanques):
                bloqueos += 1
        
        # 2. Si 3 o más lados están bloqueados, forzar retirada
        if bloqueos >= 3:
            # ¡CORRECCIÓN! Inicializamos las variables aquí para que siempre existan.
            delta_x, delta_y = 0, 0
            
            # Moverse en la dirección contraria a la que se está mirando
            if self.rotate == 0:
                delta_x = -self.velocidad
            elif self.rotate == 180:
                delta_x = self.velocidad
            elif self.rotate == 90:
                delta_y = -self.velocidad
            elif self.rotate == 270:
                delta_y = self.velocidad
            
            self.movimiento(delta_x, delta_y, obstaculos, todos_los_tanques)
            return
        # --- FIN DEL BLOQUE ---
        # 2. CALCULAR MOVIMIENTO IDEAL Y EVASIÓN
        delta_x, delta_y = 0, 0
        dx_ideal, dy_ideal = 0, 0
        
        # Solo nos movemos si no estamos ya muy cerca del objetivo
        if math.sqrt((self.forma.centerx - objetivo_movimiento.centerx)**2 + (self.forma.centery - objetivo_movimiento.centery)**2) > self.forma.width:
            # Calcular dirección ideal (sin diagonales)
            if abs(self.forma.centerx - objetivo_movimiento.centerx) > abs(self.forma.centery - objetivo_movimiento.centery):
                if self.forma.centerx > objetivo_movimiento.centerx: dx_ideal = -self.velocidad
                elif self.forma.centerx < objetivo_movimiento.centerx: dx_ideal = self.velocidad
            elif abs(self.forma.centery - objetivo_movimiento.centery) > 0:
                if self.forma.centery > objetivo_movimiento.centery: dy_ideal = -self.velocidad
                elif self.forma.centery < objetivo_movimiento.centery: dy_ideal = self.velocidad
        
            # --- INICIO DE LA LÓGICA DE EVASIÓN ---
            sensor = self.forma.copy()
            sensor.move_ip(dx_ideal * 2, dy_ideal * 2)
            
            obstaculo_en_frente = next((obs for obs in obstaculos if sensor.colliderect(obs[1])), None)
            
            if obstaculo_en_frente:
                # Si hay un muro en frente, intentar moverse en la dirección perpendicular
                if dx_ideal != 0: # Si el bloqueo es horizontal, intentar mover vertical
                    if self.forma.centery > objetivo_movimiento.centery: delta_y = -self.velocidad
                    else: delta_y = self.velocidad
                else: # Si el bloqueo es vertical, intentar mover horizontal
                    if self.forma.centerx > objetivo_movimiento.centerx: delta_x = -self.velocidad
                    else: delta_x = self.velocidad
            else:
                # Si el camino está libre, seguir la ruta ideal
                delta_x, delta_y = dx_ideal, dy_ideal
            # --- FIN DE LA LÓGICA DE EVASIÓN ---

        # 3. LÓGICA DE DISPARO
        objetivo_disparo = None
        if dist_jugador < constantes.RANGO_DISPARO and self.es_visible(jugador, arbustos, obstaculos):
            objetivo_disparo = jugador.forma
        else:
            dist_fortaleza = math.sqrt((self.forma.centerx - fortaleza.rect.centerx)**2 + (self.forma.centery - fortaleza.rect.centery)**2)
            if dist_fortaleza < constantes.RANGO_DISPARO and self.es_visible(fortaleza, [], obstaculos):
                objetivo_disparo = fortaleza.rect

        if objetivo_disparo and (pygame.time.get_ticks() - self.ultimo_ataque) >= self.disparo_cooldown:
            dx_shot = objetivo_disparo.centerx - self.forma.centerx
            dy_shot = objetivo_disparo.centery - self.forma.centery
            if abs(dx_shot) > abs(dy_shot): self.rotate = 0 if dx_shot > 0 else 180
            else: self.rotate = 90 if dy_shot > 0 else 270

            bala = self.cañon.update(self, 2, True)
            if bala:
                balas_enemigas.add(bala)
                self.ultimo_ataque = pygame.time.get_ticks()
        
        # 4. EVITAR ALIADOS antes del movimiento final
        if delta_x != 0 or delta_y != 0:
            sensor = self.forma.copy()
            sensor.move_ip(delta_x, delta_y)
            if any(t is not self and t.tipo_tanque >= 1 and sensor.colliderect(t.forma) for t in todos_los_tanques):
                delta_x, delta_y = 0, 0 # Pausa para no chocar

        # 5. EJECUTAR MOVIMIENTO
        self.movimiento(delta_x, delta_y, obstaculos, todos_los_tanques)
    
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