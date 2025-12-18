import pygame
from pygame.math import Vector2
import config

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, direction):
        super().__init__()
        self.image = pygame.Surface((config.BULLET_SIZE, config.BULLET_SIZE))
        self.image.fill(config.BULLET_COLOR)
        self.rect = self.image.get_rect()
        
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # 方向を正規化して速度を決定
        self.velocity = direction.normalize() * config.BULLET_SPEED

    def update(self, dt):
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # 画面外に出たら削除
        if (self.rect.right < 0 or self.rect.left > config.SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > config.SCREEN_HEIGHT):
            self.kill()