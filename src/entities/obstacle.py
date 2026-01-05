# src/entities/obstacle.py
import pygame
import os
import random # ランダムな大きさにするために追加
import config

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, pos, filename, is_solid=True):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.is_solid = is_solid 
        
        # 画像読み込み & リサイズ
        self.image = self.load_image(filename)
        self.rect = self.image.get_rect(center=self.pos)
        
        # 当たり判定（足元だけ）
        if self.is_solid:
            # 障害物は足元に判定を持つ
            self.hitbox = self.rect.inflate(-self.rect.width * 0.2, -self.rect.height * 0.6)
            self.hitbox.bottom = self.rect.bottom - 5
        else:
            self.hitbox = pygame.Rect(0, 0, 0, 0) 

    def load_image(self, filename):
        path = os.path.join(config.MAP_IMAGE_DIR, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            
            # ★修正: 画像が巨大すぎるので、適切なサイズに縮小する
            # 元の縦横比を維持しつつ、幅を 60px ～ 120px 程度に収める
            base_scale = random.uniform(0.6, 1.0) # 若干のランダム性
            
            # 基準サイズ (プレイヤーが80pxなので、それより少し大きいくらいに)
            target_width = 100 * base_scale
            
            # リサイズ計算
            aspect_ratio = img.get_height() / img.get_width()
            new_width = int(target_width)
            new_height = int(target_width * aspect_ratio)
            
            img = pygame.transform.scale(img, (new_width, new_height))
            
            return img
        except (FileNotFoundError, pygame.error):
            print(f"Error loading map image: {filename}")
            surf = pygame.Surface((40, 40))
            surf.fill((255, 0, 255))
            return surf

    def update(self, dt):
        pass