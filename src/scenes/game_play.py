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

# ==========================================
# 浮き出るテキスト (ダメージボイス用)
# ==========================================
class FloatingText(pygame.sprite.Sprite):
    def __init__(self, pos, text, color=(255, 50, 50)):
        super().__init__()
        try:
            self.font = pygame.font.Font(config.FONT_PATH, 22) 
        except:
            self.font = pygame.font.SysFont(None, 24)
            
        self.image = self.render_text_with_shadow(text, self.font, color)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(0, -50)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1200 

    def render_text_with_shadow(self, text, font, color):
        shadow = font.render(text, True, (0, 0, 0))
        main = font.render(text, True, color)
        width = shadow.get_width() + 2
        height = shadow.get_height() + 2
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.blit(shadow, (2, 2))
        surf.blit(main, (0, 0))
        return surf

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()

# ==========================================
# カメラ＆描画管理クラス
# ==========================================
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.margin = 100 
        self.debug_mode = False 

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

        # 通常スプライトとFloatingTextをYソートしつつ描画
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            if camera_rect.colliderect(sprite.rect): 
                offset_pos = sprite.rect.topleft - self.offset
                
                # FloatingTextは透過処理しない
                if isinstance(sprite, FloatingText):
                     self.display_surface.blit(sprite.image, offset_pos)
                     continue

                # 半透明処理
                if sprite != player and sprite.rect.centery > player.rect.centery:
                    if sprite.rect.colliderect(player.rect.inflate(10, 10)):
                        sprite.image.set_alpha(100)
                        self.display_surface.blit(sprite.image, offset_pos)
                        sprite.image.set_alpha(255)
                    else:
                        self.display_surface.blit(sprite.image, offset_pos)
                else:
                    self.display_surface.blit(sprite.image, offset_pos)

                # デバッグ表示
                if self.debug_mode and hasattr(sprite, 'hitbox'):
                    hitbox_rect = sprite.hitbox.copy()
                    hitbox_rect.topleft -= self.offset
                    pygame.draw.rect(self.display_surface, (255, 0, 0), hitbox_rect, 1)

# ==========================================
# ダメージ等のフローティングテキストクラス（追加）
# ==========================================
class FloatingText(pygame.sprite.Sprite):
    def __init__(self, pos, text, color=(255, 255, 255), duration=1000):
        super().__init__()
        # フォント設定（configにパスがあれば使用、なければデフォルト）
        try:
            self.font = pygame.font.Font(config.FONT_PATH, 24)
        except:
            self.font = pygame.font.SysFont(None, 24)
            
        # テキストの描画（視認性を高めるため、黒い縁取りまたは影を付ける）
        self.image_original = self.font.render(str(text), True, color)
        self.image_shadow = self.font.render(str(text), True, (0, 0, 0))
        
        width = self.image_original.get_width() + 2
        height = self.image_original.get_height() + 2
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.blit(self.image_shadow, (2, 2)) # 影を少しずらして描画
        self.image.blit(self.image_original, (0, 0)) # 本体を描画
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        # 上方向へ少しランダムに浮き上がる動き
        self.vel = pygame.math.Vector2(random.uniform(-1, 1), -2)
        
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255

    def update(self, dt):
        # 位置の更新
        self.pos += self.vel * (dt / 10 if dt else 1.0) # dt補正（想定）
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # フェードアウト処理
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        if elapsed > self.duration:
            self.kill()
        elif elapsed > self.duration * 0.7:
            # 寿命の残り30%でフェードアウト
            fade_ratio = 1.0 - ((elapsed - self.duration * 0.7) / (self.duration * 0.3))
            self.alpha = int(255 * fade_ratio)
            self.image.set_alpha(self.alpha)
