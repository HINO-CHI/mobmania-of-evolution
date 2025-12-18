import pygame
import config

class StageSelectScreen:
    def __init__(self):
        self.font = pygame.font.Font(None, 50)
        self.options = ["1. Grassland", "2. Water", "3. Volcano", "4. Clouds"]
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]: return ("GAME", "grass")
        if keys[pygame.K_2]: return ("GAME", "water")
        if keys[pygame.K_3]: return ("GAME", "volcano")
        if keys[pygame.K_4]: return ("GAME", "cloud")
        return None

    def draw(self, screen):
        screen.fill((20, 50, 20)) # 少し緑っぽい背景
        title = self.font.render("Select Biome (Press 1-4)", True, config.WHITE)
        screen.blit(title, (50, 50))

        for i, option in enumerate(self.options):
            text = self.font.render(option, True, config.WHITE)
            screen.blit(text, (100, 150 + i * 80))