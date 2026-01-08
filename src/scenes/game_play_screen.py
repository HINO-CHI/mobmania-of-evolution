# src/scenes/game_play_screen.py
import pygame
import random
import time
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.weapons import (
    PencilGun, BreadShield, BearSmash, WoodenStick,
    ThunderStaff, IceCream, GigaDrill,
    load_weapon_image
)
from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager
from src.system.map_generator import MapGenerator
from src.scenes.game_play import CameraGroup
from src.scenes.game_play import FloatingText

AGGRO_PHRASES = [
    "Ouch! You're dead!",    # いった！お前死んだな！
    "Damn it! Watch out!",   # くそっ！気をつけろ！
    "Is that all?!",         # その程度か？！
    "You'll pay for that!",  # 覚えてろよ！
    "Hey! That hurt!",       # おい！痛えよ！
    "Don't touch me!",       # 触んな！
    "Just a scratch!",       # かすり傷だ！
]

def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)


# ==========================================
# ゲームプレイ画面クラス
# ==========================================
class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)
        self.game_state = "PLAYING"
        
        self.current_generation = 1
        self.kill_count = 0
        self.level = 1 
        self.next_level_kill = 5
        self.upgrade_options = [] 
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []
        self.last_spawn_time = 0
        self.spawn_interval = 800
        self.last_damage_time = 0

        self.camera_group = CameraGroup()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.decorations = pygame.sprite.Group()

        self.map_gen = MapGenerator(self.biome)
        self.map_gen.setup(self.obstacles, self.decorations)
        
        self.bg_color = config.STAGE_SETTINGS.get(self.biome, {}).get("bg_color", (34, 139, 34))

        self.player = Player((0, 0), self.camera_group, self.bullets_group, self.enemies_group)
        self.camera_group.add(self.player)
        
        self.map_gen.update(self.player.pos)
        self.camera_group.add(self.obstacles.sprites())
        
        try:
            self.ui_font = pygame.font.Font(config.FONT_PATH, 20)
            self.ui_font_large = pygame.font.Font(config.FONT_PATH, 40)
            self.ui_font_bold = pygame.font.Font(config.FONT_PATH, 22) 
        except:
            self.ui_font = pygame.font.SysFont(None, 20)
            self.ui_font_large = pygame.font.SysFont(None, 40)
            self.ui_font_bold = pygame.font.SysFont(None, 22)

    def update(self, dt):
        if self.game_state == "LEVEL_UP": return

        self.map_gen.update(self.player.pos)
        self.camera_group.add(self.obstacles.sprites())
        self.spawn_enemies()
        
        self.camera_group.update(dt)
        
        hits_obstacle = pygame.sprite.spritecollide(self.player, self.obstacles, False, collided=collide_hit_rect)
        if hits_obstacle:
            for obs in hits_obstacle:
                obs_rect = getattr(obs, 'hitbox', obs.rect)
                player_rect = self.player.hitbox
                dx = player_rect.centerx - obs_rect.centerx
                dy = player_rect.centery - obs_rect.centery
                if abs(dx) > abs(dy):
                    self.player.pos.x += 5 if dx > 0 else -5
                else:
                    self.player.pos.y += 5 if dy > 0 else -5
                self.player.hitbox.center = (round(self.player.pos.x), round(self.player.pos.y))
                self.player.rect.center = self.player.hitbox.center

        # 弾 vs 敵
        hits = pygame.sprite.groupcollide(self.bullets_group, self.enemies_group, True, False, collided=collide_hit_rect)
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.take_damage(bullet.damage)
                # ★追加: 敵へのダメージ表示（黄色）
                dmg_text = FloatingText(enemy.rect.center, str(bullet.damage), (255, 255, 0))
                self.camera_group.add(dmg_text)

        # 敵 vs プレイヤー (ダメージ)
        current_time = pygame.time.get_ticks()
        hits_player = pygame.sprite.spritecollide(self.player, self.enemies_group, False, collided=collide_hit_rect)
        if hits_player:
            if current_time - self.last_damage_time > 500:
                damage = 10 
                self.player.take_damage(damage)
                self.last_damage_time = current_time
                
                # ★追加: プレイヤーの被ダメージ表示（赤字）
                # 頭上より少し低い位置に表示
                dmg_pos = (self.player.rect.centerx + random.randint(-10, 10), self.player.rect.top)
                dmg_text = FloatingText(dmg_pos, f"-{damage}", (255, 0, 0))
                self.camera_group.add(dmg_text)

                # ダメージボイス（セリフ）
                # 文字と重ならないようにもう少し上に表示
                text_pos = (self.player.rect.centerx, self.player.rect.top - 40)
                phrase = random.choice(AGGRO_PHRASES)
                floating_text = FloatingText(text_pos, phrase)
                self.camera_group.add(floating_text)

                if self.player.hp <= 0:
                    print("Player Died! Transitioning to Game Over state.")
                    self.game_state = "GAME_OVER"
                    return "GAME_OVER"

        for enemy in self.enemies_group:
            if enemy.stats["hp"] <= 0:
                self.handle_enemy_death(enemy)
        
        if self.game_state == "GAME_OVER":
            return "GAME_OVER"

        return None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "TITLE"
                if event.key == pygame.K_l: 
                    self.kill_count += self.next_level_kill
                    self.check_level_up()
                if event.key == pygame.K_h:
                    self.camera_group.debug_mode = not self.camera_group.debug_mode

            if self.game_state == "LEVEL_UP":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: self.handle_levelup_click(event.pos)

    def handle_enemy_death(self, enemy):
        enemy.death_time = time.time()
        self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
        enemy.kill()
        self.mobs_killed_in_wave += 1
        self.kill_count += 1
        if self.mobs_killed_in_wave >= self.wave_threshold: self.start_next_wave()
        self.check_level_up()

    def check_level_up(self):
        if self.kill_count >= self.next_level_kill:
            current_target = self.next_level_kill
            self.next_level_kill = current_target * 2 if current_target < 160 else current_target + 160
            self.start_level_up_sequence()

    def start_level_up_sequence(self):
        self.level += 1
        self.game_state = "LEVEL_UP"
        print(f"=== LEVEL UP! Lv.{self.level} ===")
        target_tier = 2 if self.level >= 3 else 1
        weapon_pool = []
        if target_tier == 1:
            weapon_pool = [(PencilGun, "pencil"), (BreadShield, "bread"), (BearSmash, "bear")]
        else:
            weapon_pool = [(ThunderStaff, "thunder"), (IceCream, "ice"), (GigaDrill, "drill")]
        count = min(len(weapon_pool), 3)
        self.upgrade_options = random.sample(weapon_pool, count)

    def handle_levelup_click(self, mouse_pos):
        layout = config.LEVELUP_SCREEN
        panel_x = (config.SCREEN_WIDTH - layout["panel_width"]) // 2
        panel_y = (config.SCREEN_HEIGHT - layout["panel_height"]) // 2
        current_y = panel_y + layout["list_start_y"]
        for i, (weapon_class, w_key) in enumerate(self.upgrade_options):
            item_width = layout["panel_width"] - 80 
            item_rect = pygame.Rect(panel_x + 40, current_y, item_width, layout["item_height"])
            if item_rect.collidepoint(mouse_pos):
                self.player.add_weapon(weapon_class)
                self.game_state = "PLAYING"
                print(f"Selected: {weapon_class.__name__}")
                break
            current_y += layout["item_height"] + layout["item_gap"]

    def start_next_wave(self):
        self.current_generation += 1
        self.mobs_killed_in_wave = 0
        new_stats_list = self.evo_manager.create_next_generation_stats(self.biome, 20)
        if new_stats_list:
            self.pending_stats_queue.extend(new_stats_list)

    def spawn_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
            spawn_pos = self.get_random_spawn_pos()
            stats_to_use = self.pending_stats_queue.pop(0) if self.pending_stats_queue else None
            enemy = Enemy(spawn_pos, self.player, self.enemies_group, stats=stats_to_use)
            self.camera_group.add(enemy) 
            self.enemies_group.add(enemy)
            self.last_spawn_time = current_time

    def get_random_spawn_pos(self):
        cx = self.player.rect.centerx - config.SCREEN_WIDTH // 2
        cy = self.player.rect.centery - config.SCREEN_HEIGHT // 2
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 100
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH) + cx, cy - margin)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH) + cx, cy + config.SCREEN_HEIGHT + margin)
        elif edge == 'left':
            return (cx - margin, random.randint(0, config.SCREEN_HEIGHT) + cy)
        elif edge == 'right':
            return (cx + config.SCREEN_WIDTH + margin, random.randint(0, config.SCREEN_HEIGHT) + cy)
        return (cx, cy)

    def draw(self, screen):
        # メイン描画（背景、キャラ、敵など）
        self.camera_group.custom_draw(self.player, self.bg_color, self.decorations)
        
        # ★追加: キャラクター追従HPバーを描画
        # UIよりも先に描画することで、メニュー等よりは下になるようにします
        self.draw_player_health_bar(screen)
        
        # UI描画（経験値バー、武器スロットなど）
        self.draw_ui(screen)
        
        if self.game_state == "LEVEL_UP":
            self.draw_level_up_screen(screen)

    # ★新規追加: プレイヤーの足元にHPバーを表示
    def draw_player_health_bar(self, screen):
        # プレイヤーの生存確認
        if self.player.hp <= 0: return

        # カメラのオフセットを取得してスクリーン座標を計算
        # ※CameraGroupが self.offset を持っている一般的な実装を想定
        offset = getattr(self.camera_group, 'offset', pygame.math.Vector2(0, 0))
        
        # プレイヤーの中心座標からオフセットを引くとスクリーン上の座標になります
        screen_center = self.player.rect.center - offset
        
        # バーのサイズと位置設定
        bar_width = 70   # バーの幅
        bar_height = 10  #バーの高さ
         
        # 足元（中心からY方向に少し下）に配置
        # キャラクターのサイズに合わせて +25 などの数値を調整してください
        draw_x = screen_center.x - bar_width // 2
        draw_y = screen_center.y + 45 
        
        # HP比率
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        
        # 描画 (背景 -> 中身 -> 枠)
        # 背景(黒)
        pygame.draw.rect(screen, (0, 0, 0), (draw_x, draw_y, bar_width, bar_height))
        # HP(緑)
        color = (0, 255, 0) if hp_ratio > 0.3 else (255, 0, 0) # ピンチなら赤
        pygame.draw.rect(screen, color, (draw_x, draw_y, bar_width * hp_ratio, bar_height))
        # 枠(白)
        pygame.draw.rect(screen, (255, 255, 255), (draw_x, draw_y, bar_width, bar_height), 1)

    def draw_ui(self, screen):
        # 1. 経験値バー (画面下部)
        xp_ratio = min(1.0, self.kill_count / self.next_level_kill) if self.next_level_kill > 0 else 0
        
        bar_h = config.UI_XP_BAR_HEIGHT # 30推奨
        bar_y = config.SCREEN_HEIGHT - bar_h
        
        pygame.draw.rect(screen, config.UI_XP_BG_COLOR, (0, bar_y, config.SCREEN_WIDTH, bar_h))
        pygame.draw.rect(screen, config.UI_XP_COLOR, (0, bar_y, config.SCREEN_WIDTH * xp_ratio, bar_h))
        pygame.draw.rect(screen, config.WHITE, (0, bar_y, config.SCREEN_WIDTH, bar_h), 1)

        exp_text = "EXP"
        shadow = self.ui_font_bold.render(exp_text, True, config.BLACK)
        main = self.ui_font_bold.render(exp_text, True, config.WHITE)
        text_y = bar_y + (bar_h - main.get_height()) // 2
        screen.blit(shadow, (12, text_y + 2))
        screen.blit(main, (10, text_y))

        # 3. テキスト
        level_text = self.ui_font_large.render(f"LV {self.level}", True, config.WHITE)
        level_shadow = self.ui_font_large.render(f"LV {self.level}", True, config.BLACK)
        lvl_x = config.SCREEN_WIDTH - level_text.get_width() - 20
        lvl_y = 20
        screen.blit(level_shadow, (lvl_x + 2, lvl_y + 2))
        screen.blit(level_text, (lvl_x, lvl_y))
        
        hp_text = f"{int(self.player.hp)}/{self.player.max_hp}"
        hp_surf = self.ui_font.render(hp_text, True, config.WHITE)

        # ★追加: 武器スロットの描画
        self.draw_weapon_slots(screen)

    def draw_weapon_slots(self, screen):
        # 設定
        icon_size = 60       # アイコンの大きさ
        padding = 4          # アイコン同士の間隔
        start_x = 0         # 左端の開始位置 (HPバーと同じX座標)
        start_y = 0         # 上端の開始位置 (HPバーの下)
        
        # プレイヤーが weapon リストを持っている前提
        # もし player.weapons が存在しない場合はエラー回避のため空リストとする
        weapons = getattr(self.player, "weapons", [])

        for i, weapon in enumerate(weapons):
            x = start_x + (icon_size + padding) * i
            y = start_y
            
            # 1. 背景ボックス（黒の半透明枠）
            slot_rect = pygame.Rect(x, y, icon_size, icon_size)
            s = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128)) # 半透明の黒
            screen.blit(s, (x, y))
            
            # 枠線
            pygame.draw.rect(screen, (200, 200, 200), slot_rect, 1)

            # 2. 武器アイコンの描画
            # 武器クラスが image 属性を持っているか、もしくはクラス名から画像をロードする
            # ここでは安全のため try-except や属性チェックを行います
            try:
                img = None
                # パターンA: 武器インスタンス自体が image を持っている場合
                if hasattr(weapon, "image") and weapon.image:
                    img = weapon.image
                # パターンB: main.py で使っている load_weapon_image 関数を使う場合（要import）
                # ※ここでは簡易的に「名前の頭文字」を表示するフォールバックを入れます
                
                if img:
                    # アイコンサイズに合わせて縮小
                    img = pygame.transform.scale(img, (icon_size - 4, icon_size - 4))
                    screen.blit(img, (x + 2, y + 2))
                else:
                    # 画像がない場合は武器名の頭文字を表示
                    name = getattr(weapon, "name", "?")
                    text_surf = self.ui_font_bold.render(name[:1], True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=(x + icon_size//2, y + icon_size//2))
                    screen.blit(text_surf, text_rect)

            except Exception as e:
                print(f"Icon draw error: {e}")

            # 3. レベル表示（右下に小さく）
            lvl = getattr(weapon, "level", 1)
            lvl_surf = self.ui_font.render(str(lvl), True, (255, 255, 0)) # 黄色文字
            # 少し小さくスケールしても良い
            lvl_rect = lvl_surf.get_rect(bottomright=(x + icon_size - 2, y + icon_size - 2))
            screen.blit(lvl_surf, lvl_rect)

    def draw_level_up_screen(self, screen):
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        layout = config.LEVELUP_SCREEN
        colors = config.UI_COLORS
        panel_x = (config.SCREEN_WIDTH - layout["panel_width"]) // 2
        panel_y = (config.SCREEN_HEIGHT - layout["panel_height"]) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, layout["panel_width"], layout["panel_height"])
        pygame.draw.rect(screen, colors["bg"], panel_rect)
        pygame.draw.rect(screen, colors["border"], panel_rect, layout["border_thickness"])
        
        ribbon_x = (config.SCREEN_WIDTH - layout["ribbon_width"]) // 2
        ribbon_y = panel_y - layout["ribbon_offset_y"]
        pygame.draw.rect(screen, colors["ribbon"], (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]))
        pygame.draw.rect(screen, colors["ribbon_border"], (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]), 4)

        def draw_text_with_shadow(surf, text, font, color, center_pos=None, top_left=None):
            shadow_s = font.render(text, False, (0, 0, 0))
            main_s = font.render(text, False, color)
            if center_pos:
                cx, cy = center_pos
                s_rect = shadow_s.get_rect(center=(cx + 2, cy + 2))
                m_rect = main_s.get_rect(center=(cx, cy))
            elif top_left:
                tx, ty = top_left
                s_rect = shadow_s.get_rect(topleft=(tx + 2, ty + 2))
                m_rect = main_s.get_rect(topleft=(tx, ty))
            surf.blit(shadow_s, s_rect)
            surf.blit(main_s, m_rect)

        try:
            title_font = pygame.font.Font(config.FONT_PATH, layout["font_size_title"])
            name_font = pygame.font.Font(config.FONT_PATH, layout["font_size_name"])
            detail_font = pygame.font.Font(config.FONT_PATH, layout["font_size_detail"])
        except FileNotFoundError:
            title_font = pygame.font.SysFont(None, 60)
            name_font = pygame.font.SysFont(None, 40)
            detail_font = pygame.font.SysFont(None, 24)

        draw_text_with_shadow(screen, "LEVEL UP!", title_font, colors["text_title"], 
            center_pos=(config.SCREEN_WIDTH // 2, ribbon_y + layout["ribbon_height"] // 2))
        
        current_y = panel_y + layout["list_start_y"]
        mouse_pos = pygame.mouse.get_pos()

        for i, (weapon_class, w_key) in enumerate(self.upgrade_options):
            item_width = layout["panel_width"] - 80 
            item_rect = pygame.Rect(panel_x + 40, current_y, item_width, layout["item_height"])
            
            is_hovered = item_rect.collidepoint(mouse_pos)
            bg_col = colors["item_bg_hover"] if is_hovered else colors["item_bg_normal"]
            border_col = colors["item_border_hover"] if is_hovered else colors["item_border_normal"]
            
            pygame.draw.rect(screen, bg_col, item_rect)
            pygame.draw.rect(screen, border_col, item_rect, 4 if is_hovered else 2)

            stats = config.WEAPON_STATS.get(w_key, {})
            name_text = stats.get("name", "Unknown Weapon")
            
            icon_size = layout["icon_size"]
            img = load_weapon_image(w_key)
            if img:
                img = pygame.transform.scale(img, (icon_size, icon_size))
                img_rect = img.get_rect(center=(item_rect.left + icon_size//2 + 30, item_rect.centery))
                screen.blit(img, img_rect)
            
            text_x = item_rect.left + icon_size + 60
            draw_text_with_shadow(screen, name_text, name_font, colors["text_body"], top_left=(text_x, item_rect.top + 25))
            
            detail_text = f"Tier: {stats.get('tier', 1)}  Damage: {stats.get('damage', 0)}"
            screen.blit(detail_font.render(detail_text, False, colors["text_detail"]), (text_x, item_rect.top + 80))
            
            current_y += layout["item_height"] + layout["item_gap"]