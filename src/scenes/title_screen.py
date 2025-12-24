# src/scenes/title_screen.py
import pygame
import config

class TitleScreen:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)

    # ★★★ 追加: このメソッドが必要です ★★★
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "START_GAME"
                if event.key == pygame.K_ESCAPE:
                    # タイトルでESCを押したら終了
                    pygame.quit()
                    exit()
        return None
    # ★★★★★★★★★★★★★★★★★★★★★★

    def update(self, dt):
        return None

    def draw(self, screen):
        screen.fill(config.BG_COLOR)
        
        # 画面中央に配置（フルスクリーン対応）
        text_title = self.font_large.render(config.CAPTION, True, config.WHITE)
        rect_title = text_title.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 50))
        screen.blit(text_title, rect_title)

        text_start = self.font_small.render("Press SPACE to Start", True, config.YELLOW)
        rect_start = text_start.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 50))
        screen.blit(text_start, rect_start)