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

# Mobmania風カラーパレット
UI_BG_COLOR = (245, 222, 179)      # 薄いベージュ (背景)
UI_BORDER_COLOR = (255, 255, 255)  # 白 (枠線)
UI_TEXT_COLOR = (60, 40, 40)       # 濃い焦げ茶 (文字色)
UI_HIGHLIGHT_COLOR = (255, 240, 200) # 選択中の明るい色
UI_RIBBON_COLOR = (255, 140, 0)    # オレンジ (リボン)

# ==========================================
# UI SETTINGS (Mobmania Style)
# ==========================================

# フォント
FONT_PATH = "assets/fonts/pixel_font.ttf"

# 色設定
UI_COLORS = {
    "bg": (245, 222, 179),           # ベージュ背景
    "border": (255, 255, 255),       # 白枠
    "ribbon": (255, 140, 0),         # オレンジリボン
    "ribbon_border": (255, 255, 255),
    "text_title": (255, 255, 255),
    "text_body": (60, 40, 40),       # 焦げ茶
    "text_detail": (100, 80, 80),
    "item_bg_normal": (235, 215, 180),
    "item_bg_hover": (255, 245, 220),
    "item_border_normal": (200, 180, 150),
    "item_border_hover": (255, 0, 0), # 赤
}

# レイアウト設定 (ここをいじれば大きさ変え放題！)
LEVELUP_SCREEN = {
    # メインパネル
    "panel_width": 1000,    # 大きく！
    "panel_height": 750,
    "border_thickness": 8,
    
    # リボン
    "ribbon_width": 600,
    "ribbon_height": 80,
    "ribbon_offset_y": 40,  # パネルの上端からどれだけ飛び出させるか
    
    # リスト配置
    "list_start_y": 100,    # パネル上端からの開始位置
    "item_height": 160,     # 各カードの高さ
    "item_gap": 25,         # カード間の隙間
    
    # アイコン・装飾
    "icon_size": 100,       # アイコン画像サイズ
    
    # フォントサイズ
    "font_size_title": 56,
    "font_size_name": 36,
    "font_size_detail": 24
}

# --- プレイヤー設定 ---
PLAYER_SIZE = 80
PLAYER_SPEED = 300
PLAYER_COLOR = RED
ATTACK_COOLDOWN = 500  # ミリ秒
PLAYER_DAMAGE = 10     # 基礎攻撃力

# ★追加: プレイヤー画像の設定
PLAYER_IMAGE_DIR = "assets/images/player"
PLAYER_IMAGE = "player_normal.png"

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
        "speed": 50,
        "min_speed": 30,
        "max_speed": 100,   # 木はあまり速くなれない
        "size": 70,        # 少し大きめ
        "attack": 10,
        "defense_rate": 1.2,
        "attack_type": "contact"
    },
    1: {
        "name": "Kinoko",
        "image": "mob_kinoko.png",
        "hp": 10,
        "speed": 70,
        "min_speed": 30,
        "max_speed": 140,
        "size": 50,        # 標準より少し小さい
        "attack": 5,
        "defense_rate": 1.0,
        "attack_type": "contact"
    },
    2: {
        "name": "Golem",
        "image": "mob_golem.png",
        "hp": 100,
        "speed": 10,
        "min_speed": 10,
        "max_speed": 40,  # 重いので限界がある
        "size": 170,        # かなりデカい！
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
        "size": 50,        # 小さい（当てにくい）
        "attack": 12,
        "defense_rate": 0.8,
        "attack_type": "contact"
    },
    4: {
        "name": "Snail",
        "image": "mob_snail.png",
        "hp": 15,
        "speed": 30,
        "min_speed": 10,
        "max_speed": 60,   # とても遅い
        "size": 40,        # 小さい
        "attack": 8,
        "defense_rate": 3.0,
        "attack_type": "contact"
    }
}
# config.py (WEAPON_STATS部分)

# ==========================================
# WEAPON SETTINGS
# ==========================================
ITEM_IMAGE_DIR = "assets/images/items"

# Tier 1: 初期〜序盤
# Tier 2: レベル2で解放される武器
WEAPON_STATS = {
    # --- Tier 0: 初期装備 ---
    "stick": {
        "name": "Wooden Stick",
        "tier": 0,
        "image": "items-level0-edge.png",
        "size": 80, "damage": 5, "cooldown": 600, "speed": 500, "spin_speed": 15
    },

    # --- Tier 1: レベル1武器 (既存) ---
    "pencil": {
        "name": "Magic Pencil",
        "tier": 1,
        "image": "items-level1-enpitu.png",
        "size": 60, "damage": 10, "cooldown": 500, "speed": 600
    },
    "bread": {
        "name": "Guardian Bread",
        "tier": 1,
        "image": "items-level1-shokupan.png",
        "size": 50, "damage": 5, "radius": 140, "orb_count": 3, "rot_speed": 0.05
    },
    "bear": {
        "name": "Bear Bomber",
        "tier": 1,
        "image": "items-level1-kumanuigurumi.png",
        "size": 120, "damage": 30, "cooldown": 1500, "fuse_time": 1000, "blast_radius": 150
    },

    # --- Tier 2: レベル2武器 (新規枠組み・画像はまだない) ---
    "thunder": {
        "name": "Thunder Staff",
        "tier": 2,
        "image": "items-level2-thunder.png", # 後で画像を追加
        "size": 60, "damage": 15, "cooldown": 800
    },
    "ice": {
        "name": "Ice Cream Cone",
        "tier": 2,
        "image": "items-level2-ice.png",
        "size": 50, "damage": 8, "cooldown": 400
    },
    "drill": {
        "name": "Giga Drill",
        "tier": 2,
        "image": "items-level2-drill.png",
        "size": 70, "damage": 20, "cooldown": 1000
    }
}