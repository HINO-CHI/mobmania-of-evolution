# src/scenes/gameplay.py
import pygame
import random
import time
import config
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.system.db_manager import DBManager
from src.system.evolution import EvolutionManager

# --- 追加: 当たり判定のルール関数 ---
def collide_hit_rect(one, two):
    # スプライトが hitbox を持っていれば使い、なければ rect を使う
    r1 = getattr(one, 'hitbox', one.rect)
    r2 = getattr(two, 'hitbox', two.rect)
    return r1.colliderect(r2)
# -------------------------------

class GameplayScreen:
    def __init__(self, biome_type):
        self.biome = biome_type
        self.db = DBManager()
        self.evo_manager = EvolutionManager(self.db)

        # Wave管理
        self.current_generation = 1
        self.mobs_killed_in_wave = 0
        self.wave_threshold = 5
        self.pending_stats_queue = []

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
        self.spawn_interval = 800

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return "TITLE"

        self.spawn_enemies()
        self.all_sprites.update(dt)
        
       # src/scenes/gameplay.py の updateメソッド内

        # --- 変更: 当たり判定とダメージ処理 ---
        # groupcollideの第3引数(弾)はTrue(消える)、第4引数(敵)はFalse(消えない)にする！
        hits = pygame.sprite.groupcollide(
            self.bullets_group, 
            self.enemies_group, 
            True,   # 弾は当たったら消える
            False,  # 敵はHP判定するので、ここではまだ消さない！
            collided=collide_hit_rect
        )
        
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                # 弾の持っているダメージを与える
                is_dead = enemy.take_damage(bullet.damage)
                
                if is_dead:
                    enemy.death_time = time.time()
                    self.db.log_mob_death(enemy, generation=self.current_generation, biome=self.biome)
                    enemy.kill() # ここで初めて消す

                    # 進化判定
                    self.mobs_killed_in_wave += 1
                    if self.mobs_killed_in_wave >= self.wave_threshold:
                        self.start_next_wave()

        # プレイヤーへの当たり判定も hitbox を使う
        hits_player = pygame.sprite.spritecollide(
            self.player, 
            self.enemies_group, 
            False, 
            collided=collide_hit_rect # <--- ここも重要
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
        if edge == 'top':
            return (random.randint(0, config.SCREEN_WIDTH), -50)
        elif edge == 'bottom':
            return (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + 50)
        elif edge == 'left':
            return (-50, random.randint(0, config.SCREEN_HEIGHT))
        elif edge == 'right':
            return (config.SCREEN_WIDTH + 50, random.randint(0, config.SCREEN_HEIGHT))