import pygame
import config

class TitleScreen:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 80)
        self.font_small = pygame.font.Font(None, 40)
        
    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return "STAGE_SELECT"
        
        # コントローラーのボタンでもスタートできるようにする
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            if joy.get_button(0): # Aボタンなど
                return "STAGE_SELECT"
                
        return None

    def draw(self, screen):
        screen.fill(config.BG_COLOR)
        
        title = self.font_large.render(config.CAPTION, True, config.WHITE)
        msg = self.font_small.render("Press SPACE to Start", True, config.YELLOW)
        
        screen.blit(title, (config.SCREEN_WIDTH//2 - title.get_width()//2, 200))
        screen.blit(msg, (config.SCREEN_WIDTH//2 - msg.get_width()//2, 400))