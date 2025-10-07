import random
import math
import pygame
import constantes

class Weapon():
    def __init__(self, imagen, imagen_bala):
        self.imagen_original = imagen
        self.angulo = 0
        self.imagen = pygame.transform.rotate(self.imagen_original, self.angulo)
        self.forma = self.imagen.get_rect()
        self.rect = self.forma
        self.imagen_bala = imagen_bala
        self.disparada = False
        self.ultimo_disparo = pygame.time.get_ticks()

    def update(self, tanque, tipo, en_rango):
        bala = None
        disparo_cooldown = tanque.disparo_cooldown
        self.forma.center = tanque.forma.center
        self.angulo = tanque.rotate
        self.imagen = pygame.transform.rotate(self.imagen_original, self.angulo)
        
        #Disparo del jugador o del enemigo
        if tipo == 1:
        #Detectar el espacio para disparar
            if pygame.key.get_pressed()[pygame.K_SPACE] and self.disparada == False and (pygame.time.get_ticks() - self.ultimo_disparo) >= disparo_cooldown:
                bala = Bullet(self.imagen_bala, tanque, self.angulo)
                self.disparada = True
                self.ultimo_disparo = pygame.time.get_ticks()
            
            #Resetear el disparo
            if pygame.key.get_pressed()[pygame.K_SPACE] == False:
                self.disparada = False
                
            return bala

        if tipo == 2:  # enemigo
            if en_rango:
                tiempo_actual = pygame.time.get_ticks()
                if tiempo_actual - self.ultimo_disparo >= tanque.disparo_cooldown:
                    bala = Bullet(self.imagen_bala, tanque, self.angulo)
                    self.ultimo_disparo = tiempo_actual  # reinicia el cooldown
                return bala

    def dibujar(self, pantalla, posicion_pantalla):
        # Ajustar la posición según la cámara
        imagen_rotada = pygame.transform.rotate(self.imagen_original, -self.angulo)
        rect_rotado = imagen_rotada.get_rect(center=(
            self.forma.centerx - posicion_pantalla[0],
            self.forma.centery - posicion_pantalla[1]
        ))
        pantalla.blit(imagen_rotada, rect_rotado)
        #Muestra el cuadro del cañon (funciona como hitbox)
        #pygame.draw.rect(pantalla, constantes.ROJO, self.forma, 1)
        
class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, tanque, angulo):
        pygame.sprite.Sprite.__init__(self)
        self.imagen_original = image
        self.angulo = angulo
        self.image = pygame.transform.rotate(self.imagen_original, self.angulo)
        self.rect = self.image.get_rect()
        self.rect.center = tanque.forma.center
        #Calculo de la velocidad
        self.delta_x = math.cos(math.radians(self.angulo)) * constantes.VELOCIDAD_BALA
        self.delta_y = math.sin(math.radians(-self.angulo)) * constantes.VELOCIDAD_BALA
        
    def update(self, tanques, obstaculos_tiles):
        daño = 0
        posicion_daño = None
        self.rect.x += self.delta_x
        self.rect.y -= self.delta_y
        
        #Verificar si hay colision con un tanque
        for tanque in tanques:
            if tanque.forma.colliderect(self.rect):
                daño = 50
                posicion_daño = (tanque.forma)
                tanque.energia -= daño
                self.kill()
                break
        
        #Verificar si hay colision con un obstaculo
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].colliderect(self.rect):
                # Si el obstáculo es destructible
                if obstaculo[4] > 0:
                    obstaculo[4] -= 1  # Restar 1 bala
                    if obstaculo[4] == 0:
                        obstaculos_tiles.remove(obstaculo)
                # Si es indestructible, no hacemos nada más
                self.kill()  # La bala siempre se destruye al impactar
                break
        
        return daño, posicion_daño

    def dibujar(self, pantalla, posicion_pantalla):
        pantalla.blit(self.image, (self.rect.x - posicion_pantalla[0], self.rect.y - posicion_pantalla[1]))
        #Muestra el cuadro de la bala (funciona como hitbox)
        #pygame.draw.rect(pantalla, constantes.COLOR_CAÑON, self.rect, 1)
    
    