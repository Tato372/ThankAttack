import pygame.sprite

class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, font, color):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.contador = 0 # Renombré la variable para evitar la 'ñ'
    
    # MODIFICADO: ya no recibe posicion_pantalla
    def update(self):
        # Mover el texto hacia arriba
        self.rect.y -= 1
        # Eliminar el texto después de un tiempo
        self.contador += 1
        if self.contador >= 30: # Le damos un poco más de tiempo en pantalla
            self.kill()