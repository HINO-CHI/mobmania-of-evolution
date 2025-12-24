# src/entities/enemy.py
import pygame
import os
import random
import time
from pygame.math import Vector2
import config

class Enemy(pygame.sprite.Sprite):
    # 画像キャッシュ：キーに対して (左向き画像, 右向き画像) のタプルを保存する
    _image_cache = {}

    def __init__(self, start_pos, player, stats=None):
        super().__init__()
        
        # ----------------------------------------------------
        # 1. ステータスの決定
        # ----------------------------------------------------
        if stats:
            self.stats = stats
            # 必須データの欠落防止
            if "type_id" not in self.stats: self.stats["type_id"] = 0
            
            # 画像やサイズがない場合はconfigから補完
            base = config.MOB_BASE_STATS[self.stats["type_id"]]
            if "image" not in self.stats: self.stats["image"] = base["image"]
            if "size" not in self.stats: self.stats["size"] = base["size"]
        else:
            # 第1世代：ランダム生成
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
        
        # ----------------------------------------------------
        # 2. 画像の読み込みと反転画像の準備
        # ----------------------------------------------------
        image_name = self.stats["image"]
        
        # 画面倍率を適用した表示サイズを計算
        base_size = self.stats["size"]
        scale = getattr(config, "GLOBAL_SCALE", 1.0)
        display_size = int(base_size * scale)

        # キャッシュキー
        cache_key = f"{image_name}_{display_size}"

        # キャッシュになければロードして、左右セットで作る
        if cache_key not in Enemy._image_cache:
            img_path = os.path.join(config.MOB_IMAGE_DIR, image_name)
            try:
                # 元画像（左向きと仮定）をロードしてリサイズ
                img_left = pygame.image.load(img_path).convert_alpha()
                img_left = pygame.transform.scale(img_left, (display_size, display_size))
                
                # ★ここがポイント：左右反転した画像を作成 (第2引数Trueで左右反転)
                img_right = pygame.transform.flip(img_left, True, False)
                
                # 左右セットでキャッシュに保存
                Enemy._image_cache[cache_key] = (img_left, img_right)
                
            except FileNotFoundError:
                print(f"Error: Image {image_name} not found. Using fallback rect.")
                surf = pygame.Surface((display_size, display_size))
                surf.fill(config.GREEN)
                # フォールバックの場合は左右同じでOK
                Enemy._image_cache[cache_key] = (surf, surf)

        # キャッシュから左右の画像を取得
        self.image_left, self.image_right = Enemy._image_cache[cache_key]
        
        # 初期状態は「左向き」とする
        self.image = self.image_left
        self.facing_right = False # 現在右を向いているかどうかのフラグ

        self.rect = self.image.get_rect()
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # ヒットボックス
        inflation = -1 * (display_size // 4)
        self.hitbox = self.rect.inflate(inflation, inflation)

        # ----------------------------------------------------
        # 3. その他
        # ----------------------------------------------------
        self.spawn_time = time.time()
        self.death_time = 0

    def update(self, dt):
        # プレイヤーに向かうベクトル
        direction = self.player.pos - self.pos
        
        # ★向きの更新処理
        # プレイヤーが右にいて、今左を向いているなら → 右を向く
        if direction.x > 0 and not self.facing_right:
            self.image = self.image_right
            self.facing_right = True
        # プレイヤーが左にいて、今右を向いているなら → 左を向く
        elif direction.x < 0 and self.facing_right:
            self.image = self.image_left
            self.facing_right = False

        # 移動処理
        if direction.length() > 0:
            direction = direction.normalize()
            
        self.pos += direction * self.stats["speed"] * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center

    def take_damage(self, raw_damage):
        defense = self.stats.get("defense_rate", 1.0)
        actual_damage = raw_damage / defense
        actual_damage = max(1, int(actual_damage))
        self.stats["hp"] -= actual_damage
        
        if self.stats["hp"] <= 0:
            return True
        return False