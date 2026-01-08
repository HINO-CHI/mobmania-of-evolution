import os

# --- 基本設定 ---
CAPTION = "Mobmania of Evolution"
BASE_SCREEN_WIDTH = 800 

# 実行時に書き換わる変数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GLOBAL_SCALE = 1.0

FPS = 60

# --- 色の定義 ---
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
UI_BG_COLOR = (245, 222, 179)
UI_BORDER_COLOR = (255, 255, 255)
UI_TEXT_COLOR = (60, 40, 40)
UI_HIGHLIGHT_COLOR = (255, 240, 200)
UI_RIBBON_COLOR = (255, 140, 0)

# ==========================================
# UI SETTINGS
# ==========================================
FONT_PATH = "assets/fonts/pixel_font.ttf"

UI_COLORS = {
    "bg": (245, 222, 179),
    "border": (255, 255, 255),
    "ribbon": (255, 140, 0),
    "ribbon_border": (255, 255, 255),
    "text_title": (255, 255, 255),
    "text_body": (60, 40, 40),
    "text_detail": (100, 80, 80),
    "item_bg_normal": (235, 215, 180),
    "item_bg_hover": (255, 245, 220),
    "item_border_normal": (200, 180, 150),
    "item_border_hover": (255, 0, 0),
}

LEVELUP_SCREEN = {
    "panel_width": 1000,
    "panel_height": 750,
    "border_thickness": 8,
    "ribbon_width": 600,
    "ribbon_height": 80,
    "ribbon_offset_y": 40,
    "list_start_y": 100,
    "item_height": 160,
    "item_gap": 25,
    "icon_size": 100,
    "font_size_title": 56,
    "font_size_name": 36,
    "font_size_detail": 24
}

# --- プレイヤー設定 ---
PLAYER_SIZE = 80
PLAYER_SPEED = 300
PLAYER_COLOR = RED
ATTACK_COOLDOWN = 500
PLAYER_DAMAGE = 10
PLAYER_IMAGE_DIR = "assets/images/player"
PLAYER_IMAGE = "player_normal.png"

# --- 弾丸設定 ---
BULLET_SPEED = 600
BULLET_SIZE = 10
BULLET_COLOR = YELLOW
BULLET_LIFETIME = 1000

# --- モブ設定 ---
MOB_IMAGE_DIR = "assets/images/mobs"
MOB_BASE_STATS = {
    0: {"name": "Tree", "image": "mob_tree.png", "hp": 25, "speed": 50, "min_speed": 30, "max_speed": 100, "size": 70, "attack": 10, "defense_rate": 1.2, "attack_type": "contact"},
    1: {"name": "Kinoko", "image": "mob_kinoko.png", "hp": 10, "speed": 70, "min_speed": 30, "max_speed": 140, "size": 50, "attack": 5, "defense_rate": 1.0, "attack_type": "contact"},
    2: {"name": "Golem", "image": "mob_golem.png", "hp": 100, "speed": 10, "min_speed": 10, "max_speed": 40, "size": 170, "attack": 25, "defense_rate": 2.0, "attack_type": "contact"},
    3: {"name": "Bluebird", "image": "mob_bluebird.png", "hp": 8, "speed": 220, "min_speed": 100, "max_speed": 400, "size": 50, "attack": 12, "defense_rate": 0.8, "attack_type": "contact"},
    4: {"name": "Snail", "image": "mob_snail.png", "hp": 15, "speed": 30, "min_speed": 10, "max_speed": 60, "size": 40, "attack": 8, "defense_rate": 3.0, "attack_type": "contact"}
}

# --- 武器設定 ---
ITEM_IMAGE_DIR = "assets/images/items"
WEAPON_STATS = {
    "stick": {"name": "Wooden Stick", "tier": 0, "image": "items-level0-edge.png", "size": 80, "damage": 5, "cooldown": 600, "speed": 500, "spin_speed": 15},
    "pencil": {"name": "Magic Pencil", "tier": 1, "image": "items-level1-enpitu.png", "size": 60, "damage": 10, "cooldown": 500, "speed": 600},
    "bread": {"name": "Guardian Bread", "tier": 1, "image": "items-level1-shokupan.png", "size": 50, "damage": 5, "radius": 140, "orb_count": 3, "rot_speed": 0.05},
    "bear": {"name": "Bear Bomber", "tier": 1, "image": "items-level1-kumanuigurumi.png", "size": 120, "damage": 30, "cooldown": 1500, "fuse_time": 1000, "blast_radius": 150},
    "thunder": {"name": "Thunder Staff", "tier": 2, "image": "items-level2-thunder.png", "size": 60, "damage": 15, "cooldown": 800},
    "ice": {"name": "Ice Cream Cone", "tier": 2, "image": "items-level2-ice.png", "size": 50, "damage": 8, "cooldown": 400},
    "drill": {"name": "Giga Drill", "tier": 2, "image": "items-level2-drill.png", "size": 70, "damage": 20, "cooldown": 1000}
}

# ==========================================
# MAP & STAGE SETTINGS
# ==========================================
MAP_IMAGE_DIR = "assets/images/maps/stage1"

# config.py (STAGE_SETTINGS部分のみ修正)

