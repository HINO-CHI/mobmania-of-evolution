import pygame
import math
import os
import random
import config  # ★追加: configをインポート

# 画像読み込み用のヘルパー関数
def load_drop_image(filename, size):
    # パス: assets/images/drops/filename
    path = os.path.join("assets", "images", "drops", filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except (FileNotFoundError, pygame.error):
        return None

# ==========================================
# ベースクラス: DropItem
# ==========================================
class DropItem(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        
        # 画像が設定されていない場合のフォールバック（白い四角）
        if not hasattr(self, 'image') or self.image is None:
            self.image = pygame.Surface((10, 10))
            self.image.fill((255, 255, 255))
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        # 出現時に少し散らばる演出
        scatter_x = random.uniform(-15, 15)
        scatter_y = random.uniform(-15, 15)
        self.pos.x += scatter_x
        self.pos.y += scatter_y
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = 0
        # ★変更: configから読み込み
        self.acceleration = config.DROP_SETTINGS["acceleration"]
        self.magnet_range = config.DROP_SETTINGS["magnet_range"]
        self.is_magnetized = False

    def update(self, dt, player_pos=None):
        if player_pos is None:
            return

        direction = player_pos - self.pos
        distance = direction.length()
        
        if distance < self.magnet_range:
            self.is_magnetized = True
        
        if self.is_magnetized and distance > 0:
            direction.normalize_ip()
            self.speed += self.acceleration * dt
            self.pos += direction * self.speed * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

# ==========================================
# 経験値ジェム
# ==========================================
class ExpGem(DropItem):
    def __init__(self, pos, value, image_name, color_fallback, groups):
        # ★変更: configからサイズ取得
        size = config.DROP_SETTINGS["exp_size"]
        self.image = load_drop_image(image_name, size=size)
        
        if self.image is None:
            # 画像がない場合はフォールバック図形もサイズに合わせて調整（簡易的に固定値でもOK）
            w, h = size
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            # ひし形を描画 (サイズに合わせて座標計算)
            pygame.draw.polygon(self.image, color_fallback, [(w//2, 0), (w, h//2), (w//2, h), (0, h//2)])
            pygame.draw.polygon(self.image, (255, 255, 255), [(w//2, 2), (w-2, h//2), (w//2, h-2), (2, h//2)], 1)
        
        self.value = value
        super().__init__(pos, groups)

class ExpBlue(ExpGem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=10, image_name="exp_blue.png", color_fallback=(0, 200, 255), groups=groups)

class ExpYellow(ExpGem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=50, image_name="exp_yellow.png", color_fallback=(255, 255, 0), groups=groups)

class ExpPurple(ExpGem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=200, image_name="exp_purple.png", color_fallback=(200, 0, 255), groups=groups)


# ==========================================
# 回復アイテム (HealingItem)
# ==========================================
class HealingItem(DropItem):
    def __init__(self, pos, value, image_name, groups):
        # ★変更: configからサイズ取得
        size = config.DROP_SETTINGS["healing_size"]
        self.image = load_drop_image(image_name, size=size)
        
        # 画像がない場合のフォールバック
        if self.image is None:
            w, h = size
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 50, 50), (w//2, h//2), w//2 - 2)
            pygame.draw.circle(self.image, (255, 150, 150), (w//2 - 2, h//2 - 2), w//4)
            
        self.value = value
        super().__init__(pos, groups)

class Candy(HealingItem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=20, image_name="candy.png", groups=groups)

class Chocolate(HealingItem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=40, image_name="chocolate.png", groups=groups)

class ChortCake(HealingItem):
    def __init__(self, pos, groups):
        super().__init__(pos, value=60, image_name="chort_cake.png", groups=groups)