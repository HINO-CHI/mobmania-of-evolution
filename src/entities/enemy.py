# src/entities/enemy.py
import pygame
from pygame.math import Vector2
import config
import random
import time

class Enemy(pygame.sprite.Sprite):
    def __init__(self, start_pos, player, stats=None):
        super().__init__()
        
        # ステータスの決定（引数またはランダム）
        if stats:
            self.stats = stats
            if "size" not in self.stats: self.stats["size"] = 30
        else:
            # 第1世代のランダム生成
            self.stats = {
                "speed": random.randint(100, 150),
                "hp": 10,
                "size": 30
                # colorは後で計算するのでここでは決めない
            }
        
        # --- 【追加】速さに基づく色の可視化 ---
        # 基準となる最低速度と最高速度を定義（この範囲で色を変化させる）
        MIN_SPEED_REF = 80   # これより遅ければ完全な緑
        MAX_SPEED_REF = 250  # これより速ければ完全な赤

        current_speed = self.stats["speed"]

        # 速度が基準範囲のどこに位置するかを 0.0 ～ 1.0 の割合で計算
        ratio = (current_speed - MIN_SPEED_REF) / (MAX_SPEED_REF - MIN_SPEED_REF)
        
        # 割合を 0.0 ～ 1.0 の範囲に収める（クランプ）
        ratio = max(0.0, min(1.0, ratio))

        # 色の計算: (R, G, B)
        # 遅い(ratio 0.0) -> 緑 (0, 255, 50)
        # 速い(ratio 1.0) -> 赤 (255, 0, 50)
        red_val = int(255 * ratio)
        green_val = int(255 * (1.0 - ratio))
        
        # 計算した色をstatsに設定
        self.stats["color"] = (red_val, green_val, 50)
        # ------------------------------------
        
        # 時間計測
        self.spawn_time = time.time()
        self.death_time = 0
        
        # 基本情報
        self.player = player
        self.image = pygame.Surface((self.stats["size"], self.stats["size"]))
        self.image.fill(self.stats["color"]) # 計算した色で塗りつぶす
        self.rect = self.image.get_rect()
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
    def update(self, dt):
        # プレイヤーに向かうベクトル
        direction = self.player.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        # 移動
        self.pos += direction * self.stats["speed"] * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))