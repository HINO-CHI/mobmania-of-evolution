# src/system/map_generator.py
import pygame
import random
import config
import os
from src.entities.obstacle import Obstacle

class MapGenerator:
    def __init__(self, biome_type):
        self.biome = biome_type
        self.tile_size = 60
        self.chunk_tile_size = 10
        self.chunk_pixel_size = self.chunk_tile_size * self.tile_size
        
        self.loaded_chunks = {}
        
        self.obstacles_group = None
        self.decoration_group = None
        self.loaded_obstacles = []
        self.loaded_decorations = []
        
        # 設定値保持用
        self.obs_threshold = 0.75
        self.obs_density = 1.0     # ★追加: 密度
        self.deco_threshold = 0.40

    def setup(self, obstacles_group, decoration_group):
        self.obstacles_group = obstacles_group
        self.decoration_group = decoration_group
        
        settings = config.STAGE_SETTINGS.get(self.biome, {})
        gen_settings = settings.get("generation", {})
        
        # Config読み込み
        self.obs_threshold = gen_settings.get("obstacle_threshold", 0.75)
        self.obs_density = gen_settings.get("obstacle_density", 0.3) # ★デフォルト0.3
        self.deco_threshold = gen_settings.get("decoration_threshold", 0.40)
        
        assets = settings.get("assets", {})
        self.loaded_obstacles = self._preload_images(assets.get("obstacles", []), is_solid=True)
        self.loaded_decorations = self._preload_images(assets.get("decorations", []), is_solid=False)

        # フォールバック
        if not self.loaded_obstacles:
            s = pygame.Surface((60, 60))
            s.fill((139, 69, 19))
            self.loaded_obstacles.append((s, {}))

        if not self.loaded_decorations:
            s = pygame.Surface((60, 60))
            s.fill((50, 205, 50))
            s.set_alpha(150)
            self.loaded_decorations.append((s, {}))

    def update(self, player_pos):
        if self.obstacles_group is None or self.decoration_group is None:
            return

        pcx = int(player_pos.x // self.chunk_pixel_size)
        pcy = int(player_pos.y // self.chunk_pixel_size)

        visible_chunks = set()
        range_radius = 2
        
        for dy in range(-range_radius, range_radius + 1):
            for dx in range(-range_radius, range_radius + 1):
                chunk_coord = (pcx + dx, pcy + dy)
                visible_chunks.add(chunk_coord)
                
                if chunk_coord not in self.loaded_chunks:
                    self._generate_chunk(chunk_coord)

        for chunk_coord in list(self.loaded_chunks.keys()):
            if chunk_coord not in visible_chunks:
                self._unload_chunk(chunk_coord)

    def _preload_images(self, names, is_solid):
        loaded = []
        base_size = 80
        for name in names:
            file_name = name
            if not name.lower().endswith('.png'): file_name += ".png"
            path = os.path.join(config.MAP_IMAGE_DIR, file_name)
            props = config.MAP_OBJECT_SETTINGS.get(file_name, {})
            scale_factor = props.get("scale", 1.0)
            
            try:
                img = pygame.image.load(path).convert_alpha()
                target_w = int(base_size * scale_factor)
                aspect = img.get_height() / img.get_width()
                target_h = int(target_w * aspect)
                img = pygame.transform.scale(img, (target_w, target_h))
                loaded.append((img, props))
            except:
                continue
        return loaded

    def _unload_chunk(self, chunk_coord):
        sprites = self.loaded_chunks.pop(chunk_coord)
        for sprite in sprites:
            sprite.kill()

    def _generate_chunk(self, chunk_coord):
        cx, cy = chunk_coord
        new_sprites = []
        
        chunk_seed = (cx * 73856093) ^ (cy * 19349663)
        random.seed(chunk_seed)

        noise_map = self._generate_noise_grid(self.chunk_tile_size)

        for r in range(self.chunk_tile_size):
            for c in range(self.chunk_tile_size):
                val = noise_map[r][c]
                
                world_x = (cx * self.chunk_pixel_size) + (c * self.tile_size) + self.tile_size // 2
                world_y = (cy * self.chunk_pixel_size) + (r * self.tile_size) + self.tile_size // 2
                
                world_x += random.randint(-15, 15)
                world_y += random.randint(-15, 15)

                # --- 配置ロジック (密度チェックを追加) ---
                
                # 障害物: ノイズ条件クリア AND 確率抽選クリア
                # これにより、森エリアの中でも「まばら」に配置される
                if val > self.obs_threshold:
                    # ★ここが重要: density (0.3など) より小さい乱数が出た時だけ置く
                    if random.random() < self.obs_density:
                        data = random.choice(self.loaded_obstacles)
                        img, props = data
                        s = Obstacle((world_x, world_y), img, is_solid=True, props=props)
                        self.obstacles_group.add(s)
                        new_sprites.append(s)
                
                # 装飾 (草)
                elif val > self.deco_threshold:
                    normalized = (val - self.deco_threshold) / (self.obs_threshold - self.deco_threshold)
                    idx = int(normalized * len(self.loaded_decorations))
                    idx = min(idx, len(self.loaded_decorations) - 1)
                    idx = max(0, idx)

                    if random.random() < 0.3:
                        data = random.choice(self.loaded_decorations)
                    else:
                        data = self.loaded_decorations[idx]
                    
                    img, props = data
                    s = Obstacle((world_x, world_y), img, is_solid=False, props=props)
                    self.decoration_group.add(s)
                    new_sprites.append(s)

        self.loaded_chunks[chunk_coord] = new_sprites

    def _generate_noise_grid(self, size):
        grid = []
        c1 = random.random()
        c2 = random.random()
        c3 = random.random()
        c4 = random.random()
        for y in range(size):
            row = []
            for x in range(size):
                fx = x / size
                fy = y / size
                top = c1 * (1 - fx) + c2 * fx
                bottom = c3 * (1 - fx) + c4 * fx
                val = top * (1 - fy) + bottom * fy
                val += random.uniform(-0.1, 0.1)
                row.append(val)
            grid.append(row)
        return grid