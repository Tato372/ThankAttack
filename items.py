import pygame.sprite


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_item, lista_animaciones):
        pygame.sprite.Sprite.__init__(self)
        self.tipo_item = tipo_item # 0 = moneda, 1 = pocion
        self.lista_animaciones = lista_animaciones
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.lista_animaciones[self.frame_index]       
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
    def update(self, posicion_pantalla, tanque):
        #Comprobar la colision entre el personaje y el item
        if self.rect.colliderect(tanque.forma):
            #Si son monedas
            if self.tipo_item == 0:
                tanque.puntaje += 20
            #Si son pociones
            elif self.tipo_item == 1:
                tanque.energia += 30
                if tanque.energia > 90:
                    tanque.energia = 90
            self.kill()
            
        cooldown_animacion = 200
        self.image = self.lista_animaciones[self.frame_index]
        if pygame.time.get_ticks() - self.update_time >= cooldown_animacion:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        if self.frame_index >= len(self.lista_animaciones):
            self.frame_index = 0