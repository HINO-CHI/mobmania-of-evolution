# src/entities/player.py
import pygame
import os
from pygame.math import Vector2
import config
# 新しい武器クラスをインポート
from src.entities.weapons import PencilGun, BreadShield, BearSmash, WoodenStick

class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos, all_sprites, bullets_group, enemy_group):
        super().__init__()
        
        # --- 画像読み込み処理 ---
        self.image_left = None
        self.image_right = None
        self.facing_right = True

        scale = getattr(config, "GLOBAL_SCALE", 1.0)
        display_size = int(config.PLAYER_SIZE * scale)
        
        img_path = os.path.join(config.PLAYER_IMAGE_DIR, config.PLAYER_IMAGE)
        
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (display_size, display_size))
            self.image_left = img
            self.image_right = pygame.transform.flip(img, True, False)
            self.image = self.image_right
        except FileNotFoundError:
            self.image = pygame.Surface((display_size, display_size))
            self.image.fill(config.PLAYER_COLOR)
            self.image_left = self.image
            self.image_right = self.image

        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.pos = Vector2(start_pos)
        self.speed = config.PLAYER_SPEED
        
        # --- 武器管理システム用の変数をセット ---
        # ★重要: ここでセットしてからでないと、add_weaponは使えません
        self.all_sprites = all_sprites
        self.bullets_group = bullets_group
        self.enemy_group = enemy_group 
        
        self.weapons = []
        
        # --- 初期装備の設定 ---
        # ★修正: 変数セット後に実行するように配置
        print("Initializing Player Weapon: WoodenStick...")
        self.add_weapon(WoodenStick)

    def update(self, dt):
        self.move(dt)
        
        # 全ての武器を更新
        current_time = pygame.time.get_ticks()
        for weapon in self.weapons:
            weapon.update(current_time)

    def move(self, dt):
        keys = pygame.key.get_pressed()
        direction = Vector2(0, 0)
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x = -1
            if self.image_left:
                self.image = self.image_left
                self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x = 1
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
        self.pos.x = max(0, min(self.pos.x, config.SCREEN_WIDTH))
        self.pos.y = max(0, min(self.pos.y, config.SCREEN_HEIGHT))
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def add_weapon(self, weapon_class):
        # 既に持っている武器ならレベルアップ、なければ新規追加
        for weapon in self.weapons:
            if isinstance(weapon, weapon_class):
                weapon.upgrade()
                return
        
        # ここで self.enemy_group などを使うため、__init__内での呼び出し順序が重要
        new_weapon = weapon_class(self, self.enemy_group, self.all_sprites, self.bullets_group)
        self.weapons.append(new_weapon)
        print(f"New Weapon Added: {weapon_class.__name__}")