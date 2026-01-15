import pygame
import os
import random
import math

# 画像読み込みヘルパー
def load_grave_image(filename):
    path = os.path.join("assets", "images", "grave", filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        # 必要に応じてサイズ調整（例: 32x32くらいに）
        img = pygame.transform.scale(img, (64, 64))
        return img
    except (FileNotFoundError, pygame.error):
        return None

class GraveFlower(pygame.sprite.Sprite):
    def __init__(self, pos, groups, filename):
        super().__init__(groups)
        
        self.image = load_grave_image(filename)
        
        # 画像がない場合のフォールバック（ピンクの丸）
        if self.image is None:
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 100, 200), (10, 10), 8)
        
        self.rect = self.image.get_rect(center=pos)
        
        # 花の位置を少しランダムにずらして自然に見せる
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        self.rect.x += offset_x
        self.rect.y += offset_y
        
        # 花は背景扱いなので、Y座標を少し調整してプレイヤーが踏めるように見せても良い
        # (Yソート機能があるCameraGroupを使っている前提)
        self.hitbox = self.rect.inflate(-10, -10)