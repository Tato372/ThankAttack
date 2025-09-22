import pygame.sprite

class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, font, color):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.contadore = 0
    
    def update(self, posicion_pantalla):
        #Reposicionar basado en la posicion de la camara o pantalla
        self.rect.x += posicion_pantalla[0]
        self.rect.y += posicion_pantalla[1]
        
        self.rect.y -= 2
        self.contadore += 1
        if self.contadore >= 25:
            self.kill()