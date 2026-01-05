# src/system/map_generator.py
import pygame
import random
import config
from src.entities.obstacle import Obstacle

class MapGenerator:
    def __init__(self, biome_type):
        self.biome = biome_type
        # マップサイズ (広すぎると生成に時間がかかるので 3000px 程度に)
        self.map_width = 3000
        self.map_height = 3000
        # タイルサイズ
        self.tile_size = 60
        
        self.cols = self.map_width // self.tile_size
        self.rows = self.map_height // self.tile_size
        
        self.obstacles_group = pygame.sprite.Group()
        self.decoration_group = pygame.sprite.Group()
        
        # グリッド管理用
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    def generate(self):
        print(f"Generating map for biome: {self.biome}...")
        self.obstacles_group.empty()
        self.decoration_group.empty()
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        
        settings = config.STAGE_SETTINGS.get(self.biome, {})
        assets = settings.get("assets", {})
        obs_assets = assets.get("obstacles", [])
        deco_assets = assets.get("decorations", [])

        # ================================
        # 1. 障害物 (木・岩) の配置
        # ================================
        # 中央（スタート地点）周辺を避ける
        center_c, center_r = self.cols // 2, self.rows // 2
        
        # 全体で50個ほど配置
        for _ in range(50):
            c = random.randint(0, self.cols - 1)
            r = random.randint(0, self.rows - 1)
            # 中央5マス以内は置かない
            if abs(c - center_c) < 5 and abs(r - center_r) < 5:
                continue
            
            if self.grid[r][c] is None and obs_assets:
                self.grid[r][c] = {"type": "obstacle", "name": random.choice(obs_assets)}

        # ================================
        # 2. 草の生成 (セル・オートマトン)
        # ================================
        if self.biome == "grass" and deco_assets:
            self._generate_grass_automata(deco_assets)

        # ================================
        # 3. スプライト化
        # ================================
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell:
                    x = c * self.tile_size + self.tile_size // 2 + random.randint(-10, 10)
                    y = r * self.tile_size + self.tile_size // 2 + random.randint(-10, 10)
                    
                    if cell["type"] == "obstacle":
                        s = Obstacle((x, y), cell["name"], is_solid=True)
                        self.obstacles_group.add(s)
                    elif cell["type"] == "grass":
                        s = Obstacle((x, y), cell["name"], is_solid=False)
                        self.decoration_group.add(s)
        
        print("Map generation complete.")
        return self.obstacles_group, self.decoration_group

    def _generate_grass_automata(self, deco_assets):
        """草の繁殖ロジック"""
        base_grass = deco_assets[0] if deco_assets else "stage1-kusa2.png"
        
        # Phase 1: ランダムな種まき (確率 0.1)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] is None:
                    if random.random() < 0.1:
                        self.grid[r][c] = {"type": "grass", "name": base_grass}

        # Phase 2: 繁殖 (確率 0.1 + 隣接数 * 0.1)
        # コピーを作成して判定
        current_grid = [row[:] for row in self.grid]
        
        for r in range(self.rows):
            for c in range(self.cols):
                if current_grid[r][c] is None:
                    neighbors = self._count_neighbors(current_grid, c, r)
                    if neighbors > 0:
                        prob = 0.1 + (neighbors * 0.1)
                        if random.random() < prob:
                            self.grid[r][c] = {"type": "grass", "name": base_grass}

        # Phase 3: 成長 (密集度で種類変更)
        # 最終結果を参照して書き換え
        final_ref = [row[:] for row in self.grid]
        for r in range(self.rows):
            for c in range(self.cols):
                cell = final_ref[r][c]
                if cell and cell["type"] == "grass":
                    neighbors = self._count_neighbors(final_ref, c, r)
                    
                    # 密集度が高いなら豪華な草へ
                    if neighbors >= 5 and len(deco_assets) > 1:
                        # リストの後ろの方（kusa3, kusa5など）からランダム
                        new_name = random.choice(deco_assets[1:])
                        self.grid[r][c]["name"] = new_name

    def _count_neighbors(self, grid, c, r):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nc, nr = c + dx, r + dy
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    cell = grid[nr][nc]
                    if cell and cell["type"] == "grass":
                        count += 1
        return count
    
    # setupやupdateは不要になったので削除