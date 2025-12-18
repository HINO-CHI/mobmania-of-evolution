# src/entities/enemy.py
import pygame
from pygame.math import Vector2
import config
import random
import time # 追加

class Enemy(pygame.sprite.Sprite):
    def __init__(self, start_pos, player):
        super().__init__()
        self.stats = {
            "speed": random.randint(100, 180),
            "hp": 10,
            "size": 30,
            "color": config.GREEN
        }
        
        # --- 追加: 時間計測用 ---
        self.spawn_time = time.time() # 生まれた時間 (Unix Time)
        self.death_time = 0           # 死んだ時間
        # ---------------------

        self.player = player
        self.image = pygame.Surface((self.stats["size"], self.stats["size"]))
        self.image.fill(self.stats["color"])
        self.rect = self.image.get_rect()
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
    def update(self, dt):
        direction = self.player.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * self.stats["speed"] * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))