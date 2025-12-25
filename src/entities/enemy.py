# src/entities/enemy.py
import pygame
import os
import random
import time
from pygame.math import Vector2
import config

class Enemy(pygame.sprite.Sprite):
    _image_cache = {}

    def __init__(self, start_pos, player, enemy_group, stats=None):
        super().__init__()
        self.enemy_group = enemy_group
        
        # --- 1. ステータス設定 ---
        if stats:
            self.stats = stats
            if "type_id" not in self.stats: self.stats["type_id"] = 0
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
        image_name = self.stats["image"]
        base_size = self.stats["size"]
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
        
        # ★ご指定通り 15フレームに1回 計算する
        self.update_interval = 15
        
        # タイミングを分散させる（全員が一斉に計算しないように）
        self.separation_timer = id(self) % self.update_interval

    def update(self, dt):
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
        # ★修正: 係数を下げて (0.5)、バウンドしないように「そっと」離れるようにする
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
        limit = 3 # 計算する相手の上限
        
        for neighbor in neighbors:
            if neighbor == self:
                continue
            
            diff = self.pos - neighbor.pos
            dist = diff.length()
            
            # 接触している場合のみ計算
            min_dist = self.radius + neighbor.radius
            
            if 0 < dist < min_dist:
                diff = diff.normalize()
                # ★修正: 距離による重み付けを廃止し、単純な方向ベクトルにする
                # これにより「近づきすぎたときに急激に弾かれる」動きを防ぎます
                separation += diff
                count += 1
            
            if count >= limit:
                break
        
        if count > 0:
            # 複数の相手がいる場合は平均化して正規化
            separation /= count
            if separation.length() > 0:
                separation = separation.normalize()

        return separation

    def take_damage(self, raw_damage):
        defense = self.stats.get("defense_rate", 1.0)
        actual_damage = raw_damage / defense
        actual_damage = max(1, int(actual_damage))
        self.stats["hp"] -= actual_damage
        if self.stats["hp"] <= 0:
            return True
        return False