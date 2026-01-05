# src/entities/bullet.py
import pygame
from pygame.math import Vector2

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, damage, image, speed=None, lifetime=1500):
        super().__init__()
        
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        
        self.direction = direction
        self.damage = damage
        self.speed = speed if speed else 600
        
        # 寿命管理 (ミリ秒)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = lifetime 

    def update(self, dt):
        # 移動処理
        # ★修正: dt はすでに「秒」なので、そのまま掛ける
        if self.direction.length() > 0:
            move_amount = self.direction * self.speed * dt
            self.pos += move_amount
        
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # 寿命チェック
        # spawn_time はミリ秒なので、現在時刻(ミリ秒)と比較
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time > self.lifetime:
            self.kill()