import pygame
import config
from src.entities.player import Player

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()

        # プレイヤー生成
        self.player = Player(
            (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), 
            self.all_sprites, 
            self.bullets_group
        )
        self.all_sprites.add(self.player)
        
        # ステージごとの背景色
        self.bg_color = config.BG_COLOR
        if self.biome == "grass": self.bg_color = (34, 139, 34)
        elif self.biome == "water": self.bg_color = (30, 144, 255)
        elif self.biome == "volcano": self.bg_color = (139, 0, 0)
        elif self.biome == "cloud": self.bg_color = (200, 200, 255)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return "TITLE" # ESCでタイトルへ戻る

        self.all_sprites.update(dt)
        return None

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)