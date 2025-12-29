# src/scenes/game_play.py
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

def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)

        self.current_generation = 1
        
        # --- レベルアップ管理用 ---
        self.kill_count = 0
        self.level = 0
        self.next_level_kill = 5
        
        # ゲームの状態管理
        self.game_state = "PLAYING"
        self.upgrade_options = [] 

        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []

        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()

        self.player = Player(
            (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), 
            self.all_sprites, 
            self.bullets_group,
            self.enemies_group
        )
        self.all_sprites.add(self.player)
        
        self.bg_color = config.BG_COLOR
        if self.biome == "grass": self.bg_color = (34, 139, 34)
        elif self.biome == "water": self.bg_color = (30, 144, 255)
        elif self.biome == "volcano": self.bg_color = (139, 0, 0)
        elif self.biome == "cloud": self.bg_color = (200, 200, 255)

        self.last_spawn_time = 0
        self.spawn_interval = 800

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
                if event.key == pygame.K_l: # デバッグ用
                    self.kill_count += self.next_level_kill
                    self.check_level_up()

            if self.game_state == "LEVEL_UP":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_levelup_click(event.pos)

        return None

    def update(self, dt):
        if self.game_state == "LEVEL_UP":
            return None

        self.spawn_enemies()
        self.all_sprites.update(dt)
        
        # 1. 弾の当たり判定
        hits = pygame.sprite.groupcollide(
            self.bullets_group, 
            self.enemies_group, 
            True, False, collided=collide_hit_rect
        )
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.take_damage(bullet.damage)

        # 2. プレイヤーの当たり判定
        hits_player = pygame.sprite.spritecollide(
            self.player, self.enemies_group, False, collided=collide_hit_rect
        )

        # 3. 死んだ敵の処理
        for enemy in self.enemies_group:
            if enemy.stats["hp"] <= 0:
                self.handle_enemy_death(enemy)

        return None
    
    def handle_enemy_death(self, enemy):
        enemy.death_time = time.time()
        self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
        enemy.kill()
        
        self.mobs_killed_in_wave += 1
        self.kill_count += 1
        
        if self.mobs_killed_in_wave >= self.wave_threshold:
            self.start_next_wave()
            
        self.check_level_up()

    def check_level_up(self):
        if self.kill_count >= self.next_level_kill:
            current_target = self.next_level_kill
            if current_target < 160:
                self.next_level_kill = current_target * 2
            else:
                self.next_level_kill = current_target + 160
            
            self.start_level_up_sequence()

    def start_level_up_sequence(self):
        self.level += 1
        self.game_state = "LEVEL_UP"
        print(f"=== LEVEL UP! Lv.{self.level} ===")
        
        # Tier決定
        target_tier = 1
        if self.level == 1:
            target_tier = 1 
        elif self.level >= 2:
            target_tier = 2 
            
        # 候補リスト作成
        weapon_pool = []
        if target_tier == 1:
            weapon_pool = [
                (PencilGun, "pencil"),
                (BreadShield, "bread"),
                (BearSmash, "bear")
            ]
        elif target_tier == 2:
            weapon_pool = [
                (ThunderStaff, "thunder"),
                (IceCream, "ice"),
                (GigaDrill, "drill")
            ]

        # 重複なしで3つ選ぶ
        count = min(len(weapon_pool), 3)
        self.upgrade_options = random.sample(weapon_pool, count)

    def handle_levelup_click(self, mouse_pos):
        # configからレイアウト情報を取得
        layout = config.LEVELUP_SCREEN
        
        # パネル位置計算
        panel_x = (config.SCREEN_WIDTH - layout["panel_width"]) // 2
        panel_y = (config.SCREEN_HEIGHT - layout["panel_height"]) // 2
        
        # リスト開始位置
        current_y = panel_y + layout["list_start_y"]
        
        for i, (weapon_class, w_key) in enumerate(self.upgrade_options):
            # 判定エリア計算
            # 横幅はパネル幅から左右のマージン(仮に40px)を引いたもの
            item_width = layout["panel_width"] - 80 
            item_rect = pygame.Rect(
                panel_x + 40, 
                current_y, 
                item_width, 
                layout["item_height"]
            )
            
            if item_rect.collidepoint(mouse_pos):
                self.player.add_weapon(weapon_class)
                self.game_state = "PLAYING"
                print(f"Selected: {weapon_class.__name__}")
                break
            
            # 次のアイテムのY座標へ
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
            stats_to_use = None
            if self.pending_stats_queue:
                stats_to_use = self.pending_stats_queue.pop(0)
            enemy = Enemy(spawn_pos, self.player, self.enemies_group, stats=stats_to_use)
            self.all_sprites.add(enemy)
            self.enemies_group.add(enemy)
            self.last_spawn_time = current_time

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)
        
        font = pygame.font.SysFont(None, 24)
        info_text = f"Lv: {self.level} | Kills: {self.kill_count} / {self.next_level_kill}"
        text_surf = font.render(info_text, True, config.WHITE)
        screen.blit(text_surf, (10, 10))
        
        if self.game_state == "LEVEL_UP":
            self.draw_level_up_screen(screen)

    def draw_level_up_screen(self, screen):
        # 1. 暗転背景
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # --- config読み込み ---
        layout = config.LEVELUP_SCREEN
        colors = config.UI_COLORS
        
        # パネル位置計算
        panel_x = (config.SCREEN_WIDTH - layout["panel_width"]) // 2
        panel_y = (config.SCREEN_HEIGHT - layout["panel_height"]) // 2
        
        # 2. メインパネル描画
        panel_rect = pygame.Rect(panel_x, panel_y, layout["panel_width"], layout["panel_height"])
        pygame.draw.rect(screen, colors["bg"], panel_rect)
        pygame.draw.rect(screen, colors["border"], panel_rect, layout["border_thickness"])
        
        # 3. リボン描画
        ribbon_x = (config.SCREEN_WIDTH - layout["ribbon_width"]) // 2
        ribbon_y = panel_y - layout["ribbon_offset_y"]
        
        pygame.draw.rect(screen, colors["ribbon"], 
                         (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]))
        pygame.draw.rect(screen, colors["ribbon_border"], 
                         (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]), 4)

        # フォント準備
        try:
            title_font = pygame.font.Font(config.FONT_PATH, layout["font_size_title"])
            name_font = pygame.font.Font(config.FONT_PATH, layout["font_size_name"])
            detail_font = pygame.font.Font(config.FONT_PATH, layout["font_size_detail"])
        except FileNotFoundError:
            title_font = pygame.font.SysFont(None, 60)
            name_font = pygame.font.SysFont(None, 40)
            detail_font = pygame.font.SysFont(None, 24)

       # ヘルパー関数: 影付き文字 (修正ポイント1)
        def draw_text_with_shadow(surf, text, font, color, center_pos=None, top_left=None):
            # ドット感を出すため antialias=False
            shadow_s = font.render(text, False, (0, 0, 0))
            main_s = font.render(text, False, color)
            
            # ★修正: 影の距離を +3 から +1 に変更してタイトに
            offset = 1
            
            if center_pos:
                cx, cy = center_pos
                s_rect = shadow_s.get_rect(center=(cx + offset, cy + offset))
                m_rect = main_s.get_rect(center=(cx, cy))
            elif top_left:
                tx, ty = top_left
                s_rect = shadow_s.get_rect(topleft=(tx + offset, ty + offset))
                m_rect = main_s.get_rect(topleft=(tx, ty))
            
            surf.blit(shadow_s, s_rect)
            surf.blit(main_s, m_rect)

        # タイトル描画
        draw_text_with_shadow(
            screen, "Make Your Choice!", title_font, colors["text_title"], 
            center_pos=(config.SCREEN_WIDTH // 2, ribbon_y + layout["ribbon_height"] // 2)
        )
        
        # 4. 選択肢リスト描画
        current_y = panel_y + layout["list_start_y"]
        mouse_pos = pygame.mouse.get_pos()

        for i, (weapon_class, w_key) in enumerate(self.upgrade_options):
            # アイテムエリア計算
            item_width = layout["panel_width"] - 80
            item_rect = pygame.Rect(panel_x + 40, current_y, item_width, layout["item_height"])
            
            is_hovered = item_rect.collidepoint(mouse_pos)
            
            # 背景と枠線
            bg_col = colors["item_bg_hover"] if is_hovered else colors["item_bg_normal"]
            border_col = colors["item_border_hover"] if is_hovered else colors["item_border_normal"]
            border_width = 4 if is_hovered else 2
            
            pygame.draw.rect(screen, bg_col, item_rect)
            pygame.draw.rect(screen, border_col, item_rect, border_width)

            # --- 情報取得 ---
            stats = config.WEAPON_STATS.get(w_key)
            name_text = stats["name"]
            
            # --- 画像描画 (修正ポイント2) ---
            icon_size = layout["icon_size"]
            icon_center_x = item_rect.left + icon_size // 2 + 30
            icon_center_y = item_rect.centery
            
            img = load_weapon_image(w_key)
            if img:
                img = pygame.transform.scale(img, (icon_size, icon_size))
                img_rect = img.get_rect(center=(icon_center_x, icon_center_y))
                
                # 画像の影
                shadow_img = img.copy()
                shadow_img.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
                # ★修正: 影の距離を +6 から +3 に変更
                screen.blit(shadow_img, (img_rect.x + 3, img_rect.y + 3))
                screen.blit(img, img_rect)
            
            # --- テキスト描画 ---
            text_x = item_rect.left + icon_size + 60
            
            # 武器名
            draw_text_with_shadow(
                screen, name_text, name_font, colors["text_body"], 
                top_left=(text_x, item_rect.top + 25)
            )
            
            # 詳細情報
            tier = stats.get('tier', 1)
            dmg = stats.get('damage', 0)
            detail_text = f"Tier: {tier}  Damage: {dmg}"
            cd = stats.get('cooldown', 0)
            if cd > 0:
                detail_text += f"  CD: {cd/1000}s"
            
            # アンチエイリアスOFFで描画(ここは影なしでOK)
            detail_surf = detail_font.render(detail_text, False, colors["text_detail"])
            screen.blit(detail_surf, (text_x, item_rect.top + 80))
            
            # ホバー時のCLICK演出
            if is_hovered:
                click_txt = detail_font.render("<<< CLICK TO SELECT", False, config.RED)
                screen.blit(click_txt, (item_rect.right - 250, item_rect.bottom - 40))
            
            # 次のアイテム位置へ更新
            current_y += layout["item_height"] + layout["item_gap"]

    # ★これが抜けていました！
    def get_random_spawn_pos(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH), -50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (-50, random.randint(0, config.SCREEN_HEIGHT))
        elif edge == 'right':
            return (config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT))