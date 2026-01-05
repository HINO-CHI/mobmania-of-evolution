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
from src.system.map_generator import MapGenerator

def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)

# ==========================================
# カメラ＆描画管理 (変更なし)
# ==========================================
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.margin = 100 

    def custom_draw(self, player, background_color, decorations):
        self.offset.x = player.rect.centerx - config.SCREEN_WIDTH // 2
        self.offset.y = player.rect.centery - config.SCREEN_HEIGHT // 2

        self.display_surface.fill(background_color)

        camera_rect = pygame.Rect(
            self.offset.x - self.margin, 
            self.offset.y - self.margin, 
            config.SCREEN_WIDTH + self.margin * 2, 
            config.SCREEN_HEIGHT + self.margin * 2
        )

        for sprite in decorations:
            if camera_rect.colliderect(sprite.rect): 
                offset_pos = sprite.rect.topleft - self.offset
                self.display_surface.blit(sprite.image, offset_pos)

        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            if camera_rect.colliderect(sprite.rect): 
                offset_pos = sprite.rect.topleft - self.offset
                
                if sprite != player and sprite.rect.centery > player.rect.centery:
                    if sprite.rect.colliderect(player.rect.inflate(10, 10)):
                        sprite.image.set_alpha(100)
                        self.display_surface.blit(sprite.image, offset_pos)
                        sprite.image.set_alpha(255)
                    else:
                        self.display_surface.blit(sprite.image, offset_pos)
                else:
                    self.display_surface.blit(sprite.image, offset_pos)

# ==========================================
# ゲームプレイ画面
# ==========================================
class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)
        self.game_state = "PLAYING"
        
        self.current_generation = 1
        self.kill_count = 0
        self.level = 0
        self.next_level_kill = 5
        self.upgrade_options = [] 
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []
        self.last_spawn_time = 0
        self.spawn_interval = 800

        self.camera_group = CameraGroup()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()

        # --- マップ生成 (一括生成) ---
        self.map_gen = MapGenerator(self.biome)
        # ★修正: generate() を呼んで一気に作る
        self.obstacles, self.decorations = self.map_gen.generate()
        
        # 障害物は描画グループへ追加
        self.camera_group.add(self.obstacles)
        
        self.bg_color = config.STAGE_SETTINGS.get(self.biome, {}).get("bg_color", (34, 139, 34))

        # プレイヤー配置 (中央)
        center_x = self.map_gen.map_width // 2
        center_y = self.map_gen.map_height // 2
        
        self.player = Player(
            (center_x, center_y), 
            self.camera_group, 
            self.bullets_group,
            self.enemies_group
        )
        self.camera_group.add(self.player)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
                if event.key == pygame.K_l: 
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

        # ★修正: マップの都度更新は不要になったので削除
        
        self.spawn_enemies()
        
        self.camera_group.update(dt)
        self.bullets_group.update(dt)
        
        # 当たり判定処理
        hits_obstacle = pygame.sprite.spritecollide(self.player, self.obstacles, False, collided=collide_hit_rect)
        if hits_obstacle:
            for obs in hits_obstacle:
                dx = self.player.rect.centerx - obs.rect.centerx
                dy = self.player.rect.centery - obs.rect.centery
                if abs(dx) > abs(dy):
                    self.player.pos.x += 10 if dx > 0 else -10
                else:
                    self.player.pos.y += 10 if dy > 0 else -10
                self.player.rect.center = self.player.pos

        hits = pygame.sprite.groupcollide(
            self.bullets_group, self.enemies_group, True, False, collided=collide_hit_rect
        )
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.take_damage(bullet.damage)

        hits_player = pygame.sprite.spritecollide(
            self.player, self.enemies_group, False, collided=collide_hit_rect
        )

        for enemy in self.enemies_group:
            if enemy.stats["hp"] <= 0:
                self.handle_enemy_death(enemy)

        return None
    
    # ... (以下のメソッドは変更なし、そのまま記述してください) ...
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
            self.next_level_kill = current_target * 2 if current_target < 160 else current_target + 160
            self.start_level_up_sequence()

    def start_level_up_sequence(self):
        self.level += 1
        self.game_state = "LEVEL_UP"
        print(f"=== LEVEL UP! Lv.{self.level} ===")
        
        target_tier = 2 if self.level >= 2 else 1
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
        camera_x = self.player.rect.centerx - config.SCREEN_WIDTH // 2
        camera_y = self.player.rect.centery - config.SCREEN_HEIGHT // 2
        
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH) + camera_x, camera_y - 50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH) + camera_x, camera_y + config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (camera_x - 50, random.randint(0, config.SCREEN_HEIGHT) + camera_y)
        elif edge == 'right':
            return (camera_x + config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT) + camera_y)
        return (camera_x, camera_y)

    def draw(self, screen):
        self.camera_group.custom_draw(self.player, self.bg_color, self.decorations)
        self.draw_ui(screen)
        if self.game_state == "LEVEL_UP":
            self.draw_level_up_screen(screen)

    def draw_ui(self, screen):
        font = pygame.font.SysFont(None, 24)
        info_text = f"Lv: {self.level} | Kills: {self.kill_count} / {self.next_level_kill}"
        text_surf = font.render(info_text, True, config.WHITE)
        screen.blit(text_surf, (10, 10))

    def draw_level_up_screen(self, screen):
        # 既存コード（省略なし）
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

        try:
            title_font = pygame.font.Font(config.FONT_PATH, layout["font_size_title"])
            name_font = pygame.font.Font(config.FONT_PATH, layout["font_size_name"])
            detail_font = pygame.font.Font(config.FONT_PATH, layout["font_size_detail"])
        except FileNotFoundError:
            title_font = pygame.font.SysFont(None, 60)
            name_font = pygame.font.SysFont(None, 40)
            detail_font = pygame.font.SysFont(None, 24)

        def draw_text_with_shadow(surf, text, font, color, center_pos=None, top_left=None):
            shadow_s = font.render(text, False, (0, 0, 0))
            main_s = font.render(text, False, color)
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

        draw_text_with_shadow(screen, "Make Your Choice!", title_font, colors["text_title"], 
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

            stats = config.WEAPON_STATS.get(w_key)
            name_text = stats["name"]
            
            icon_size = layout["icon_size"]
            img = load_weapon_image(w_key)
            if img:
                img = pygame.transform.scale(img, (icon_size, icon_size))
                img_rect = img.get_rect(center=(item_rect.left + icon_size//2 + 30, item_rect.centery))
                shadow_img = img.copy()
                shadow_img.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(shadow_img, (img_rect.x + 3, img_rect.y + 3))
                screen.blit(img, img_rect)
            
            text_x = item_rect.left + icon_size + 60
            draw_text_with_shadow(screen, name_text, name_font, colors["text_body"], top_left=(text_x, item_rect.top + 25))
            
            detail_text = f"Tier: {stats.get('tier', 1)}  Dmg: {stats.get('damage', 0)}"
            screen.blit(detail_font.render(detail_text, False, colors["text_detail"]), (text_x, item_rect.top + 80))
            
            current_y += layout["item_height"] + layout["item_gap"]