STAGE_SETTINGS = {
    "grass": {
        "display_name": "Meadow",
        "desc": "Peaceful training ground.",
        "difficulty": 1,
        "bg_color": (120, 230, 120),
        
        "generation": {
            # --- 変更点 ---
            # obstacle_threshold: 0.60 くらいまで下げて「森の範囲」自体は広げます
            "obstacle_threshold": 0.90,
            
            # ★新規: その範囲内で実際に木が生える確率 (0.0 ~ 1.0)
            # 0.3 (30%) にすれば、森の中でもスカスカになり歩きやすくなります
            "obstacle_density": 0.20,
            
            "decoration_threshold": 0.40,
            "frequency": 8.0 
        },

        "assets": {
            "obstacles": [
                "stage1-iwa1.png", "stage1-iwa2.png", "stage1-koiwa.png",
                "stage1-ki1.png", "stage1-ki2.png", "stage1-ki3.png"
            ],
            "decorations": [
                "stage1-kusa2.png", "stage1-kusa3.png", 
                "stage1-kusa3-hana.png", "stage1-kusa5.png"
            ]
        }
    },
    # ... 他のステージも同様に ...

    "water": {
        "display_name": "Coast",
        "desc": "Slippery aquatic zone.",
        "bg_color": (30, 144, 255),
        "generation": {"obstacle_threshold": 0.8, "decoration_threshold": 0.5, "frequency": 8.0},
        "assets": {"obstacles": [], "decorations": []}
    },
    "volcano": {
        "display_name": "Inferno",
        "desc": "Scorching heat awaits.",
        "bg_color": (139, 0, 0),
        "generation": {"obstacle_threshold": 0.7, "decoration_threshold": 0.4, "frequency": 8.0},
        "assets": {"obstacles": [], "decorations": []}
    },
    "cloud": {
        "display_name": "Sky High",
        "desc": "Battle in the clouds.",
        "bg_color": (200, 200, 255),
        "generation": {"obstacle_threshold": 0.85, "decoration_threshold": 0.6, "frequency": 8.0},
        "assets": {"obstacles": [], "decorations": []}
    }
}

# ==========================================
# MAP OBJECT DETAILS (大きさ・当たり判定の調整)
# ==========================================
# ファイル名ごとに詳細設定を行います。
# scale: 画像の拡大倍率 (1.0 = 基準サイズ 80px)
# hitbox_w: 当たり判定の幅 (0.0 ~ 1.0, 1.0で画像と同じ幅)
# hitbox_h: 当たり判定の高さ (0.0 ~ 1.0)
# offset_y: 当たり判定の縦位置調整 (プラスで下へ、マイナスで上へ)

MAP_OBJECT_SETTINGS = {
    # --- 障害物 (木・岩) ---
    # 木は「根元」だけ判定を持たせるのがコツです
    "stage1-ki1.png": { "scale": 3.5, "hitbox_w": 0.3, "hitbox_h": 0.5, "offset_y": 10 },
    "stage1-ki2.png": { "scale": 3.4, "hitbox_w": 0.3, "hitbox_h": 0.5, "offset_y": 15 },
    "stage1-ki3.png": { "scale": 3.3, "hitbox_w": 0.3, "hitbox_h": 0.8, "offset_y": 10 },

    # 岩は下半分くらいに判定を持たせると自然です
    "stage1-iwa1.png": { "scale": 2.0, "hitbox_w": 0.5, "hitbox_h": 1.0, "offset_y": 15 },
    "stage1-iwa2.png": { "scale": 1.9, "hitbox_w": 0.5, "hitbox_h": 1.0, "offset_y": 10 },
    "stage1-koiwa.png": { "scale": 1.6, "hitbox_w": 0.2, "hitbox_h": 0.2, "offset_y": 5 },
    
    # --- 装飾 (草・花) ---
    # 当たり判定はありませんが、大きさ(scale)は反映されます
    "stage1-kusa2.png": { "scale": 0.8 },
    "stage1-kusa3.png": { "scale": 0.9 },
    "stage1-kusa5.png": { "scale": 1.1 },
}

# ==========================================
# UI BAR SETTINGS
# ==========================================
# HPバー設定
UI_HP_BAR_WIDTH = 200
UI_HP_BAR_HEIGHT = 20
UI_HP_COLOR = (50, 205, 50)       # 緑
UI_HP_BG_COLOR = (60, 0, 0)       # 暗い赤（ダメージ受けた時の背景）
UI_HP_BORDER_COLOR = (255, 255, 255)

# 経験値バー設定
UI_XP_BAR_HEIGHT = 30
UI_XP_COLOR = (0, 191, 255)       # 水色
UI_XP_BG_COLOR = (20, 20, 40)     # 暗い青

# config.py (末尾に追加)

# ==========================================
# GAME OVER SCREEN SETTINGS
# ==========================================
GAME_OVER_BG_COLOR = (0, 0, 0)       # 黒背景
GAME_OVER_TEXT_COLOR = (100, 200, 255) # ネオンっぽい青
GAME_OVER_OPTION_COLOR = (255, 255, 255) # 白
GAME_OVER_SELECT_COLOR = (255, 255, 0)   # 黄色（選択時）
GAME_OVER_FONT_SIZE_TITLE = 100
GAME_OVER_FONT_SIZE_OPTION = 36

# ==========================================
# ドロップアイテム設定
# ==========================================
DROP_SETTINGS = {
    "exp_size": (50, 50),       # 経験値ジェムの表示サイズ
    "healing_size": (70, 70),   # 回復アイテムの表示サイズ
    "magnet_range": 150,        # プレイヤーが近づいた時の吸い寄せ開始距離
    "acceleration": 900         # 吸い寄せ時の加速度
}