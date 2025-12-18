import pygame
from pygame.math import Vector2
import config
from src.entities.projectile import Projectile

class Player(pygame.sprite.Sprite):
    # ↓ ここに bullets_group を受け取る記述が必要です！
    def __init__(self, start_pos, all_sprites, bullets_group):
        super().__init__()
        self.image = pygame.Surface((config.PLAYER_SIZE, config.PLAYER_SIZE))
        self.image.fill(config.RED)
        self.rect = self.image.get_rect()
        
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.speed = config.PLAYER_SPEED

        # 攻撃管理用
        self.all_sprites = all_sprites
        self.bullets_group = bullets_group  # 受け取ったグループを保存
        self.last_shot_time = 0
        self.aim_direction = Vector2(1, 0) # 初期向きは右

    def update(self, dt):
        self.input(dt)
        self.auto_attack()

    def input(self, dt):
        keys = pygame.key.get_pressed()
        direction = Vector2(0, 0)
        
        # キーボード移動
        if keys[pygame.K_w]: direction.y = -1
        if keys[pygame.K_s]: direction.y = 1
        if keys[pygame.K_a]: direction.x = -1
        if keys[pygame.K_d]: direction.x = 1

        # コントローラー左スティック移動
        if direction.length() == 0 and pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            if abs(joy.get_axis(0)) > 0.1: direction.x = joy.get_axis(0)
            if abs(joy.get_axis(1)) > 0.1: direction.y = joy.get_axis(1)

        if direction.length() > 0:
            direction = direction.normalize()
            
        self.pos += direction * self.speed * dt
        self.pos.x = max(0, min(self.pos.x, config.SCREEN_WIDTH))
        self.pos.y = max(0, min(self.pos.y, config.SCREEN_HEIGHT))
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # 照準の更新
        self.update_aim()

    def update_aim(self):
        # 1. 右スティック (コントローラー)
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            rx = joy.get_axis(2)
            ry = joy.get_axis(3)
            aim_vec = Vector2(rx, ry)
            if aim_vec.length() > 0.2:
                self.aim_direction = aim_vec.normalize()
                return

        # 2. マウス
        mouse_pos = Vector2(pygame.mouse.get_pos())
        diff = mouse_pos - self.pos
        if diff.length() > 0:
            self.aim_direction = diff.normalize()

    def auto_attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > config.ATTACK_COOLDOWN:
            bullet = Projectile(self.pos, self.aim_direction)
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
            self.last_shot_time = current_time