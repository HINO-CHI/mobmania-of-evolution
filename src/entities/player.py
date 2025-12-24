# src/entities/player.py

import pygame
from pygame.math import Vector2
import config
from src.entities.bullet import Bullet 

class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos, all_sprites, bullets_group):
        super().__init__()

        display_size = int(config.PLAYER_SIZE * config.GLOBAL_SCALE)

        self.image = pygame.Surface((config.PLAYER_SIZE, config.PLAYER_SIZE))
        self.image.fill(config.PLAYER_COLOR)
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
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x = 1
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

    def auto_attack(self):
        # 修正: クリック判定を削除し、常に発射するように変更
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > config.ATTACK_COOLDOWN:
            self.shoot()

    def shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = Vector2(mouse_pos) - self.pos
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = Bullet(self.pos, direction, config.PLAYER_DAMAGE)
            
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
            self.last_shot_time = pygame.time.get_ticks()