import pygame
import os
import config

class StageSelectScreen:
    def __init__(self):
        # フォント設定
        try:
            self.font = pygame.font.Font(config.FONT_PATH, 32)
            self.title_font = pygame.font.Font(config.FONT_PATH, 60)
            self.small_font = pygame.font.Font(config.FONT_PATH, 24)
        except:
            self.font = pygame.font.SysFont(None, 32)
            self.title_font = pygame.font.SysFont(None, 60)
            self.small_font = pygame.font.SysFont(None, 24)

        # --- マップ画像の読み込み ---
        self.map_image = None
        map_path = os.path.join("assets", "images", "maps", "stage.png")
        
        try:
            if os.path.exists(map_path):
                self.map_image = pygame.image.load(map_path).convert()
                self.map_image = pygame.transform.scale(self.map_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            else:
                print(f"Warning: Stage map image not found at {map_path}")
        except Exception as e:
            print(f"Error loading stage map: {e}")

        self.bg_color = (30, 30, 30)

        # =================================================================
        # ★ ステージ位置の手動設定エリア ★
        # ここで各ステージの (x, y) 座標を直接指定してください。
        # キー名は config.STAGE_SETTINGS のキーと一致させる必要があります。
        # =================================================================
        self.manual_positions = {
            # "キー名": (x座標, y座標)
            "forest":  (1000, 1000),  # Farest
            "desert":  (900, 300),  # Desert
            "volcano": (600, 700),  # Volcano
        }
        # =================================================================

        # --- ステージ情報の構築 (config連携) ---
        # config.STAGE_SETTINGS があれば使い、なければデフォルト
        raw_stages = getattr(config, "STAGE_SETTINGS", {
            "forest": {"display_name": "Farest", "bg_color": (50, 200, 50)},
            "desert": {"display_name": "Desert", "bg_color": (200, 200, 50)},
            "volcano": {"display_name": "Volcano", "bg_color": (200, 50, 50)}
        })

        self.nodes = []
        
        # 自動配置用の基準値（手動設定がない場合に使用）
        start_x = 200
        step_x = 250
        base_y = config.SCREEN_HEIGHT // 2
        
        # ステージの並び順を決定
        stage_keys = list(raw_stages.keys())
        
        # "forest" をスタート地点にするため先頭へ
        if "forest" in stage_keys:
            stage_keys.remove("forest")
            stage_keys.insert(0, "forest")
        elif "grass" in stage_keys: # 以前の設定名対策
            stage_keys.remove("grass")
            stage_keys.insert(0, "grass")

        for i, key in enumerate(stage_keys):
            info = raw_stages[key]
            
            # 座標決定ロジック
            # 1. このファイル内の manual_positions 設定を最優先
            if key in self.manual_positions:
                pos = self.manual_positions[key]
            # 2. configに 'pos' 指定がある場合
            elif "pos" in info:
                pos = info["pos"]
            elif "x" in info and "y" in info:
                pos = (info["x"], info["y"])
            else:
                # 3. 指定がない場合は従来の自動計算 (ジグザグ配置)
                offset_y = -80 if i % 2 == 0 else 80
                pos = (start_x + i * step_x, base_y + offset_y)
            
            # ロック判定: Farest (forest) 以外はロック
            is_locked = info.get("locked", False)
            if key not in ["forest", "grass"]:
                is_locked = True

            self.nodes.append({
                "index": i,
                "key": key,
                "name": info.get("display_name", key),
                "pos": pos,
                "locked": is_locked,
                "color": info.get("bg_color", (100, 100, 100))
            })

        # プレイヤーの状態
        self.current_index = 0 # 現在いるノードのインデックス
        self.target_index = None # 移動先のインデックス
        self.state = "IDLE" # "IDLE" or "MOVING"
        
        # キャラクター位置（最初はStartノードに配置）
        if self.nodes:
            start_pos = self.nodes[0]["pos"]
        else:
            start_pos = (0, 0)
            
        self.pos = pygame.math.Vector2(start_pos)
        self.move_speed = 600 # 移動速度
        
        # 入力受付開始までのクールダウン (誤操作防止)
        self.start_time = pygame.time.get_ticks()

    def handle_events(self, events):
        # 画面遷移直後の誤操作を防ぐために少し待つ
        if pygame.time.get_ticks() - self.start_time < 500:
            return None

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"
                
                # --- 移動入力 (IDLE時のみ) ---
                if self.state == "IDLE" and self.nodes:
                    # 右 (D) -> 次のステージへ
                    if (event.key == pygame.K_d or event.key == pygame.K_RIGHT):
                        if self.current_index < len(self.nodes) - 1:
                            self.set_target(self.current_index + 1)
                    
                    # 左 (A) -> 前のステージへ
                    elif (event.key == pygame.K_a or event.key == pygame.K_LEFT):
                        if self.current_index > 0:
                            self.set_target(self.current_index - 1)

                    # 決定 (Enter/Space) -> ステージ入場
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        current_node = self.nodes[self.current_index]
                        if not current_node["locked"]:
                            print(f"Stage Selected: {current_node['key']}")
                            return ("GAMEPLAY", current_node["key"])
                        else:
                            print(f"{current_node['name']} is locked!")

        return None

    def set_target(self, index):
        self.target_index = index
        self.state = "MOVING"

    def update(self, dt):
        # --- 移動アニメーション ---
        if self.state == "MOVING" and self.target_index is not None:
            target_pos = pygame.math.Vector2(self.nodes[self.target_index]["pos"])
            direction = target_pos - self.pos
            distance = direction.length()
            
            # 到着判定 (近いなら吸着)
            if distance < 15:
                self.pos = target_pos
                self.current_index = self.target_index
                self.target_index = None
                self.state = "IDLE"
            else:
                # 移動
                if distance > 0:
                    direction.normalize_ip()
                    self.pos += direction * self.move_speed * dt

        return None

    def draw(self, screen):
        # 1. 背景
        if self.map_image:
            screen.blit(self.map_image, (0, 0))
        else:
            screen.fill(self.bg_color)

        # ノードがなければ何もしない
        if not self.nodes:
            return

        # 2. ルート（線）の描画
        if len(self.nodes) > 1:
            points = [node["pos"] for node in self.nodes]
            pygame.draw.lines(screen, (200, 200, 200), False, points, 5)

        # 3. ノード（点）の描画
        for node in self.nodes:
            pos = node["pos"]
            color = node["color"]
            
            # ロックされていたらグレー
            draw_color = (80, 80, 80) if node["locked"] else color
            
            # 点を描画
            radius = 15
            pygame.draw.circle(screen, (255, 255, 255), pos, radius + 3) # 縁取り
            pygame.draw.circle(screen, draw_color, pos, radius)
            
            # ロックアイコン
            if node["locked"]:
                lock_surf = self.small_font.render("LOCKED", True, (200, 50, 50))
                lock_rect = lock_surf.get_rect(midbottom=(pos[0], pos[1] - 20))
                screen.blit(lock_surf, lock_rect)
            
            # ステージ名表示 (選択中のノードは大きく)
            if self.current_index == node["index"]:
                text_surf = self.font.render(node["name"], True, (255, 255, 0))
                text_rect = text_surf.get_rect(midtop=(pos[0], pos[1] + 25))
                # 影
                shadow = self.font.render(node["name"], True, (0, 0, 0))
                screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
                screen.blit(text_surf, text_rect)
            else:
                text_surf = self.small_font.render(node["name"], True, (200, 200, 200))
                text_rect = text_surf.get_rect(midtop=(pos[0], pos[1] + 20))
                screen.blit(text_surf, text_rect)

        # 4. プレイヤー（キャラ）の描画
        player_color = (255, 50, 50)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), 12)
        pygame.draw.circle(screen, player_color, (int(self.pos.x), int(self.pos.y)), 9)

        # 5. UIタイトル
        title = self.title_font.render("WORLD MAP", True, (255, 255, 255))
        title_shadow = self.title_font.render("WORLD MAP", True, (0, 0, 0))
        screen.blit(title_shadow, (23, 23))
        screen.blit(title, (20, 20))
        
        # ガイド
        current_node = self.nodes[self.current_index]
        if self.state == "IDLE":
            if not current_node["locked"]:
                msg_text = f"Press ENTER to enter {current_node['name']}"
                msg_color = (255, 255, 0)
            else:
                msg_text = "This area is currently unavailable."
                msg_color = (200, 200, 200)
                
            msg = self.font.render(msg_text, True, msg_color)
            msg_rect = msg.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
            pygame.draw.rect(screen, (0, 0, 0, 180), msg_rect.inflate(20, 10), border_radius=5)
            screen.blit(msg, msg_rect)