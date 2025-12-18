# src/scenes/gameplay.py
import pygame
import random
import time
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager # 追加

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db) # 追加

        # Wave管理
        self.current_generation = 1
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5  # テスト用に「5体倒したら進化」にする
        self.pending_stats_queue = [] # 次にスポーンする予定の遺伝子リスト

        # ... (グループ初期化、プレイヤー生成などは変更なし) ...
        self.all_sprites = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()

        self.player = Player(
            (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), 
            self.all_sprites, 
            self.bullets_group
        )
        self.all_sprites.add(self.player)
        
        # ... (背景色設定などは変更なし) ...
        self.bg_color = config.BG_COLOR
        if self.biome == "grass": self.bg_color = (34, 139, 34)
        # ... 

        self.last_spawn_time = 0
        self.spawn_interval = 800

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return "TITLE"

        self.spawn_enemies()
        self.all_sprites.update(dt)
        
        hits = pygame.sprite.groupcollide(self.bullets_group, self.enemies_group, True, False)
        
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.death_time = time.time()
                # ログ保存 (現在の世代を記録)
                self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
                enemy.kill()

                # --- 進化判定 ---
                self.mobs_killed_in_wave += 1
                if self.mobs_killed_in_wave >= self.wave_threshold:
                    self.start_next_wave()
                # ----------------

        # ... (プレイヤーの当たり判定は変更なし) ...
        return None

    def start_next_wave(self):
        """次世代を開始する処理"""
        self.current_generation += 1
        self.mobs_killed_in_wave = 0
        print(f"=== WAVE {self.current_generation} START! ===")
        
        # 進化マネージャーを使って、次の20体分の遺伝子を生成してキューに入れる
        new_stats_list = self.evo_manager.create_next_generation_stats(self.biome, 20)
        
        if new_stats_list:
            self.pending_stats_queue.extend(new_stats_list)

    def spawn_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
            spawn_pos = self.get_random_spawn_pos()
            
            # --- 進化した遺伝子を使う ---
            stats_to_use = None
            if self.pending_stats_queue:
                stats_to_use = self.pending_stats_queue.pop(0) # キューから取り出す
            # ------------------------
            
            # stats_to_use を渡して敵を生成
            enemy = Enemy(spawn_pos, self.player, stats=stats_to_use)
            
            self.all_sprites.add(enemy)
            self.enemies_group.add(enemy)
            self.last_spawn_time = current_time

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(screen)

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