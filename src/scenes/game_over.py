# src/scenes/game_over.py
import pygame
import config

class GameOverScreen:
    def __init__(self, retry_stage_key):
        self.retry_stage_key = retry_stage_key
        
        try:
            self.title_font = pygame.font.Font(config.FONT_PATH, config.GAME_OVER_FONT_SIZE_TITLE)
            self.option_font = pygame.font.Font(config.FONT_PATH, config.GAME_OVER_FONT_SIZE_OPTION)
        except:
            self.title_font = pygame.font.SysFont(None, config.GAME_OVER_FONT_SIZE_TITLE)
            self.option_font = pygame.font.SysFont(None, config.GAME_OVER_FONT_SIZE_OPTION)
            
        self.options = ["CONTINUE", "QUIT"]
        self.selected_index = 0
        
        self.title_surf = self.title_font.render("GAME OVER", True, config.GAME_OVER_TEXT_COLOR)
        self.title_rect = self.title_surf.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 3))

    def update(self, dt):
        pass

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.get_selected_action()
                elif event.key == pygame.K_ESCAPE:
                    return "TITLE"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    action = self.check_mouse_click(event.pos)
                    if action:
                        return action
            
            # ★追加: マウス移動時に選択状態を更新（ホバー処理）
            elif event.type == pygame.MOUSEMOTION:
                self.check_mouse_hover(event.pos)
                
        return None

    def get_selected_action(self):
        if self.options[self.selected_index] == "CONTINUE":
            return ("RETRY", self.retry_stage_key)
        elif self.options[self.selected_index] == "QUIT":
            return "TITLE"
        return None

    # ★追加: ホバー判定用メソッド
    def check_mouse_hover(self, mouse_pos):
        base_y = config.SCREEN_HEIGHT * 2 // 3
        opt_width = 200
        spacing = 300
        start_x = (config.SCREEN_WIDTH - (len(self.options) * opt_width + (len(self.options) - 1) * spacing)) // 2

        for i, option in enumerate(self.options):
            opt_x = start_x + i * (opt_width + spacing)
            # クリック判定と同じ矩形を使用
            opt_rect = pygame.Rect(opt_x, base_y, opt_width, config.GAME_OVER_FONT_SIZE_OPTION)
            if opt_rect.collidepoint(mouse_pos):
                self.selected_index = i

    def check_mouse_click(self, mouse_pos):
        base_y = config.SCREEN_HEIGHT * 2 // 3
        opt_width = 200
        spacing = 300
        start_x = (config.SCREEN_WIDTH - (len(self.options) * opt_width + (len(self.options) - 1) * spacing)) // 2

        for i, option in enumerate(self.options):
            opt_x = start_x + i * (opt_width + spacing)
            opt_rect = pygame.Rect(opt_x, base_y, opt_width, config.GAME_OVER_FONT_SIZE_OPTION)
            if opt_rect.collidepoint(mouse_pos):
                self.selected_index = i
                return self.get_selected_action()
        return None

    def draw(self, screen):
        screen.fill(config.GAME_OVER_BG_COLOR)
        
        shadow_surf = self.title_font.render("GAME OVER", True, (0, 0, 150))
        screen.blit(shadow_surf, self.title_rect.move(4, 4))
        screen.blit(shadow_surf, self.title_rect.move(-4, -4))
        screen.blit(self.title_surf, self.title_rect)
        
        base_y = config.SCREEN_HEIGHT * 2 // 3
        opt_width = 200
        spacing = 300
        start_x = (config.SCREEN_WIDTH - (len(self.options) * opt_width + (len(self.options) - 1) * spacing)) // 2
        
        for i, option in enumerate(self.options):
            color = config.GAME_OVER_SELECT_COLOR if i == self.selected_index else config.GAME_OVER_OPTION_COLOR
            opt_text = option
            if option == "CONTINUE": opt_text = "▶ CONTINUE" if i == self.selected_index else "CONTINUE"
            if option == "QUIT": opt_text = "▶ QUIT" if i == self.selected_index else "QUIT"
            
            opt_surf = self.option_font.render(opt_text, True, color)
            opt_x = start_x + i * (opt_width + spacing)
            
            # テキスト描画位置（中心合わせ）
            center_x = opt_x + opt_width // 2
            center_y = base_y + config.GAME_OVER_FONT_SIZE_OPTION // 2
            opt_rect = opt_surf.get_rect(center=(center_x, center_y))
            
            screen.blit(opt_surf, opt_rect)
            
            # ★追加: 選択されている場合、黄色い枠を表示
            if i == self.selected_index:
                # テキストよりも少し大きめの枠を作る
                border_rect = opt_rect.inflate(40, 20) 
                pygame.draw.rect(screen, config.GAME_OVER_SELECT_COLOR, border_rect, 2)