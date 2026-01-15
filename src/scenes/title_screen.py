import pygame
import os
import math
import config

class TitleScreen:
    def __init__(self):
        # フォント設定
        try:
            # 少し大きめのフォントを使用
            self.font = pygame.font.Font(config.FONT_PATH, 48)
            self.small_font = pygame.font.Font(config.FONT_PATH, 24)
        except:
            self.font = pygame.font.SysFont(None, 60)
            self.small_font = pygame.font.SysFont(None, 30)

        # --- 画像読み込み ---
        bg_path = os.path.join("assets", "images", "title", "title_mobmania_background.png")
        logo_path = os.path.join("assets", "images", "title", "title_mobmania_logo.png")

        self.background = None
        self.logo = None

        # 1. 背景画像の読み込みとスケーリング
        try:
            if os.path.exists(bg_path):
                bg_img = pygame.image.load(bg_path).convert()
                # 画面サイズに合わせてリサイズ
                self.background = pygame.transform.scale(bg_img, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            else:
                print(f"Warning: Title background not found at {bg_path}")
        except Exception as e:
            print(f"Error loading title background: {e}")

        # 2. ロゴ画像の読み込みとスケーリング
        try:
            if os.path.exists(logo_path):
                logo_img = pygame.image.load(logo_path).convert_alpha()
                
                # ロゴを画面幅の 60% くらいの幅に合わせてリサイズ
                target_width = int(config.SCREEN_WIDTH * 0.6)
                scale = target_width / logo_img.get_width()
                target_height = int(logo_img.get_height() * scale)
                
                self.logo = pygame.transform.scale(logo_img, (target_width, target_height))
            else:
                print(f"Warning: Title logo not found at {logo_path}")
        except Exception as e:
            print(f"Error loading title logo: {e}")

        self.start_time = pygame.time.get_ticks()

    def handle_events(self, events):
        for event in events:
            # キーを押すかクリックでゲーム開始
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # main.py側で終了処理をするためのシグナル
                    return "QUIT" 
                return "START_GAME"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                return "START_GAME"
                
        return None

    def update(self, dt):
        return None

    def draw(self, screen):
        # 1. 背景描画
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            # 画像がない場合はフォールバック（暗い青色のグラデーション風単色）
            screen.fill((20, 30, 50))

        # 2. ロゴ描画
        if self.logo:
            # 画面上部 (30%の位置) に配置
            logo_rect = self.logo.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 0.3))
            screen.blit(self.logo, logo_rect)
        else:
            # ロゴがない場合のテキスト表示
            title_text = self.font.render("MobMania of Evolution", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 0.3))
            screen.blit(title_text, title_rect)

        # 3. 「PRESS ANY KEY」の点滅演出
        current_time = pygame.time.get_ticks()
        # sin波を使ってアルファ値（透明度）をなめらかに変化させる (50〜255)
        alpha = (math.sin(current_time * 0.005) + 1) * 102.5 + 50
        
        press_text = self.font.render("PRESS ANY KEY TO START", True, (255, 255, 255))
        press_text.set_alpha(int(alpha))
        press_rect = press_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 0.75))
        
        # 視認性を上げるための影
        shadow_text = self.font.render("PRESS ANY KEY TO START", True, (0, 0, 0))
        shadow_text.set_alpha(int(alpha))
        shadow_rect = shadow_text.get_rect(center=(press_rect.centerx + 3, press_rect.centery + 3))
        
        screen.blit(shadow_text, shadow_rect)
        screen.blit(press_text, press_rect)
        
        # 4. クレジット表記（右下）
        credit_text = self.small_font.render("Database Project 2025", True, (200, 200, 200))
        credit_rect = credit_text.get_rect(bottomright=(config.SCREEN_WIDTH - 20, config.SCREEN_HEIGHT - 20))
        screen.blit(credit_text, credit_rect)