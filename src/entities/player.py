# src/entities/player.py
import pygame
import os
from pygame.math import Vector2
import config
from src.entities.bullet import Bullet 

class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos, all_sprites, bullets_group):
        super().__init__()
        
        # 1. 画像の読み込み処理
        self.image_left = None
        self.image_right = None
        self.facing_right = True # 初期向き

        # 画面サイズに合わせた表示サイズ
        scale = getattr(config, "GLOBAL_SCALE", 1.0)
        display_size = int(config.PLAYER_SIZE * scale)
        
        img_path = os.path.join(config.PLAYER_IMAGE_DIR, config.PLAYER_IMAGE)
        
        try:
            # 画像のロード
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (display_size, display_size))
            
            # 敵と同じように、元画像が「左向き」か「右向き」かで処理が変わります。
            # ここでは「元画像は左向き」と仮定して、右向き用に反転させます。
            # (もし逆なら、img_leftの方に flip(..., True, False) をかけてください)
            self.image_left = img
            self.image_right = pygame.transform.flip(img, True, False)
            
            # 初期画像
            self.image = self.image_right
            
        except FileNotFoundError:
            print(f"Player image not found at {img_path}. Using square.")
            self.image = pygame.Surface((display_size, display_size))
            self.image.fill(config.PLAYER_COLOR)
            self.image_left = self.image
            self.image_right = self.image

        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        
        self.pos = Vector2(start_pos)
        self.speed = config.PLAYER_SPEED
        
        self.all_sprites = all_sprites
        self.bullets_group = bullets_group
        
        self.last_shot_time = 0

    def update(self, dt):
        self.move(dt)
        self.auto_attack()

    def move(self, dt):
        keys = pygame.key.get_pressed()
        direction = Vector2(0, 0)
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x = -1
            # 左入力で左向き画像へ
            if self.image_left:
                self.image = self.image_left
                self.facing_right = False
                
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x = 1
            # 右入力で右向き画像へ
            if self.image_right:
                self.image = self.image_right
                self.facing_right = True
                
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y = 1
            
        if direction.length() > 0:
            direction = direction.normalize()
            
        self.pos += direction * self.speed * dt
        
        # 画面外に出ないように制限
        self.pos.x = max(0, min(self.pos.x, config.SCREEN_WIDTH))
        self.pos.y = max(0, min(self.pos.y, config.SCREEN_HEIGHT))
        
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def auto_attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > config.ATTACK_COOLDOWN:
            self.shoot()

    def shoot(self):
        # 一番近い敵を探すロジックに変更するのが理想ですが、
        # まずは「マウスカーソルの方向」のままにします
        mouse_pos = pygame.mouse.get_pos()
        direction = Vector2(mouse_pos) - self.pos
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = Bullet(self.pos, direction, config.PLAYER_DAMAGE)
            
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
            self.last_shot_time = pygame.time.get_ticks()