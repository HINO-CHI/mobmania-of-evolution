# src/entities/enemy.py
import pygame
from pygame.math import Vector2
import config
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, start_pos, player):
        super().__init__()
        # 将来的にはここで遺伝子情報(stats)を受け取ります
        self.stats = {
            "speed": random.randint(100, 200), # ランダムな速さ
            "hp": 10,
            "size": 30,
            "color": config.GREEN # 緑色
        }
        
        # プレイヤーへの参照（追いかけるため）
        self.player = player
        
        # 見た目
        self.image = pygame.Surface((self.stats["size"], self.stats["size"]))
        self.image.fill(self.stats["color"])
        self.rect = self.image.get_rect()
        
        # 位置
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
    def update(self, dt):
        # プレイヤーに向かうベクトルを計算
        # プレイヤー位置 - 自分位置 = 自分からプレイヤーへの矢印
        direction = self.player.pos - self.pos
        
        if direction.length() > 0:
            direction = direction.normalize()
            
        # 移動
        self.pos += direction * self.stats["speed"] * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))