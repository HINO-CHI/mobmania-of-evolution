# src/entities/obstacle.py
import pygame
import random

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, pos, image_source, is_solid=True, props=None):
        """
        props: configで定義した個別設定 (hitbox_w, hitbox_h, offset_yなど)
        """
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.is_solid = is_solid 
        
        # propsがNoneの場合の対策
        if props is None: props = {}
        
        if isinstance(image_source, pygame.Surface):
            self.image = image_source
        else:
            self.image = pygame.Surface((50, 50))
            self.image.fill((255, 0, 255))

        self.rect = self.image.get_rect(center=self.pos)
        
        # --- 当たり判定のカスタマイズ ---
        if self.is_solid:
            # configから設定を取得 (デフォルト値も設定)
            # 幅倍率 (例: 0.2 なら画像の20%の幅)
            w_ratio = props.get("hitbox_w", 0.6) 
            # 高さ倍率
            h_ratio = props.get("hitbox_h", 0.4)
            # 縦オフセット (判定を下にずらす)
            offset_y = props.get("offset_y", 0)

            # 判定サイズ計算
            hitbox_w = self.rect.width * w_ratio
            hitbox_h = self.rect.height * h_ratio
            
            # Hitboxを作成 (まずはRectの中心に配置)
            self.hitbox = pygame.Rect(0, 0, hitbox_w, hitbox_h)
            self.hitbox.center = self.rect.center
            
            # 縦位置の調整 (通常は足元に寄せる)
            # offset_y がある場合はさらにずらす
            self.hitbox.centery = self.rect.bottom - (hitbox_h / 2) + offset_y
            
            # 最後にRectの中心座標でhitboxも移動（念のため）
            self.hitbox.centerx = self.rect.centerx
            
        else:
            self.hitbox = pygame.Rect(0, 0, 0, 0) 

    def update(self, dt):
        pass