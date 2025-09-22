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
        self.imagen_bala = imagen_bala
        self.disparada = False
        self.ultimo_disparo = pygame.time.get_ticks()
        
    def uptade(self, tanque, tipo, en_rango):
        bala = None
        disparo_cooldown = constantes.DISPARO_COOLDOWN
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

        if tipo == 2:
            #Solo dispara si el tanque del jugador esta en rango
            if en_rango == True:
                if self.disparada == False and (pygame.time.get_ticks() - self.ultimo_disparo) >= disparo_cooldown:
                    bala = Bullet(self.imagen_bala, tanque, self.angulo)
                    self.disparada = True
                    self.ultimo_disparo = pygame.time.get_ticks()
                
                #Resetear el disparo
                if self.disparada == True:
                    self.disparada = False
                
                return bala
            
    def dibujar(self, pantalla):
        pantalla.blit(self.imagen, self.forma)
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
        self.delta_y = math.sin(math.radians(self.angulo)) * constantes.VELOCIDAD_BALA
        
    def update(self, tanques, obstaculos_tiles):
        daño = 0
        posicion_daño = None
        self.rect.x += self.delta_x
        self.rect.y -= self.delta_y
        
        #Eliminar la bala si sale de la pantalla
        if self.rect.right < 0 or self.rect.left > constantes.ANCHO_VENTANA or self.rect.top > constantes.ALTO_VENTANA or self.rect.bottom < 0:
            self.kill()
        
        #Verificar si hay colision con un tanque
        for tanque in tanques:
            if tanque.forma.colliderect(self.rect):
                daño = 15 + random.randint(0, 10)
                posicion_daño = (tanque.forma)
                tanque.energia -= daño
                self.kill()
                break
        
        #Verificar si hay colision con un obstaculo
        for obstaculo in obstaculos_tiles:
            if obstaculo[1].colliderect(self.rect):
                self.kill()
                break
        
        return daño, posicion_daño
        
    def dibujar(self, pantalla):
        pantalla.blit(self.image, self.rect)
        #Muestra el cuadro de la bala (funciona como hitbox)
        #pygame.draw.rect(pantalla, constantes.COLOR_CAÑON, self.rect, 1)
    
    