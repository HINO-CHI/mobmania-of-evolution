import pygame
import math
import random
import os
from pygame.math import Vector2
import config
from src.entities.bullet import Bullet

# --- 画像読み込みヘルパー ---
def load_weapon_image(key):
    # config.WEAPON_STATS からファイル名を取得
    stats = config.WEAPON_STATS.get(key)
    if not stats:
        return create_fallback_surface(32, (255, 0, 255)) # マゼンタ(エラー色)
    
    filename = stats.get("image")
    size = stats.get("size", 32)
    
    # config.ITEM_IMAGE_DIR (例: assets/images/items) を参照
    path = os.path.join(config.ITEM_IMAGE_DIR, filename)
    
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (size, size))
        return img
    except (FileNotFoundError, pygame.error):
        print(f"Warning: Image not found {path}")
        # フォールバック色の設定
        color = (150, 75, 0) if key == "stick" else (255, 255, 0)
        if key == "thunder": color = (255, 255, 0)
        elif key == "ice": color = (0, 255, 255)
        elif key == "drill": color = (255, 0, 0)
        return create_fallback_surface(size, color)

def create_fallback_surface(size, color):
    surf = pygame.Surface((size, size // 2))
    surf.fill(color)
    return surf

# ==========================================
# ★追加: 演出用クラス (画像表示)
# ==========================================
class VisualEffect(pygame.sprite.Sprite):
    def __init__(self, pos, image, duration, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration
        # 少しふわふわさせるための初期位置
        self.start_y = pos[1]

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.spawn_time
        
        # 寿命チェック
        if elapsed > self.duration:
            self.kill()
            return

        # ふわふわ演出 (上に少し浮く)
        progress = elapsed / self.duration
        self.rect.centery = self.start_y - (progress * 20)

# ==========================================
# ★追加: 演出用クラス (遅延テキスト)
# ==========================================
class DelayedHealingText(pygame.sprite.Sprite):
    def __init__(self, pos, text, color, delay, groups):
        super().__init__(groups)
        # フォント設定 (config.FONT_PATHがあれば使い、なければデフォルト)
        try:
            self.font = pygame.font.Font(config.FONT_PATH, 24)
        except:
            self.font = pygame.font.SysFont(None, 48)
            
        self.image_orig = self.font.render(text, True, color)
        
        # 最初は透明な空画像にしておく（遅延用）
        self.image = pygame.Surface((0, 0))
        self.rect = self.image.get_rect(center=pos)
        
        self.pos = Vector2(pos)
        self.start_time = pygame.time.get_ticks()
        self.delay = delay
        self.is_visible = False
        self.life_time = 1500 # 表示されてから消えるまでの時間

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        
        if not self.is_visible:
            # 遅延待機中
            if current_time - self.start_time >= self.delay:
                self.is_visible = True
                self.image = self.image_orig
                self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
                self.appear_time = current_time
        else:
            # 表示中
            # 上に昇る
            self.pos.y -= 1 * (dt * 60)
            self.rect.center = (round(self.pos.x), round(self.pos.y))
            
            # 寿命チェック
            if current_time - self.appear_time > self.life_time:
                self.kill()

class SpinningBullet(Bullet):
    def __init__(self, pos, dir, damage, image, spin_speed):
        super().__init__(pos, dir, damage, image)
        self.orig_image = image
        self.angle = 0
        self.spin_speed = spin_speed

    def update(self, dt):
        super().update(dt)
        if self.orig_image:
            self.angle = (self.angle + self.spin_speed) % 360
            self.image = pygame.transform.rotate(self.orig_image, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)

# ==========================================
# ★追加: プレイヤー用 極太レーザー
# ==========================================
class PlayerLaser(pygame.sprite.Sprite):
    def __init__(self, owner, angle_vec, damage, width, length, duration, all_sprites, enemy_group):
        super().__init__(all_sprites)
        self.owner = owner
        self.damage = damage
        self.enemy_group = enemy_group
        self.duration = duration
        self.spawn_time = pygame.time.get_ticks()
        self.hit_enemies = set()

        self.angle_vec = angle_vec.normalize()
        
        # 描画用Surface作成
        self.image_orig = pygame.Surface((length, width), pygame.SRCALPHA)
        pygame.draw.rect(self.image_orig, (0, 200, 255, 80), (0, 0, length, width))
        pygame.draw.rect(self.image_orig, (100, 255, 255, 180), (0, width//4, length, width//2))
        pygame.draw.rect(self.image_orig, (255, 255, 255, 255), (0, width//2 - 2, length, 4))
        
        self.angle = math.degrees(math.atan2(-angle_vec.y, angle_vec.x))
        self.image = pygame.transform.rotate(self.image_orig, self.angle)
        self.rect = self.image.get_rect()
        
        center_offset = self.angle_vec * (length / 2)
        self.rect.center = self.owner.rect.center + center_offset
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        # 現在時刻を取得
        current_time = pygame.time.get_ticks()

        length = self.image_orig.get_width()
        center_offset = self.angle_vec * (length / 2)
        self.rect.center = self.owner.rect.center + center_offset

        # 寿命チェック
        if current_time - self.spawn_time >= self.duration:
            self.kill()
            return

        hits = pygame.sprite.spritecollide(self, self.enemy_group, False)
        for enemy in hits:
            if enemy not in self.hit_enemies:
                if pygame.sprite.collide_mask(self, enemy):
                    enemy.take_damage(self.damage)
                    self.hit_enemies.add(enemy)

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
        # 爆発範囲の判定用スプライト
        explosion_area = pygame.sprite.Sprite()
        explosion_area.rect = pygame.Rect(0, 0, self.explosion_radius*2, self.explosion_radius*2)
        explosion_area.rect.center = self.rect.center
        
        # 円形衝突判定
        hits = pygame.sprite.spritecollide(explosion_area, self.enemy_group, False, pygame.sprite.collide_circle_ratio(1.0))
        for enemy in hits:
            # 距離チェックを厳密にするならここで distance check を入れる
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
        mouse_pos = Vector2(pygame.mouse.get_pos())
        screen_center = Vector2(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        
        direction = mouse_pos - screen_center
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = SpinningBullet(
                self.owner.pos, 
                direction, 
                self.damage, 
                self.image, 
                self.spin_speed
            )
            bullet.speed = self.bullet_speed
            bullet.lifetime = 1500 
            
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
        mouse_pos = Vector2(pygame.mouse.get_pos())
        screen_center = Vector2(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        
        direction = mouse_pos - screen_center
        
        if direction.length() > 0:
            direction = direction.normalize()
            
            bullet = Bullet(self.owner.pos, direction, self.damage, self.bullet_image)
            bullet.speed = self.bullet_speed
            bullet.lifetime = 2000
            
            # 進行方向へ画像を回転 (右向き画像前提)
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
            orb_sprite.rect.center = self.owner.pos
            self.all_sprites.add(orb_sprite)
            self.orbs.append(orb_sprite)

    def update(self, current_time):
        self.angle += self.speed
        
        wx, wy = self.owner.pos.x, self.owner.pos.y
        
        for i, orb in enumerate(self.orbs):
            offset = (2 * math.pi / self.orb_count) * i
            current_orb_angle = self.angle + offset
            
            orb_x = wx + math.cos(current_orb_angle) * self.radius
            orb_y = wy + math.sin(current_orb_angle) * self.radius
            
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
        spawn_x = self.owner.pos.x - offset if self.owner.facing_right else self.owner.pos.x + offset
        spawn_pos = Vector2(spawn_x, self.owner.pos.y)
        
        bomb = BearBomb(spawn_pos, self.damage, self.enemy_group, self.image, self.fuse_time, self.blast_radius)
        self.all_sprites.add(bomb)

    def upgrade(self):
        super().upgrade()
        self.cooldown = max(500, self.cooldown - 100)
        self.damage += 10


# ==========================================
# Tier 2: パルスバリア (ThunderStaff)
# ==========================================
# src/entities/weapons.py (ThunderStaff部分のみ)

class ThunderStaff(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["thunder"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        
        self.radius = stats["radius"] # この半径が攻撃＆回収範囲になる
        self.stun_duration = stats.get("stun_duration", 200)
        
        # バリア表示用のスプライトを1つだけ作る
        self.barrier_sprite = pygame.sprite.Sprite()
        size = int(self.radius * 2 + 40)
        self.barrier_sprite.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.barrier_sprite.rect = self.barrier_sprite.image.get_rect()
        self.barrier_sprite.rect.center = self.owner.pos
        
        self.all_sprites.add(self.barrier_sprite)

    def update(self, current_time):
        # 1. バリアの位置をプレイヤーに追従させる
        self.barrier_sprite.rect.center = self.owner.rect.center
        
        # 2. ビリビリ円のアニメーション描画
        self.draw_electric_ring(self.barrier_sprite)

        # 3. 攻撃＆スタン判定
        self.barrier_sprite.radius = self.radius
        hits = pygame.sprite.spritecollide(self.barrier_sprite, self.enemy_group, False, pygame.sprite.collide_circle)
        for enemy in hits:
            enemy.take_damage(self.damage / 20.0)
            if hasattr(enemy, "apply_stun"):
                enemy.apply_stun(self.stun_duration)

        # 4. アイテム収集
        self.collect_items()

    def draw_electric_ring(self, sprite):
        """プレイヤーを中心としたビリビリした円環を描画する"""
        w, h = sprite.image.get_size()
        center = (w // 2, h // 2)
        sprite.image.fill((0, 0, 0, 0))
        
        color_core = (255, 255, 255)
        color_glow = (100, 200, 255)
        
        points = []
        num_points = 60
        
        for i in range(num_points):
            angle = (2 * math.pi / num_points) * i
            noise = random.randint(-5, 5)
            r = self.radius + noise
            x = center[0] + math.cos(angle) * r
            y = center[1] + math.sin(angle) * r
            points.append((x, y))
        
        points.append(points[0])
        
        if len(points) > 2:
            pygame.draw.lines(sprite.image, color_glow, False, points, 5)
            pygame.draw.lines(sprite.image, color_core, False, points, 2)

    def collect_items(self):
        if not hasattr(self.owner, "items_group"): return
        
        for item in self.owner.items_group:
            dist_vec = self.owner.pos - Vector2(item.rect.center)
            distance = dist_vec.length()
            
            # ★修正: 攻撃範囲(self.radius)と同じ範囲で吸い寄せる
            if distance <= self.radius:
                if distance > 10: 
                    dir = dist_vec.normalize()
                    item.rect.centerx += dir.x * 20
                    item.rect.centery += dir.y * 20

    def upgrade(self):
        super().upgrade()
        self.radius += 20         # 範囲拡大
        self.damage += 1
        
        # スプライト再生成
        self.all_sprites.remove(self.barrier_sprite)
        self.barrier_sprite = pygame.sprite.Sprite()
        size = int(self.radius * 2 + 40)
        self.barrier_sprite.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.barrier_sprite.rect = self.barrier_sprite.image.get_rect()
        self.barrier_sprite.rect.center = self.owner.pos
        self.all_sprites.add(self.barrier_sprite)

# ==========================================
# Tier 2: ミルク (IceCream改め)
# ==========================================
class IceCream(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["ice"]
        self.name = stats["name"]
        self.heal_amount = stats["heal_amount"]
        self.cooldown = stats["cooldown"]
        self.image = load_weapon_image("ice")
        
        self.last_attack_time = pygame.time.get_ticks()

    def update(self, current_time):
        if current_time - self.last_attack_time >= self.cooldown:
            self.heal()
            self.last_attack_time = current_time

    def heal(self):
        if self.owner.hp < self.owner.max_hp:
            self.owner.hp = min(self.owner.hp + self.heal_amount, self.owner.max_hp)
            
            # ★修正: 演出の追加
            # 1. ミルクの画像をプレイヤーの頭上に表示（1秒間）
            effect_pos = (self.owner.rect.centerx, self.owner.rect.top - 40)
            VisualEffect(effect_pos, self.image, 1000, self.all_sprites)
            
            # 2. 数字を1秒後に表示（遅延テキスト）
            # VisualEffectより少し上に表示されるように位置を調整
            text_pos = (self.owner.rect.centerx, self.owner.rect.top - 60)
            DelayedHealingText(text_pos, f"+{self.heal_amount}", (0, 255, 0), 1000, self.all_sprites)
            
            print(f"Milk used! Recovered {self.heal_amount}")

    def upgrade(self):
        super().upgrade()
        self.heal_amount += 10
        self.cooldown = max(10000, self.cooldown - 2000)

# ==========================================
# Tier 2: レーザーキャノン (LaserCannon)
# ==========================================
class LaserCannon(Weapon):
    def __init__(self, owner, enemy_group, all_sprites, bullets_group):
        super().__init__(owner, enemy_group, all_sprites, bullets_group)
        stats = config.WEAPON_STATS["drill"]
        self.name = stats["name"]
        self.damage = stats["damage"]
        self.cooldown = stats["cooldown"]
        
        self.width = stats.get("laser_width", 50)
        self.length = stats.get("laser_length", 1000)
        self.duration = stats.get("duration", 500)
        
        self.image = load_weapon_image("drill")

    def update(self, current_time):
        if current_time - self.last_attack_time >= self.cooldown:
            self.shoot()
            self.last_attack_time = current_time

    def shoot(self):
        mouse_pos = Vector2(pygame.mouse.get_pos())
        screen_center = Vector2(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        direction = mouse_pos - screen_center
        
        if direction.length() > 0:
            PlayerLaser(
                self.owner,
                direction,
                self.damage,
                self.width,
                self.length,
                self.duration,
                self.all_sprites,
                self.enemy_group
            )
            
    def upgrade(self):
        super().upgrade()
        self.damage += 50
        self.width += 20
        self.cooldown = max(5000, self.cooldown - 1000)