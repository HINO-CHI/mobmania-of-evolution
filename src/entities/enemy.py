# src/entities/enemy.py
import pygame
import os
import random
import time
from pygame.math import Vector2
import config

class Enemy(pygame.sprite.Sprite):
    # 画像を一度だけ読み込むためのキャッシュ（メモリ節約・高速化）
    _image_cache = {}

    def __init__(self, start_pos, player, stats=None):
        super().__init__()
        
        # ----------------------------------------------------
        # 1. ステータスの決定
        # ----------------------------------------------------
        if stats:
            # 進化などで既にステータスが決まっている場合
            self.stats = stats
            # データ不整合の保険（万が一type_idがない場合）
            if "type_id" not in self.stats: self.stats["type_id"] = 0
            if "image" not in self.stats: self.stats["image"] = config.MOB_BASE_STATS[0]["image"]
        else:
            # 第1世代：ランダムに種類を決める
            type_id = random.choice(list(config.MOB_BASE_STATS.keys()))
            base_data = config.MOB_BASE_STATS[type_id]
            
            # configのデータをコピーして個体のステータスにする
            self.stats = {
                "type_id": type_id,
                "name": base_data["name"],
                "image": base_data["image"],
                "hp": base_data["hp"],
                "max_hp": base_data["hp"], # HPバー表示用などに最大値も保存
                "speed": base_data["speed"],
                "attack": base_data["attack"],
                "defense_rate": base_data["defense_rate"],
                "attack_type": base_data["attack_type"]
            }

        self.player = player
        
        # ----------------------------------------------------
        # 2. 画像の読み込みと設定
        # ----------------------------------------------------
        image_name = self.stats["image"]
        
        # キャッシュになければロードする
        if image_name not in Enemy._image_cache:
            img_path = os.path.join(config.MOB_IMAGE_DIR, image_name)
            try:
                # 画像を読み込み、透明度対応(convert_alpha)
                img = pygame.image.load(img_path).convert_alpha()
                
                # サイズ調整 (今のところ一律40x40くらいにリサイズしておくと安全)
                # ※ 元画像のサイズをそのまま使いたい場合はここをコメントアウトしてください
                img = pygame.transform.scale(img, (40, 40))
                
                Enemy._image_cache[image_name] = img
            except FileNotFoundError:
                print(f"Error: Image {image_name} not found. Using fallback rect.")
                # 画像がない場合は緑の四角で代用
                surf = pygame.Surface((40, 40))
                surf.fill(config.GREEN)
                Enemy._image_cache[image_name] = surf

        self.image = Enemy._image_cache[image_name]
        self.rect = self.image.get_rect()
        
        # 位置合わせ
        self.pos = Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # ★ヒットボックス（当たり判定）の作成
        # 見た目(rect)より少し小さくすることで、理不尽な被弾を防ぐ
        self.hitbox = self.rect.inflate(-10, -10)

        # ----------------------------------------------------
        # 3. その他
        # ----------------------------------------------------
        self.spawn_time = time.time()
        self.death_time = 0

    def update(self, dt):
        # プレイヤーに向かうベクトル
        direction = self.player.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            
        # 移動
        self.pos += direction * self.stats["speed"] * dt
        
        # 座標更新
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center # ヒットボックスも追従させる

        # src/entities/enemy.py (Enemyクラスの中に追加)

    # ... (既存の __init__, update はそのまま) ...

    def take_damage(self, raw_damage):
        """
        ダメージを受ける処理。
        戻り値: Trueなら死亡、Falseなら生存
        """
        # 防御倍率でダメージを軽減 (例: rate 2.0 ならダメージ半減)
        actual_damage = raw_damage / self.stats["defense_rate"]
        
        # 1以上のダメージは最低限保証する（0ダメージ防止）
        actual_damage = max(1, int(actual_damage))
        
        self.stats["hp"] -= actual_damage
        print(f"{self.stats['name']} took {actual_damage} dmg! (HP: {self.stats['hp']})") # デバッグ用

        if self.stats["hp"] <= 0:
            return True # 死亡
        return False # 生存