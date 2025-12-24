import os

# --- 基本設定 ---
CAPTION = "Mobmania of Evolution"
# 開発時の基準サイズ (このサイズで作ったバランスを基準にする)
BASE_SCREEN_WIDTH = 800 

# 実行時に書き換わる変数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GLOBAL_SCALE = 1.0  # <--- 追加: 画面サイズに合わせた拡大倍率

FPS = 60

# --- 色の定義 (R, G, B) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
BG_COLOR = (30, 30, 30)

# --- プレイヤー設定 ---
PLAYER_SIZE = 40
PLAYER_SPEED = 300
PLAYER_COLOR = RED
ATTACK_COOLDOWN = 500  # ミリ秒
PLAYER_DAMAGE = 10     # 基礎攻撃力

# --- 弾丸設定 ---
BULLET_SPEED = 600
BULLET_SIZE = 10
BULLET_COLOR = YELLOW
BULLET_LIFETIME = 1000  # ミリ秒

# --- モブ設定 ---
MOB_IMAGE_DIR = "assets/images/mobs"

# モブの種類ごとのステータス設定
# size: 画像の大きさ (ピクセル)
# min_speed / max_speed: 進化における速度の限界値
MOB_BASE_STATS = {
    0: {
        "name": "Tree",
        "image": "mob_tree.png",
        "hp": 25,
        "speed": 40,
        "min_speed": 10,
        "max_speed": 80,   # 木はあまり速くなれない
        "size": 50,        # 少し大きめ
        "attack": 10,
        "defense_rate": 1.2,
        "attack_type": "contact"
    },
    1: {
        "name": "Kinoko",
        "image": "mob_kinoko.png",
        "hp": 10,
        "speed": 100,
        "min_speed": 50,
        "max_speed": 180,
        "size": 35,        # 標準より少し小さい
        "attack": 5,
        "defense_rate": 1.0,
        "attack_type": "contact"
    },
    2: {
        "name": "Golem",
        "image": "mob_golem.png",
        "hp": 50,
        "speed": 60,
        "min_speed": 20,
        "max_speed": 100,  # 重いので限界がある
        "size": 70,        # かなりデカい！
        "attack": 25,
        "defense_rate": 2.0,
        "attack_type": "contact"
    },
    3: {
        "name": "Bluebird",
        "image": "mob_bluebird.png",
        "hp": 8,
        "speed": 220,
        "min_speed": 100,
        "max_speed": 400,  # 超高速になれる可能性
        "size": 25,        # 小さい（当てにくい）
        "attack": 12,
        "defense_rate": 0.8,
        "attack_type": "contact"
    },
    4: {
        "name": "Snail",
        "image": "mob_snail.png",
        "hp": 15,
        "speed": 30,
        "min_speed": 5,
        "max_speed": 60,   # とても遅い
        "size": 30,        # 小さい
        "attack": 8,
        "defense_rate": 3.0,
        "attack_type": "contact"
    }
}