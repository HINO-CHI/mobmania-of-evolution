# src/scenes/stage_select.py
import pygame
import config

class StageSelectScreen:
    def __init__(self):
        # カードのレイアウト設定
        self.card_width = 220
        self.card_height = 300
        self.gap = 40
        self.start_y = 150
        
        # コンフィグからステージ情報を読み込む
        # なければデフォルトの草ステージを入れる
        self.stages = config.STAGE_SETTINGS if hasattr(config, "STAGE_SETTINGS") else {
            "grass": {"display_name": "Grass", "desc": "Training", "bg_color": (50, 200, 50)}
        }
        
        # カードの矩形（当たり判定用）を作成
        self.stage_rects = {}
        
        # 画面中央に寄せるための計算
        total_width = len(self.stages) * self.card_width + (len(self.stages) - 1) * self.gap
        current_x = (config.SCREEN_WIDTH - total_width) // 2
        
        for key in self.stages:
            rect = pygame.Rect(current_x, self.start_y, self.card_width, self.card_height)
            self.stage_rects[key] = rect
            current_x += self.card_width + self.gap

        # フォント読み込み
        try:
            self.title_font = pygame.font.Font(config.FONT_PATH, 50)
            self.card_font = pygame.font.Font(config.FONT_PATH, 30)
            self.desc_font = pygame.font.Font(config.FONT_PATH, 20)
        except:
            self.title_font = pygame.font.SysFont(None, 50)
            self.card_font = pygame.font.SysFont(None, 30)
            self.desc_font = pygame.font.SysFont(None, 20)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    mouse_pos = event.pos
                    # どのカードをクリックしたか判定
                    for key, rect in self.stage_rects.items():
                        if rect.collidepoint(mouse_pos):
                            print(f"Stage Selected: {key}")
                            # main.py に ("GAMEPLAY", "キー名") を返す
                            return ("GAMEPLAY", key)
        return None

    def update(self, dt):
        pass

    def draw(self, screen):
        # 背景
        screen.fill(config.BG_COLOR)
        
        # タイトル
        title_surf = self.title_font.render("SELECT STAGE", True, config.WHITE)
        title_rect = title_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        screen.blit(title_surf, title_rect)
        
        # ステージカード描画
        mouse_pos = pygame.mouse.get_pos()
        
        for key, rect in self.stage_rects.items():
            info = self.stages[key]
            
            # ホバー判定
            is_hovered = rect.collidepoint(mouse_pos)
            
            # カード背景色
            base_color = info.get("bg_color", (100, 100, 100))
            if is_hovered:
                # 明るくする
                color = (min(255, base_color[0]+30), min(255, base_color[1]+30), min(255, base_color[2]+30))
                draw_rect = rect.inflate(10, 10)
            else:
                color = base_color
                draw_rect = rect

            # カード枠
            pygame.draw.rect(screen, color, draw_rect, border_radius=10)
            pygame.draw.rect(screen, config.WHITE, draw_rect, 3, border_radius=10)
            
            # ステージ名
            name_surf = self.card_font.render(info.get("display_name", key), True, config.WHITE)
            name_rect = name_surf.get_rect(center=(draw_rect.centerx, draw_rect.top + 40))
            
            # 影付き文字
            shadow_surf = self.card_font.render(info.get("display_name", key), True, (0,0,0))
            screen.blit(shadow_surf, (name_rect.x+2, name_rect.y+2))
            screen.blit(name_surf, name_rect)
            
            # 説明文
            desc_surf = self.desc_font.render(info.get("desc", ""), True, (230, 230, 230))
            desc_rect = desc_surf.get_rect(center=(draw_rect.centerx, draw_rect.bottom - 40))
            screen.blit(desc_surf, desc_rect)