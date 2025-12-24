# src/scenes/game_play.py
import pygame
import random
import time
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager

def collide_hit_rect(one, two):
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)

        self.current_generation = 1
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []

        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()

        # フルスクリーン対応のため、画面中央の計算に config.SCREEN_WIDTH を使用
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
        self.spawn_interval = 800

    # ★★★ 追加: このメソッドが必要です ★★★
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESCキーでタイトルに戻る
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
        return None
    # ★★★★★★★★★★★★★★★★★★★★★★

    def update(self, dt):
        # handle_eventsで処理するので、ここのキー判定は削除しても良いですが、
        # 万が一のために残しておいても害はありません
        self.spawn_enemies()
        self.all_sprites.update(dt)
        
        hits = pygame.sprite.groupcollide(
            self.bullets_group, 
            self.enemies_group, 
            True, 
            False, 
            collided=collide_hit_rect
        )
        
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                is_dead = enemy.take_damage(bullet.damage)
                if is_dead:
                    enemy.death_time = time.time()
                    self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
                    enemy.kill()
                    self.mobs_killed_in_wave += 1
                    if self.mobs_killed_in_wave >= self.wave_threshold:
                        self.start_next_wave()

        hits_player = pygame.sprite.spritecollide(
            self.player, 
            self.enemies_group, 
            False, 
            collided=collide_hit_rect
        )
        if hits_player:
            print("ダメージ！")

        return None

    def start_next_wave(self):
        self.current_generation += 1
        self.mobs_killed_in_wave = 0
        print(f"=== WAVE {self.current_generation} START! ===")
        new_stats_list = self.evo_manager.create_next_generation_stats(self.biome, 20)
        if new_stats_list:
            self.pending_stats_queue.extend(new_stats_list)

    def spawn_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
            spawn_pos = self.get_random_spawn_pos()
            stats_to_use = None
            if self.pending_stats_queue:
                stats_to_use = self.pending_stats_queue.pop(0)
            enemy = Enemy(spawn_pos, self.player, stats=stats_to_use)
            self.all_sprites.add(enemy)
            self.enemies_group.add(enemy)
            self.last_spawn_time = current_time

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)

    def get_random_spawn_pos(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        # config.SCREEN_WIDTH/HEIGHT を使うことでフルスクリーンに対応
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH), -50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (-50, random.randint(0, config.SCREEN_HEIGHT))
        elif edge == 'right':
            return (config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT))