import pygame
import config

class GameClearScreen:
    def __init__(self):
        try:
            self.title_font = pygame.font.Font(config.FONT_PATH, 80)
            self.msg_font = pygame.font.Font(config.FONT_PATH, 40)
        except:
            self.title_font = pygame.font.SysFont(None, 80)
            self.msg_font = pygame.font.SysFont(None, 40)
            
        self.start_time = pygame.time.get_ticks()

    def update(self, dt):
        return None

    def handle_events(self, events):
        # 少し待ってからキー入力を受け付ける（誤操作防止）
        if pygame.time.get_ticks() - self.start_time < 1000:
            return None
            
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: # Enterでタイトルへ
                    return "TITLE"
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
        return None

    def draw(self, screen):
        # 背景を少し明るい色や、勝利っぽい色にする
        screen.fill((50, 50, 100)) 
        
        # テキスト描画
        title_text = self.title_font.render("GAME CLEAR!!", True, (255, 255, 0)) # 黄色
        msg_text = self.msg_font.render("Press Enter to Title", True, (255, 255, 255))
        
        title_rect = title_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 50))
        msg_rect = msg_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 50))
        
        screen.blit(title_text, title_rect)
        screen.blit(msg_text, msg_rect)