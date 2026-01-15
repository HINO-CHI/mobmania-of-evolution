# src/entities/enemy.py
import pygame
import os
import random
import time
from pygame.math import Vector2
import config
import math
from src.entities.enemy_projectile import EnemyProjectile

class Enemy(pygame.sprite.Sprite):
    _image_cache = {}

    def __init__(self, start_pos, player, enemy_group, stats=None):
        super().__init__()
        self.enemy_group = enemy_group

        self.stun_end_time = 0
        
        # --- 1. ステータス設定 ---
        if stats:
            self.stats = stats
            if "type_id" not in self.stats: self.stats["type_id"] = 0
            
            # 通常モブの場合のみベースステータスを参照
            if self.stats["type_id"] in config.MOB_BASE_STATS:
                base = config.MOB_BASE_STATS[self.stats["type_id"]]
                if "image" not in self.stats: self.stats["image"] = base["image"]
                if "size" not in self.stats: self.stats["size"] = base["size"]
        else:
            type_id = random.choice(list(config.MOB_BASE_STATS.keys()))
            base_data = config.MOB_BASE_STATS[type_id]
            self.stats = {
                "type_id": type_id,
                "name": base_data["name"],
                "image": base_data["image"],
                "hp": base_data["hp"],
                "max_hp": base_data["hp"],
                "speed": base_data["speed"],
                "attack": base_data["attack"],
                "defense_rate": base_data["defense_rate"],
                "attack_type": base_data["attack_type"],
                "size": base_data["size"]
            }

        self.player = player
        
        # --- 2. 画像設定 ---
        img_source = self.stats.get("image")
        
        if isinstance(img_source, pygame.Surface):
            # すでに読み込まれた画像（ボスなど）
            self.image_left = img_source
            self.image_right = pygame.transform.flip(img_source, True, False)
            display_size = img_source.get_width()
        else:
            # 通常の敵（ファイル名から読み込み）
            image_name = img_source
            base_size = self.stats.get("size", 32) # デフォルト32
            scale = getattr(config, "GLOBAL_SCALE", 1.0)
            display_size = int(base_size * scale)

            cache_key = f"{image_name}_{display_size}"

            if cache_key not in Enemy._image_cache:
                img_path = os.path.join(config.MOB_IMAGE_DIR, image_name)
                try:
                    img_left = pygame.image.load(img_path).convert_alpha()
                    img_left = pygame.transform.scale(img_left, (display_size, display_size))
                    img_right = pygame.transform.flip(img_left, True, False)
                    Enemy._image_cache[cache_key] = (img_left, img_right)
                except FileNotFoundError:
                    print(f"Error: Image {image_name} not found. Using fallback rect.")
                    surf = pygame.Surface((display_size, display_size))
                    surf.fill(config.GREEN)
                    Enemy._image_cache[cache_key] = (surf, surf)

            self.image_left, self.image_right = Enemy._image_cache[cache_key]

        self.image = self.image_left
        self.facing_right = False 

        self.rect = self.image.get_rect()
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # 円形当たり判定用の半径
        self.radius = int(display_size * 0.4)
        
        inflation = -1 * (display_size // 4)
        self.hitbox = self.rect.inflate(inflation, inflation)

        self.spawn_time = time.time()
        self.death_time = 0

        # --- 3. 軽量化と分離の変数 ---
        self.cached_separation = Vector2(0, 0)
        self.update_interval = 15
        self.separation_timer = id(self) % self.update_interval

    def update(self, dt):

        # スタン中は移動処理をスキップ
        current_time = pygame.time.get_ticks()
        if current_time < self.stun_end_time:
            # スタン中はアニメーションだけ更新するか、完全に止めるか
            # ここでは移動計算(self.move)を呼ばないことで停止させる
            return
        
        # 1. プレイヤー追尾ベクトル
        to_player = self.player.pos - self.pos
        if to_player.length() > 0:
            to_player = to_player.normalize()
        
        # 2. 分離ベクトル (15フレームに1回だけ更新)
        self.separation_timer -= 1
        if self.separation_timer <= 0:
            self.cached_separation = self.get_separation_vector()
            self.separation_timer = self.update_interval
        
        separation = self.cached_separation

        # 3. ベクトルの合成
        move_vector = to_player + (separation * 0.5)
        
        if move_vector.length() > 0:
            move_vector = move_vector.normalize()

        # 4. 向きの更新
        if move_vector.x > 0 and not self.facing_right:
            self.image = self.image_right
            self.facing_right = True
        elif move_vector.x < 0 and self.facing_right:
            self.image = self.image_left
            self.facing_right = False

        # 5. 移動
        self.pos += move_vector * self.stats["speed"] * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center

    def get_separation_vector(self):
        separation = Vector2(0, 0)
        
        # 半径を使った高速判定
        neighbors = pygame.sprite.spritecollide(self, self.enemy_group, False, pygame.sprite.collide_circle)
        
        count = 0
        limit = 3 
        
        for neighbor in neighbors:
            if neighbor == self:
                continue
            
            diff = self.pos - neighbor.pos
            dist = diff.length()
            
            min_dist = self.radius + neighbor.radius
            
            if 0 < dist < min_dist:
                diff = diff.normalize()
                separation += diff
                count += 1
            
            if count >= limit:
                break
        
        if count > 0:
            separation /= count
            if separation.length() > 0:
                separation = separation.normalize()

        return separation

    # ★修正: knockback_force 引数を受け取れるように変更 (デフォルト値0)
    def take_damage(self, raw_damage, knockback_force=0):
        defense = self.stats.get("defense_rate", 1.0)
        actual_damage = raw_damage / defense
        actual_damage = max(1, int(actual_damage))
        self.stats["hp"] -= actual_damage
        if self.stats["hp"] <= 0:
            return True
        return False
    
    # ★追加: 外部からスタンさせるためのメソッド
    def apply_stun(self, duration_ms):
        current_time = pygame.time.get_ticks()
        # 既にスタンしているなら、より長い時間の方を採用して延長
        new_end_time = current_time + duration_ms
        if new_end_time > self.stun_end_time:
            self.stun_end_time = new_end_time
    
# ==========================================
# ボス・中ボスクラス
# ==========================================

# 画像読み込み用ヘルパー
def load_boss_image(filename, scale_size=None):
    path = os.path.join("assets", "images", "boss", filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale_size:
            img = pygame.transform.scale(img, scale_size)
        return img
    except (FileNotFoundError, pygame.error):
        return None

class Boss(Enemy):
    def __init__(self, pos, player, groups, boss_data):
        filename = boss_data["filename"]
        scale_size = boss_data["scale"]
        
        img = load_boss_image(filename, scale_size)
        if img is None:
            img = pygame.Surface(scale_size)
            img.fill((100, 0, 0) if "golem" in filename else (255, 100, 0))

        stats = {
            "hp": boss_data["hp"],
            "max_hp": boss_data["hp"],
            "speed": boss_data["speed"],
            "damage": boss_data["damage"],
            "exp": 1000,
            "name": boss_data["name"],
            "image": img,
            "attacks": boss_data.get("attacks", []) # configから技設定を受け取る
        }
        
        # --- グループの受け取り ---
        target_group = groups[1] if len(groups) > 1 else groups[0]
        self.camera_group = groups[0]
        self.bullet_group = groups[2] if len(groups) > 2 else None 

        super().__init__(pos, player, target_group, stats)
        
        # Hitboxの手動設定
        if "hitbox" in boss_data:
            hb_w, hb_h = boss_data["hitbox"]
            self.hitbox = pygame.Rect(0, 0, hb_w, hb_h)
            self.hitbox.center = self.rect.center

        # グループ登録 (弾グループ以外)
        for g in groups:
            if g != self.bullet_group:
                g.add(self)

        # 攻撃用タイマー
        self.last_attack_time = pygame.time.get_ticks() - 2000
        self.attack_cooldown = 1500 

    def update(self, dt):
        super().update(dt)
        self.check_attack()

    def check_attack(self):
        now = pygame.time.get_ticks()
        
        if self.bullet_group is None:
            return

        if now - self.last_attack_time > self.attack_cooldown:
            self.last_attack_time = now
            self.perform_skill()

    def perform_skill(self):
        # ★修正: config.py の attacks リストを使って攻撃する
        # これにより、config側で設定した弾のサイズや速度が反映されます
        attack_list = self.stats.get("attacks", [])
        base_damage = self.stats["damage"]
        
        if not attack_list:
            return

        for atk in attack_list:
            atk_type = atk["type"]
            img_name = atk["image"]
            count = atk["count"]
            speed = atk["speed"]
            size = atk.get("size", None) # configのサイズを取得
            dmg_rate = atk.get("damage_rate", 1.0)
            
            final_damage = int(base_damage * dmg_rate)
            
            if atk_type == "circle":
                self.shoot_circle(count, speed, final_damage, img_name, size)
            
            elif atk_type == "target":
                self.shoot_at(self.player.pos, speed, final_damage, img_name, size)
            
            elif atk_type == "random" or atk_type == "target_rapid":
                for _ in range(count):
                    offset = (random.randint(-60, 60), random.randint(-60, 60))
                    target = self.player.pos + pygame.math.Vector2(offset)
                    self.shoot_at(target, speed, final_damage, img_name, size)

    # ★引数に size を追加
    def shoot_at(self, target_pos, speed, damage, img, size=None):
        
        # 発射位置調整
        # ボスが 600px (半径300px) なので、350px 外側から発射する
        direction = pygame.math.Vector2(target_pos) - self.pos
        if direction.length() > 0: direction = direction.normalize()
        spawn_pos = self.pos + direction * 350 

        EnemyProjectile(spawn_pos, target_pos, speed, damage, [self.camera_group, self.bullet_group], img, scale_size=size)

    # ★引数に size を追加
    def shoot_circle(self, count, speed, damage, img, size=None):
        
        for i in range(count):
            angle = (360 / count) * i
            rad = math.radians(angle)
            vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            
            # ここも 350px に調整
            spawn_pos = self.pos + vec * 350
            target = self.pos + vec * 450
            
            EnemyProjectile(spawn_pos, target, speed, damage, [self.camera_group, self.bullet_group], img, scale_size=size)

    def take_damage(self, amount, knockback_force=0):
        super().take_damage(amount, knockback_force * 0.1)