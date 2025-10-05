import pygame

class Fortaleza(pygame.sprite.Sprite):
    def __init__(self, x, y, imagen):
        pygame.sprite.Sprite.__init__(self)
        self.image = imagen
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.energia = 200 # Le damos una buena cantidad de vida

    def dibujar(self, pantalla, posicion_pantalla):
        # Dibuja la fortaleza ajustando su posición según la cámara
        pantalla.blit(self.image, (self.rect.x - posicion_pantalla[0], self.rect.y - posicion_pantalla[1]))