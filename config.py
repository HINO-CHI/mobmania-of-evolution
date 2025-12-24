import os

# --- 基本設定 ---
CAPTION = "Mobmania of Evolution"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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
ATTACK_COOLDOWN = 500
PLAYER_DAMAGE = 10  # <--- 追加: 基礎攻撃力

# --- 弾丸設定 ---
BULLET_SPEED = 600
BULLET_SIZE = 10
BULLET_COLOR = YELLOW
BULLET_LIFETIME = 1000  # ミリ秒

# --- モブ設定 ---
# モブ画像のパス
MOB_IMAGE_DIR = "assets/images/mobs"

# モブの種類ごとの基本ステータス設定
MOB_BASE_STATS = {
    0: {
        "name": "Tree",
        "image": "mob_tree.png",
        "hp": 25,
        "speed": 40,
        "attack": 10,
        "defense_rate": 1.2,
        "attack_type": "contact"
    },
    1: {
        "name": "Kinoko",
        "image": "mob_kinoko.png",
        "hp": 10,
        "speed": 100,
        "attack": 5,
        "defense_rate": 1.0,
        "attack_type": "contact"
    },
    2: {
        "name": "Golem",
        "image": "mob_golem.png",
        "hp": 50,
        "speed": 60,
        "attack": 25,
        "defense_rate": 2.0,
        "attack_type": "contact"
    },
    3: {
        "name": "Bluebird",
        "image": "mob_bluebird.png",
        "hp": 8,
        "speed": 220,
        "attack": 12,
        "defense_rate": 0.8,
        "attack_type": "contact"
    },
    4: {
        "name": "Snail",
        "image": "mob_snail.png",
        "hp": 15,
        "speed": 30,
        "attack": 8,
        "defense_rate": 3.0,
        "attack_type": "contact"
    }
}