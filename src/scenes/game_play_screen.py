import pygame
import random
import time
import config
import math

from src.entities.player import Player
# ★変更: Bossクラスをインポート
from src.entities.enemy import Enemy, Boss
from src.entities.weapons import (
    PencilGun, BreadShield, BearSmash, WoodenStick,
    ThunderStaff, IceCream, GigaDrill,
    load_weapon_image
)
from src.entities.items import (
    ExpBlue, ExpYellow, ExpPurple, 
    HealingItem, Candy, Chocolate, ChortCake
)

from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager
from src.system.map_generator import MapGenerator
from src.scenes.game_play import CameraGroup
from src.scenes.game_play import FloatingText
from src.entities.grave import GraveFlower

AGGRO_PHRASES = ["Ouch!", "Hey!", "Stop it!", "No!", "Why!", "It hurts!", "Watch out!"]

def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)
        self.game_state = "PLAYING"
        
        self.current_generation = 1
        
        self.current_exp = 0
        self.level_exp_curve = [100, 200, 400, 800, 1600, 3200, 6400]
        self.level = 1 
        self.next_level_exp = self.level_exp_curve[0]
        
        self.kill_count = 0
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []
        self.last_spawn_time = 0
        self.spawn_interval = 800
        self.last_damage_time = 0

        # ★追加: ゲーム開始時刻とボス管理
        self.start_time = pygame.time.get_ticks()
        self.active_boss = None
        self.spawned_boss_minutes = set() # すでに出現させた時間を記録

        # ★追加: ボスの出現スケジュール (分: (ファイル名, 名前, HP, 攻撃力, サイズ))
        self.boss_schedule = {
            1: ("mini_boss_big_tree.png", "Big Tree", 500, 10, (120, 120)),
            2: ("mini_boss_kinoko.png", "Giant Kinoko", 800, 12, (100, 100)),
            3: ("mini_boss_turtle.png", "Iron Turtle", 1500, 15, (130, 100)),
            4: ("mini_boss_kinoko_derk.png", "Dark Kinoko", 2000, 18, (110, 110)),
            5: ("mini_boss_cobra.png", "King Cobra", 3000, 25, (150, 150)),
            6: ("boss_golem.png", "ANCIENT GOLEM", 10000, 40, (200, 200)) # ラスボス
        }

        self.camera_group = CameraGroup()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.decorations = pygame.sprite.Group()
        self.items_group = pygame.sprite.Group()

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

        # ★追加: 時間経過によるボス出現チェック
        self.check_boss_spawn()

        self.map_gen.update(self.player.pos)
        self.camera_group.add(self.obstacles.sprites())
        self.spawn_enemies()
        
        self.camera_group.update(dt)
        self.items_group.update(dt, self.player.rect.center)

        # アイテム回収
        hits_items = pygame.sprite.spritecollide(self.player, self.items_group, True, collided=collide_hit_rect)
        for item in hits_items:
            if isinstance(item, HealingItem):
                recover = item.value
                if self.player.hp < self.player.max_hp:
                    self.player.hp = min(self.player.hp + recover, self.player.max_hp)
                    heal_text = FloatingText(self.player.rect.center, f"+{recover}", (0, 255, 0))
                    self.camera_group.add(heal_text)
            elif hasattr(item, 'value'):
                self.current_exp += item.value
                self.check_level_up()
        
        # 障害物
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
                dmg_text = FloatingText(enemy.rect.center, str(bullet.damage), (255, 255, 0))
                self.camera_group.add(dmg_text)

        # 敵 vs プレイヤー
        current_time = pygame.time.get_ticks()
        hits_player = pygame.sprite.spritecollide(self.player, self.enemies_group, False, collided=collide_hit_rect)
        if hits_player:
            if current_time - self.last_damage_time > 500:
                damage = 10
                # ボスならダメージ増やすなどの調整も可能
                self.player.take_damage(damage)
                self.last_damage_time = current_time
                
                dmg_pos = (self.player.rect.centerx + random.randint(-10, 10), self.player.rect.top)
                dmg_text = FloatingText(dmg_pos, f"-{damage}", (255, 0, 0))
                self.camera_group.add(dmg_text)
                
                phrase = random.choice(AGGRO_PHRASES)
                floating_text = FloatingText((self.player.rect.centerx, self.player.rect.top - 40), phrase)
                self.camera_group.add(floating_text)

                if self.player.hp <= 0:
                    self.game_state = "GAME_OVER"
                    return "GAME_OVER"

        for enemy in self.enemies_group:
            if enemy.stats["hp"] <= 0:
                self.handle_enemy_death(enemy)
        
        if self.game_state == "GAME_OVER":
            return "GAME_OVER"

        return None

    def check_boss_spawn(self):
        elapsed_ms = pygame.time.get_ticks() - self.start_time
        current_minute = elapsed_ms // 60000  # ミリ秒 -> 分
        
        # スケジュールにあり、かつ まだ出現させていない場合
        if current_minute in self.boss_schedule and current_minute not in self.spawned_boss_minutes:
            data = self.boss_schedule[current_minute]
            filename, name, hp, dmg, size = data
            
            print(f"!!! SPAWNING BOSS: {name} at {current_minute} min !!!")
            
            # ★変更: プレイヤーの頭上 200px の位置に出現（確実に見える位置）
            px, py = self.player.rect.center
            spawn_pos = (px - random.randint(-500, 500), py - random.randint(-500, 500))
            
            boss = Boss(
                pos=spawn_pos, 
                player=self.player, 
                groups=[self.camera_group, self.enemies_group],
                filename=filename,
                boss_name=name,
                hp=hp,
                damage=dmg,
                scale_size=size
            )
            
            self.active_boss = boss
            self.spawned_boss_minutes.add(current_minute)
            
            # 警告テキスト表示
            warning_text = FloatingText((px, py - 50), f"WARNING: {name}!!", (255, 0, 0), duration=3000)
            self.camera_group.add(warning_text)
            
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "TITLE"
                if event.key == pygame.K_l: 
                    self.current_exp += self.next_level_exp
                    self.check_level_up()
                if event.key == pygame.K_h:
                    self.camera_group.debug_mode = not self.camera_group.debug_mode
                # ★デバッグ用: Tキーで時間を1分進める（ボス呼び出しテスト）
                if event.key == pygame.K_t:
                    self.start_time -= 60000
                    print("Debug: Time skipped +1 min")

                if event.key == pygame.K_b:
                    print("Debug: Force Spawning Boss!")
                    # Big Tree のデータを強制的に使う
                    filename = "mini_boss_big_tree.png"
                    name = "Debug Boss"
                    hp = 500
                    dmg = 10
                    size = (120, 120)
                    
                    px, py = self.player.rect.center
                    spawn_pos = (px, py) # 頭上
                    
                    boss = Boss(
                        pos=spawn_pos,
                        player=self.player,
                        groups=[self.camera_group, self.enemies_group],
                        filename=filename,
                        boss_name=name,
                        hp=hp,
                        damage=dmg,
                        scale_size=size
                    )
                    self.active_boss = boss
                    warning_text = FloatingText((px, py - 50), "DEBUG BOSS!!", (255, 0, 0), duration=2000)
                    self.camera_group.add(warning_text)

                # ★追加: Tキーで時間を進める（既存のまま）
                if event.key == pygame.K_t:
                    self.start_time -= 60000
                    print("Debug: Time skipped +1 min")

            if self.game_state == "LEVEL_UP":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: self.handle_levelup_click(event.pos)

    def handle_enemy_death(self, enemy):
        enemy.death_time = time.time()
        self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
        
        # ==========================================================
        # ボス撃破時の処理
        # ==========================================================
        if enemy == self.active_boss:
            self.active_boss = None 
            
            # 1. 中心にメインの花を咲かせる
            # camera_groupに入れることで描画され、decorationsに入れることで背景物として管理
            GraveFlower(enemy.rect.center, [self.camera_group, self.decorations], "grave_flower_main.png")
            
            # 2. 周囲にサブの花を円形に咲かせる
            sub_flowers = ["grave_flower_orange.png", "grave_flower_blue.png", "grave_flower_yellow.png"]
            
            # 花の数（10〜15個くらい）
            flower_count = random.randint(40, 60)
            
            for i in range(flower_count):
                # 角度を計算 (0 〜 360度)
                angle = (360 / flower_count) * i
                # ランダム性を加えて自然なバラつきを出す
                angle += random.uniform(-15, 15)
                
                # 半径 (中心から 40px 〜 70px 離れた位置)
                distance = random.uniform(100, 300)
                
                # 座標計算 (三角関数)
                rad = math.radians(angle)
                offset_x = math.cos(rad) * distance
                offset_y = math.sin(rad) * distance
                
                flower_pos = (enemy.rect.centerx + offset_x, enemy.rect.centery + offset_y)
                
                # 色をランダムに選択
                color_img = random.choice(sub_flowers)
                GraveFlower(flower_pos, [self.camera_group, self.decorations], color_img)

            # 3. 経験値ジェム (花畑の上に散らばるように)
            for _ in range(5):
                # 花と同じように少し散らして配置
                scatter_pos = (
                    enemy.rect.centerx + random.randint(-50, 50),
                    enemy.rect.centery + random.randint(-50, 50)
                )
                ExpPurple(scatter_pos, groups=[self.camera_group, self.items_group])

            print("BOSS DEFEATED! Flower garden created.")
        
        else:
            # --- 通常モブのドロップ (変更なし) ---
            drop_count = random.randint(1, 2)
            for _ in range(drop_count):
                ExpBlue(enemy.rect.center, groups=[self.camera_group, self.items_group])

            max_hp = enemy.stats.get("max_hp", enemy.stats.get("hp", 10))
            if max_hp >= 50:
                ExpYellow(enemy.rect.center, groups=[self.camera_group, self.items_group])
                
            if random.random() < 0.01:
                ExpPurple(enemy.rect.center, groups=[self.camera_group, self.items_group])

            if random.random() < 0.05:
                r = random.random()
                if r < 0.6: Candy(enemy.rect.center, groups=[self.camera_group, self.items_group])
                elif r < 0.9: Chocolate(enemy.rect.center, groups=[self.camera_group, self.items_group])
                else: ChortCake(enemy.rect.center, groups=[self.camera_group, self.items_group])

        enemy.kill()
        self.mobs_killed_in_wave += 1
        self.kill_count += 1
        if self.mobs_killed_in_wave >= self.wave_threshold: self.start_next_wave()

    def check_level_up(self):
        if self.current_exp >= self.next_level_exp:
            while self.current_exp >= self.next_level_exp:
                self.current_exp -= self.next_level_exp
                if self.level < len(self.level_exp_curve):
                    self.next_level_exp = self.level_exp_curve[self.level]
                else:
                    self.next_level_exp = self.level_exp_curve[-1]
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
        self.camera_group.custom_draw(self.player, self.bg_color, self.decorations)
        self.draw_player_health_bar(screen)
        
        # ★追加: ボスHPバー表示
        if self.active_boss and self.active_boss.alive():
            self.draw_boss_health_bar(screen)

        self.draw_ui(screen)
        if self.game_state == "LEVEL_UP":
            self.draw_level_up_screen(screen)

    # ★追加: ボスHPバー描画メソッド
    def draw_boss_health_bar(self, screen):
        boss = self.active_boss
        hp = max(0, boss.stats["hp"])
        max_hp = boss.stats.get("max_hp", hp)
        ratio = hp / max_hp if max_hp > 0 else 0
        
        bar_w = 600
        bar_h = 25
        x = (config.SCREEN_WIDTH - bar_w) // 2
        y = 50 # 画面上部
        
        # 背景
        pygame.draw.rect(screen, (0, 0, 0), (x, y, bar_w, bar_h))
        # HP (赤)
        pygame.draw.rect(screen, (180, 0, 0), (x, y, bar_w * ratio, bar_h))
        # 枠
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_w, bar_h), 3)
        
        # 名前表示
        name_surf = self.ui_font_bold.render(boss.stats.get("name", "BOSS"), True, (255, 255, 255))
        name_rect = name_surf.get_rect(midbottom=(config.SCREEN_WIDTH // 2, y - 5))
        # 影
        shadow_surf = self.ui_font_bold.render(boss.stats.get("name", "BOSS"), True, (0, 0, 0))
        screen.blit(shadow_surf, (name_rect.x+2, name_rect.y+2))
        screen.blit(name_surf, name_rect)

    def draw_player_health_bar(self, screen):
        if self.player.hp <= 0: return
        offset = getattr(self.camera_group, 'offset', pygame.math.Vector2(0, 0))
        screen_center = self.player.rect.center - offset
        
        bar_width = 70
        bar_height = 10
        draw_x = screen_center.x - bar_width // 2
        draw_y = screen_center.y + 45 
        
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        
        pygame.draw.rect(screen, (0, 0, 0), (draw_x, draw_y, bar_width, bar_height))
        color = (0, 255, 0) if hp_ratio > 0.3 else (255, 0, 0)
        pygame.draw.rect(screen, color, (draw_x, draw_y, bar_width * hp_ratio, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (draw_x, draw_y, bar_width, bar_height), 1)

    def draw_ui(self, screen):
        xp_ratio = min(1.0, self.current_exp / self.next_level_exp) if self.next_level_exp > 0 else 0
        
        bar_h = config.UI_XP_BAR_HEIGHT 
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

        level_text = self.ui_font_large.render(f"LV {self.level}", True, config.WHITE)
        level_shadow = self.ui_font_large.render(f"LV {self.level}", True, config.BLACK)
        lvl_x = config.SCREEN_WIDTH - level_text.get_width() - 20
        lvl_y = 20
        screen.blit(level_shadow, (lvl_x + 2, lvl_y + 2))
        screen.blit(level_text, (lvl_x, lvl_y))
        
        # 時間表示 (オプション)
        elapsed_sec = (pygame.time.get_ticks() - self.start_time) // 1000
        mins = elapsed_sec // 60
        secs = elapsed_sec % 60
        time_str = f"{mins:02}:{secs:02}"
        time_surf = self.ui_font_large.render(time_str, True, (255, 255, 255))
        screen.blit(time_surf, (config.SCREEN_WIDTH // 2 - time_surf.get_width() // 2, 20))
        
        self.draw_weapon_slots(screen)

    def draw_weapon_slots(self, screen):
        icon_size = 60
        padding = 4
        start_x = 0
        start_y = 0
        
        weapons = getattr(self.player, "weapons", [])

        for i, weapon in enumerate(weapons):
            x = start_x + (icon_size + padding) * i
            y = start_y
            
            slot_rect = pygame.Rect(x, y, icon_size, icon_size)
            s = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128))
            screen.blit(s, (x, y))
            pygame.draw.rect(screen, (200, 200, 200), slot_rect, 1)

            try:
                img = None
                if hasattr(weapon, "image") and weapon.image:
                    img = weapon.image
                
                if img:
                    img = pygame.transform.scale(img, (icon_size - 4, icon_size - 4))
                    screen.blit(img, (x + 2, y + 2))
                else:
                    name = getattr(weapon, "name", "?")
                    text_surf = self.ui_font_bold.render(name[:1], True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=(x + icon_size//2, y + icon_size//2))
                    screen.blit(text_surf, text_rect)

            except Exception as e:
                print(f"Icon draw error: {e}")

            lvl = getattr(weapon, "level", 1)
            lvl_surf = self.ui_font.render(str(lvl), True, (255, 255, 0))
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
            
            detail_text = f"Tier: {stats.get('tier', 1)}  Damage: {stats.get('damage', 0)}"
            screen.blit(detail_font.render(detail_text, False, colors["text_detail"]), (text_x, item_rect.top + 80))
            
            current_y += layout["item_height"] + layout["item_gap"]