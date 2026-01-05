# src/entities/weapons.py
import pygame
import math
import random
import os
from pygame.math import Vector2
import config
from src.entities.bullet import Bullet

# --- 画像読み込みヘルパー ---
def load_weapon_image(key):
    stats = config.WEAPON_STATS.get(key)
    if not stats:
        return create_fallback_surface(32, config.RED)
    
    filename = stats.get("image")
    size = stats.get("size", 32)
    path = os.path.join(config.ITEM_IMAGE_DIR, filename)
    
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (size, size))
        return img
    except (FileNotFoundError, pygame.error):
        color = config.BROWN if key == "stick" else config.YELLOW
        if key == "thunder": color = config.YELLOW
        elif key == "ice": color = config.CYAN
        elif key == "drill": color = config.RED
        return create_fallback_surface(size, color)

def create_fallback_surface(size, color):
    surf = pygame.Surface((size, size // 2))
    surf.fill(color)
    return surf

# ==========================================
# 回転する弾丸クラス
# ==========================================
class SpinningBullet(Bullet):
    def __init__(self, pos, dir, damage, image, spin_speed):
        # 親クラス(Bullet)の初期化
        # speedとlifetimeは後で設定するかデフォルトを使う
        super().__init__(pos, dir, damage, image)
        self.orig_image = image
        self.angle = 0
        self.spin_speed = spin_speed

    def update(self, dt):
        # 移動処理 (Bulletのupdate)
        super().update(dt)
        
        # 回転処理
        if self.orig_image:
            self.angle = (self.angle + self.spin_speed) % 360
            self.image = pygame.transform.rotate(self.orig_image, self.angle)
            # 回転後の中心を維持
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
            enemy.take_damage(self.damage)
        
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
# Tier 0: 木の棒 (WoodenStick)
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
        # ★修正: 画面上のマウス位置 - 画面中央(プレイヤー)
        mouse_pos = Vector2(pygame.mouse.get_pos())
        screen_center = Vector2(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        
        direction = mouse_pos - screen_center
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            # 弾の生成 (位置はプレイヤーのワールド座標)
            bullet = SpinningBullet(
                self.owner.pos, 
                direction, 
                self.damage, 
                self.image, 
                self.spin_speed
            )
            bullet.speed = self.bullet_speed
            bullet.lifetime = 1500 # 1.5秒で消える
            
            self.all_sprites.add(bullet)
            self.bullets_group.add(bullet)
            
    def upgrade(self):
        super().upgrade()
        self.cooldown = max(200, self.cooldown - 50)
        self.damage += 2

# ==========================================
# Tier 1: えんぴつ (PencilGun)
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
        # ★修正: 画面上のマウス位置 - 画面中央
        mouse_pos = Vector2(pygame.mouse.get_pos())
        screen_center = Vector2(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        
        direction = mouse_pos - screen_center
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = Bullet(self.owner.pos, direction, self.damage, self.bullet_image)
            bullet.speed = self.bullet_speed
            bullet.lifetime = 2000 # 2秒
            
            # 進行方向へ画像を回転
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
# Tier 1: 食パン (BreadShield)
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
        
        self.orbs = []
        for i in range(self.orb_count):
            orb_sprite = pygame.sprite.Sprite()
            orb_sprite.image = self.image
            orb_sprite.rect = self.image.get_rect()
            # 初期位置
            orb_sprite.rect.center = self.owner.pos
            self.all_sprites.add(orb_sprite)
            self.orbs.append(orb_sprite)

    def update(self, current_time):
        # パンはプレイヤーの周りを回る
        self.angle += self.speed
        cx, cy = self.owner.rect.center # 画面上の位置ではなく、描画時に補正されるRectを使う
        
        # プレイヤーのワールド座標を中心に計算
        wx, wy = self.owner.pos.x, self.owner.pos.y
        
        for i, orb in enumerate(self.orbs):
            offset = (2 * math.pi / self.orb_count) * i
            current_orb_angle = self.angle + offset
            
            # ワールド座標での位置
            orb_x = wx + math.cos(current_orb_angle) * self.radius
            orb_y = wy + math.sin(current_orb_angle) * self.radius
            
            # Rectを更新 (描画用)
            orb.rect.centerx = round(orb_x)
            orb.rect.centery = round(orb_y)
            
            hits = pygame.sprite.spritecollide(orb, self.enemy_group, False)
            for enemy in hits:
                enemy.take_damage(self.damage / 5.0)

    def upgrade(self):
        super().upgrade()
        self.radius += 10
        self.speed += 0.01
        self.damage += 2

# ==========================================
# Tier 1: くまちゃん (BearSmash)
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
        bomb = BearBomb(spawn_pos, self.damage, self.enemy_group, self.image, self.fuse_time, self.blast_radius)
        self.all_sprites.add(bomb)

    def upgrade(self):
        super().upgrade()
        self.cooldown -= 100
        self.damage += 10

# ==========================================
# Tier 2: 上位武器
# ==========================================
class ThunderStaff(PencilGun):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["thunder"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.bullet_image = load_weapon_image("thunder")

class IceCream(PencilGun):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["ice"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.bullet_image = load_weapon_image("ice")

class GigaDrill(PencilGun):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["drill"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.bullet_image = load_weapon_image("drill")