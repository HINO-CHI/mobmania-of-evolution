# src/scenes/game_play.py
import pygame
import random
import time
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
# 武器クラスをすべてインポート
from src.entities.weapons import (
    PencilGun, BreadShield, BearSmash, WoodenStick,
    ThunderStaff, IceCream, GigaDrill,
    load_weapon_image
)
from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager
from src.system.map_generator import MapGenerator

# 矩形の当たり判定関数
def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)

# ==========================================
# カメラ＆描画管理クラス
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
        
        # 画面内判定用Rect
        camera_rect = pygame.Rect(
            self.offset.x - self.margin, 
            self.offset.y - self.margin, 
            config.SCREEN_WIDTH + self.margin * 2, 
            config.SCREEN_HEIGHT + self.margin * 2
        )

        # 装飾（草など）
        for sprite in decorations:
            if camera_rect.colliderect(sprite.rect): 
                offset_pos = sprite.rect.topleft - self.offset
                self.display_surface.blit(sprite.image, offset_pos)

        # 障害物・キャラ（Y座標順で描画して奥行き表現）
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            if camera_rect.colliderect(sprite.rect): 
                offset_pos = sprite.rect.topleft - self.offset
                # プレイヤーの手前にある背の高い物体は半透明にする
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
# ゲームプレイ画面クラス
# ==========================================
class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)
        self.game_state = "PLAYING"
        
        # --- ゲーム進行パラメータ ---
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

        # --- グループ ---
        self.camera_group = CameraGroup()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        
        # マップ用グループ
        self.obstacles = pygame.sprite.Group()
        self.decorations = pygame.sprite.Group()

        # --- マップ生成 ---
        self.map_gen = MapGenerator(self.biome)
        self.map_gen.setup(self.obstacles, self.decorations)
        
        self.bg_color = config.STAGE_SETTINGS.get(self.biome, {}).get("bg_color", (34, 139, 34))

        # プレイヤー配置
        self.player = Player((0, 0), self.camera_group, self.bullets_group, self.enemies_group)
        self.camera_group.add(self.player)
        
        # 初期マップ生成
        self.map_gen.update(self.player.pos)
        self.camera_group.add(self.obstacles.sprites())
        
        # デバッグ用
        self.debug_timer = 0

    def update(self, dt):
        if self.game_state == "LEVEL_UP": return

        self.map_gen.update(self.player.pos)
        self.camera_group.add(self.obstacles.sprites())
        self.spawn_enemies()
        
        self.camera_group.update(dt)
        
        # --- ★修正: 障害物との衝突処理 ---
        # 画像(rect)ではなく、当たり判定(hitbox)の中心を使って正しく押し出す
        hits_obstacle = pygame.sprite.spritecollide(self.player, self.obstacles, False, collided=collide_hit_rect)
        if hits_obstacle:
            for obs in hits_obstacle:
                # 相手がhitboxを持っていればそれを、なければrectを使う
                obs_rect = getattr(obs, 'hitbox', obs.rect)
                player_rect = self.player.hitbox
                
                # 中心座標の差分を計算 (これが一番重要！)
                dx = player_rect.centerx - obs_rect.centerx
                dy = player_rect.centery - obs_rect.centery
                
                # 横方向のズレの方が大きいなら、横に押し出す
                if abs(dx) > abs(dy):
                    if dx > 0: # プレイヤーが右にいる -> 右へ
                        self.player.pos.x += 5
                    else:      # プレイヤーが左にいる -> 左へ
                        self.player.pos.x -= 5
                # 縦方向のズレの方が大きいなら、縦に押し出す
                else:
                    if dy > 0: # プレイヤーが下にいる -> 下へ
                        self.player.pos.y += 5
                    else:      # プレイヤーが上にいる -> 上へ
                        self.player.pos.y -= 5
                
                # 座標を反映してHitboxを更新
                self.player.hitbox.center = (round(self.player.pos.x), round(self.player.pos.y))
                self.player.rect.center = self.player.hitbox.center

        # 弾 vs 敵
        hits = pygame.sprite.groupcollide(self.bullets_group, self.enemies_group, True, False, collided=collide_hit_rect)
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.take_damage(bullet.damage)

        # 敵の死亡チェック
        for enemy in self.enemies_group:
            if enemy.stats["hp"] <= 0:
                self.handle_enemy_death(enemy)

    def handle_events(self, events):
        for event in events:
            # 共通キー操作
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
                # デバッグ用: Lキーで強制レベルアップ
                if event.key == pygame.K_l: 
                    self.kill_count += self.next_level_kill
                    self.check_level_up()

            # レベルアップ画面でのクリック操作
            if self.game_state == "LEVEL_UP":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # 左クリック
                        self.handle_levelup_click(event.pos)
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
            # 必要キル数を更新
            current_target = self.next_level_kill
            self.next_level_kill = current_target * 2 if current_target < 160 else current_target + 160
            self.start_level_up_sequence()

    def start_level_up_sequence(self):
        self.level += 1
        self.game_state = "LEVEL_UP"
        print(f"=== LEVEL UP! Lv.{self.level} ===")
        
        # レベルに応じて武器プールを切り替える
        target_tier = 2 if self.level >= 2 else 1
        weapon_pool = []
        
        if target_tier == 1:
            weapon_pool = [(PencilGun, "pencil"), (BreadShield, "bread"), (BearSmash, "bear")]
        else:
            weapon_pool = [(ThunderStaff, "thunder"), (IceCream, "ice"), (GigaDrill, "drill")]
            
        # ランダムに3つ選出
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
            
            # 選択されたら武器を追加してゲーム再開
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
        # 画面外の少し遠くからスポーンさせる
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
        # メイン描画
        self.camera_group.custom_draw(self.player, self.bg_color, self.decorations)
        
        # UI描画
        self.draw_ui(screen)
        
        # レベルアップ画面描画
        if self.game_state == "LEVEL_UP":
            self.draw_level_up_screen(screen)

    def draw_ui(self, screen):
        font = pygame.font.SysFont(None, 24)
        info_text = f"Lv: {self.level} | Kills: {self.kill_count} / {self.next_level_kill}"
        text_surf = font.render(info_text, True, config.WHITE)
        # 影をつけて見やすく
        shadow_surf = font.render(info_text, True, config.BLACK)
        screen.blit(shadow_surf, (12, 12))
        screen.blit(text_surf, (10, 10))

    def draw_level_up_screen(self, screen):
        # ★ここが重要: 完全に記述した描画ロジック
        
        # 1. 半透明の黒背景
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        layout = config.LEVELUP_SCREEN
        colors = config.UI_COLORS
        
        # パネル位置計算
        panel_x = (config.SCREEN_WIDTH - layout["panel_width"]) // 2
        panel_y = (config.SCREEN_HEIGHT - layout["panel_height"]) // 2
        
        # 2. メインパネル
        panel_rect = pygame.Rect(panel_x, panel_y, layout["panel_width"], layout["panel_height"])
        pygame.draw.rect(screen, colors["bg"], panel_rect)
        pygame.draw.rect(screen, colors["border"], panel_rect, layout["border_thickness"])
        
        # 3. リボン（タイトル背景）
        ribbon_x = (config.SCREEN_WIDTH - layout["ribbon_width"]) // 2
        ribbon_y = panel_y - layout["ribbon_offset_y"]
        pygame.draw.rect(screen, colors["ribbon"], (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]))
        pygame.draw.rect(screen, colors["ribbon_border"], (ribbon_x, ribbon_y, layout["ribbon_width"], layout["ribbon_height"]), 4)

        # フォント読み込み
        try:
            title_font = pygame.font.Font(config.FONT_PATH, layout["font_size_title"])
            name_font = pygame.font.Font(config.FONT_PATH, layout["font_size_name"])
            detail_font = pygame.font.Font(config.FONT_PATH, layout["font_size_detail"])
        except FileNotFoundError:
            title_font = pygame.font.SysFont(None, 60)
            name_font = pygame.font.SysFont(None, 40)
            detail_font = pygame.font.SysFont(None, 24)

        # テキスト描画ヘルパー
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

        # 4. タイトル
        draw_text_with_shadow(screen, "LEVEL UP!", title_font, colors["text_title"], 
            center_pos=(config.SCREEN_WIDTH // 2, ribbon_y + layout["ribbon_height"] // 2))
        
        # 5. 選択肢リスト
        current_y = panel_y + layout["list_start_y"]
        mouse_pos = pygame.mouse.get_pos()

        for i, (weapon_class, w_key) in enumerate(self.upgrade_options):
            item_width = layout["panel_width"] - 80
            item_rect = pygame.Rect(panel_x + 40, current_y, item_width, layout["item_height"])
            
            # ホバー判定
            is_hovered = item_rect.collidepoint(mouse_pos)
            bg_col = colors["item_bg_hover"] if is_hovered else colors["item_bg_normal"]
            border_col = colors["item_border_hover"] if is_hovered else colors["item_border_normal"]
            
            # カード背景
            pygame.draw.rect(screen, bg_col, item_rect)
            pygame.draw.rect(screen, border_col, item_rect, 4 if is_hovered else 2)

            # アイテム情報取得
            stats = config.WEAPON_STATS.get(w_key, {})
            name_text = stats.get("name", "Unknown Weapon")
            
            # アイコン
            icon_size = layout["icon_size"]
            img = load_weapon_image(w_key) # weapons.pyからインポートした関数
            if img:
                img = pygame.transform.scale(img, (icon_size, icon_size))
                img_rect = img.get_rect(center=(item_rect.left + icon_size//2 + 30, item_rect.centery))
                screen.blit(img, img_rect)
            
            # 武器名
            text_x = item_rect.left + icon_size + 60
            draw_text_with_shadow(screen, name_text, name_font, colors["text_body"], top_left=(text_x, item_rect.top + 25))
            
            # 詳細ステータス
            detail_text = f"Tier: {stats.get('tier', 1)}  Damage: {stats.get('damage', 0)}"
            screen.blit(detail_font.render(detail_text, False, colors["text_detail"]), (text_x, item_rect.top + 80))
            
            current_y += layout["item_height"] + layout["item_gap"]