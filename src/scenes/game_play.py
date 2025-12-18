# src/scenes/gameplay.py
import pygame
import random
import time # 追加
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.system.db_manager import DBManager # 追加

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        
        # DB接続
        self.db = DBManager() # 追加

        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()

        self.player = Player(
            (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), 
            self.all_sprites, 
            self.bullets_group
        )
        self.all_sprites.add(self.player)
        
        self.bg_color = config.BG_COLOR
        if self.biome == "grass": self.bg_color = (34, 139, 34)
        elif self.biome == "water": self.bg_color = (30, 144, 255)
        elif self.biome == "volcano": self.bg_color = (139, 0, 0)
        elif self.biome == "cloud": self.bg_color = (200, 200, 255)

        self.last_spawn_time = 0
        self.spawn_interval = 500

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return "TITLE"

        self.spawn_enemies()
        self.all_sprites.update(dt)
        
        # --- 変更: 当たり判定とログ保存 ---
        # groupcollideの結果は {bullet: [enemy1, enemy2...]} という辞書で返る
        hits = pygame.sprite.groupcollide(self.bullets_group, self.enemies_group, True, False) # 敵をまだ消さない
        
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                # ここでHP処理などを入れてもよいが、今回は即死させる
                enemy.death_time = time.time() # 死んだ時刻を記録
                
                # DBに保存
                self.db.log_mob_death(enemy, generation=1, biome=self.biome)
                
                enemy.kill() # スプライトから削除
        # -------------------------------
        
        hits_player = pygame.sprite.spritecollide(self.player, self.enemies_group, False)
        if hits_player:
            print("ダメージ！")

        return None

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)

    # spawn_enemies と get_random_spawn_pos は変更なし
    def spawn_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
            spawn_pos = self.get_random_spawn_pos()
            enemy = Enemy(spawn_pos, self.player)
            self.all_sprites.add(enemy)
            self.enemies_group.add(enemy)
            self.last_spawn_time = current_time

    def get_random_spawn_pos(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH), -50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (-50, random.randint(0, config.SCREEN_HEIGHT))
        elif edge == 'right':
            return (config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT))