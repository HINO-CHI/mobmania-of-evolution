# src/scenes/gameplay.py
import pygame
import random
import config
from src.entities.player import Player
from src.entities.enemy import Enemy # 追加

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        # グループ分け
        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group() # 追加: 敵グループ

        # プレイヤー生成
        self.player = Player(
            (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), 
            self.all_sprites, 
            self.bullets_group
        )
        self.all_sprites.add(self.player)
        
        # 背景色
        self.bg_color = config.BG_COLOR
        if self.biome == "grass": self.bg_color = (34, 139, 34)
        elif self.biome == "water": self.bg_color = (30, 144, 255)
        elif self.biome == "volcano": self.bg_color = (139, 0, 0)
        elif self.biome == "cloud": self.bg_color = (200, 200, 255)

        # 敵スポーン用タイマー
        self.last_spawn_time = 0
        self.spawn_interval = 1000 # 1秒ごとに発生

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return "TITLE"

        # 1. 敵のスポーン処理
        self.spawn_enemies()

        # 2. 全スプライトの更新
        self.all_sprites.update(dt)
        
        # 3. 当たり判定: 弾 vs 敵
        # groupcollide(A, B, True, True) -> AとBが触れたら両方消す(True)
        hits = pygame.sprite.groupcollide(self.bullets_group, self.enemies_group, True, True)
        if hits:
            # ここで将来的に「撃破ログ」をDBに保存します
            pass

        # 4. 当たり判定: 敵 vs プレイヤー
        # spritecollide(A, B, False) -> AとBグループが触れたらリストを返す（消さない）
        hits_player = pygame.sprite.spritecollide(self.player, self.enemies_group, False)
        if hits_player:
            print("Ouch! Player hit!")
            # ここにHP減少処理やゲームオーバー判定が入ります

        return None

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)

    def spawn_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
            # 画面外のランダムな位置を計算
            spawn_pos = self.get_random_spawn_pos()
            
            enemy = Enemy(spawn_pos, self.player)
            self.all_sprites.add(enemy)
            self.enemies_group.add(enemy)
            
            self.last_spawn_time = current_time

    def get_random_spawn_pos(self):
        # 画面の四辺のどこかから出現させる
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH), -50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (-50, random.randint(0, config.SCREEN_HEIGHT))
        elif edge == 'right':
            return (config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT))