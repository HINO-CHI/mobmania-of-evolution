import pygame
import config

class StageSelectScreen:
    def __init__(self):
        # フォント読み込み
        try:
            self.font_title = pygame.font.Font(config.FONT_PATH, 50)
            self.font_body = pygame.font.Font(config.FONT_PATH, 30)
            self.font_small = pygame.font.Font(config.FONT_PATH, 20)
        except Exception:
            print("Warning: Pixel font not found, using default.")
            self.font_title = pygame.font.SysFont(None, 60)
            self.font_body = pygame.font.SysFont(None, 40)
            self.font_small = pygame.font.SysFont(None, 24)
        
        # configからステージキーを取得
        self.stage_keys = list(config.STAGE_SETTINGS.keys())

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "TITLE"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    return self.handle_click(event.pos)
        return None

    def get_card_rects(self):
        # カードの配置計算
        card_width = 250
        card_height = 350
        gap = 30
        total_width = len(self.stage_keys) * card_width + (len(self.stage_keys) - 1) * gap
        
        start_x = (config.SCREEN_WIDTH - total_width) // 2
        center_y = config.SCREEN_HEIGHT // 2
        
        rects = []
        for i, key in enumerate(self.stage_keys):
            card_x = start_x + i * (card_width + gap)
            rect = pygame.Rect(card_x, center_y - card_height // 2, card_width, card_height)
            rects.append((key, rect))
        return rects

    def handle_click(self, pos):
        for key, rect in self.get_card_rects():
            if rect.collidepoint(pos):
                print(f"Stage Selected: {key}")
                # 次のシーン名とステージキーを返す
                return ("GAMEPLAY", key)
        return None

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(config.BG_COLOR)
        
        # タイトル
        title_surf = self.font_title.render("SELECT STAGE", False, config.WHITE)
        screen.blit(title_surf, (config.SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        card_info = self.get_card_rects()

        for key, rect in card_info:
            data = config.STAGE_SETTINGS[key]
            is_hovered = rect.collidepoint(mouse_pos)
            
            # カード背景
            bg_color = config.UI_COLORS["item_bg_hover"] if is_hovered else config.UI_COLORS["item_bg_normal"]
            pygame.draw.rect(screen, bg_color, rect)
            
            # 枠線
            border_col = config.RED if is_hovered else config.UI_COLORS["item_border_normal"]
            border_width = 4 if is_hovered else 2
            pygame.draw.rect(screen, border_col, rect, border_width)

            # プレビューエリア
            preview_h = 150
            preview_rect = pygame.Rect(rect.x + 20, rect.y + 20, rect.width - 40, preview_h)
            pygame.draw.rect(screen, data["bg_color"], preview_rect)
            pygame.draw.rect(screen, config.BLACK, preview_rect, 2)
            
            # ステージ名
            name_surf = self.font_body.render(data["display_name"], False, config.UI_COLORS["text_body"])
            screen.blit(name_surf, (rect.centerx - name_surf.get_width()//2, preview_rect.bottom + 20))
            
            # 難易度
            stars = "★" * data["difficulty"]
            diff_surf = self.font_small.render(f"Diff: {stars}", False, config.RED)
            screen.blit(diff_surf, (rect.centerx - diff_surf.get_width()//2, preview_rect.bottom + 60))
            
            # クリック誘導
            if is_hovered:
                click_surf = self.font_small.render(">>> CLICK <<<", False, config.RED)
                screen.blit(click_surf, (rect.centerx - click_surf.get_width()//2, rect.bottom - 40))