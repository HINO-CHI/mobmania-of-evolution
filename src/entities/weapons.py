# src/entities/weapons.py
import pygame
import math
import random
import os
from pygame.math import Vector2
import config
from src.entities.bullet import Bullet

# 画像読み込みヘルパー
def load_weapon_image(key):
    stats = config.WEAPON_STATS.get(key)
    if not stats:
        return None
    
    filename = stats.get("image")
    size = stats.get("size", 32)
    path = os.path.join(config.ITEM_IMAGE_DIR, filename)
    
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (size, size))
        return img
    except FileNotFoundError:
        print(f"Warning: Image not found {path}")
        return None

# ==========================================
# ★追加: 回転する弾丸クラス
# ==========================================
class SpinningBullet(Bullet):
    def __init__(self, pos, dir, damage, image, spin_speed):
        super().__init__(pos, dir, damage, image)
        self.orig_image = image  # 回転させる前の元画像を保存
        self.angle = 0
        self.spin_speed = spin_speed

    def update(self, dt):
        # 通常の移動処理
        super().update(dt)
        
        # 回転処理 (元画像を毎回回転させて劣化を防ぐ)
        self.angle = (self.angle + self.spin_speed) % 360
        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        # 回転すると矩形サイズが変わるので中心位置を合わせ直す
        self.rect = self.image.get_rect(center=self.rect.center)

# ==========================================
# くま爆弾クラス
# ==========================================
class BearBomb(pygame.sprite.Sprite):
    def __init__(self, pos, damage, enemy_group, image, fuse_time, blast_radius):
        super().__init__()
        self.pos = Vector2(pos)
        self.damage = damage
        self.enemy_group = enemy_group
        self.image = image
        self.rect = self.image.get_rect(center=self.pos)
        
        self.spawn_time = pygame.time.get_ticks()
        self.fuse_time = fuse_time
        self.explosion_radius = blast_radius

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.spawn_time >= self.fuse_time:
            self.explode()

    def explode(self):
        explosion_area = pygame.sprite.Sprite()
        explosion_area.rect = pygame.Rect(0, 0, self.explosion_radius*2, self.explosion_radius*2)
        explosion_area.rect.center = self.rect.center
        explosion_area.radius = self.explosion_radius
        
        hits = pygame.sprite.spritecollide(explosion_area, self.enemy_group, False, pygame.sprite.collide_circle)
        for enemy in hits:
            # 武器ダメージを与えて、倒したらkillする処理はGameplayScreenで一括管理しているので
            # ここではダメージを与えるだけにする（kill判定はupdateで行う）
            enemy.take_damage(self.damage)
        
        print("Bear Bomb Exploded!") 
        self.kill()

# ==========================================
# 武器 基本クラス
# ==========================================
class Weapon:
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        self.owner = owner
        self.enemy_group = enemy_group
        self.all_sprites = all_sprites
        self.bullets_group = bullets_group
        self.level = 1
        self.name = "Unknown"
        self.last_attack_time = 0

    def update(self, current_time):
        pass

    def upgrade(self):
        self.level += 1
        print(f"{self.name} Leveled Up! -> Lv.{self.level}")

# ==========================================
# ★追加: レベル0 木の棒 (回転投げ)
# ==========================================
class WoodenStick(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["stick"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.cooldown = stats["cooldown"]
        self.bullet_speed = stats.get("speed", 500)
        self.spin_speed = stats.get("spin_speed", 15)
        
        self.image = load_weapon_image("stick")

    def update(self, current_time):
        if current_time - self.last_attack_time >= self.cooldown:
            self.shoot()
            self.last_attack_time = current_time

    def shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = Vector2(mouse_pos) - self.owner.pos
        if direction.length() > 0:
            direction = direction.normalize()
            
            # 回転する弾丸(SpinningBullet)を生成
            bullet = SpinningBullet(
                self.owner.pos, 
                direction, 
                self.damage, 
                self.image, 
                self.spin_speed
            )
            bullet.speed = self.bullet_speed
            
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
            
    def upgrade(self):
        super().upgrade()
        self.cooldown = max(200, self.cooldown - 50)
        self.damage += 2

# ==========================================
# 武器1: えんぴつ
# ==========================================
class PencilGun(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["pencil"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.cooldown = stats["cooldown"]
        self.bullet_speed = stats.get("speed", 600)
        
        self.bullet_image = load_weapon_image("pencil")

    def update(self, current_time):
        if current_time - self.last_attack_time >= self.cooldown:
            self.shoot()
            self.last_attack_time = current_time

    def shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = Vector2(mouse_pos) - self.owner.pos
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = Bullet(self.owner.pos, direction, self.damage, self.bullet_image)
            bullet.speed = self.bullet_speed
            
            # えんぴつは進行方向に向けて一度だけ回転
            angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
            bullet.image = pygame.transform.rotate(bullet.image, angle)
            bullet.rect = bullet.image.get_rect(center=bullet.rect.center)
            
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
    
    def upgrade(self):
        super().upgrade()
        self.cooldown = max(100, self.cooldown - 50)
        self.damage += int(self.damage * 0.2) 

# ==========================================
# 武器2: 食パン
# ==========================================
class BreadShield(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["bread"]
        
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.radius = stats["radius"]
        self.orb_count = stats["orb_count"]
        self.speed = stats["rot_speed"]
        self.angle = 0
        
        self.image = load_weapon_image("bread")
        if not self.image:
            self.image = pygame.Surface((20, 20))
            self.image.fill(config.CYAN)
        
        self.orbs = []
        for i in range(self.orb_count):
            orb_sprite = pygame.sprite.Sprite()
            orb_sprite.image = self.image
            orb_sprite.rect = self.image.get_rect()
            orb_sprite.rect.center = self.owner.pos
            self.all_sprites.add(orb_sprite)
            self.orbs.append(orb_sprite)

    def update(self, current_time):
        self.angle += self.speed
        cx, cy = self.owner.rect.center
        
        for i, orb in enumerate(self.orbs):
            offset = (2 * math.pi / self.orb_count) * i
            current_orb_angle = self.angle + offset
            
            orb.rect.centerx = cx + math.cos(current_orb_angle) * self.radius
            orb.rect.centery = cy + math.sin(current_orb_angle) * self.radius

            hits = pygame.sprite.spritecollide(orb, self.enemy_group, False)
            for enemy in hits:
                enemy.take_damage(self.damage / 5.0)

    def upgrade(self):
        super().upgrade()
        self.radius += 10
        self.speed += 0.01
        self.damage += 2

# ==========================================
# 武器3: くまちゃん
# ==========================================
class BearSmash(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["bear"]
        
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.cooldown = stats["cooldown"]
        self.fuse_time = stats["fuse_time"]
        self.blast_radius = stats["blast_radius"]
        
        self.image = load_weapon_image("bear")

    def update(self, current_time):
        if current_time - self.last_attack_time >= self.cooldown:
            self.smash()
            self.last_attack_time = current_time

    def smash(self):
        offset = 60
        if self.owner.facing_right:
            spawn_x = self.owner.pos.x - offset
        else:
            spawn_x = self.owner.pos.x + offset
        
        spawn_pos = Vector2(spawn_x, self.owner.pos.y)
        
        bomb = BearBomb(
            spawn_pos, 
            self.damage, 
            self.enemy_group, 
            self.image, 
            self.fuse_time, 
            self.blast_radius
        )
        self.all_sprites.add(bomb)

    def upgrade(self):
        super().upgrade()
        self.cooldown -= 100
        self.damage += 10