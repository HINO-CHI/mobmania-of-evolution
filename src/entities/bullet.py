# src/entities/bullet.py
import pygame
from pygame.math import Vector2
import config

class Bullet(pygame.sprite.Sprite):
    # damage引数を追加
    def __init__(self, pos, direction, damage):
        super().__init__()
        self.image = pygame.Surface((config.BULLET_SIZE, config.BULLET_SIZE))
        self.image.fill(config.BULLET_COLOR)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        
        self.pos = Vector2(pos)
        self.vel = direction * config.BULLET_SPEED
        self.damage = damage  # <--- 威力を記憶
        
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if pygame.time.get_ticks() - self.spawn_time > config.BULLET_LIFETIME:
            self.kill()