import pygame
import sys
import config
from src.scenes.title_screen import TitleScreen
from src.scenes.stage_select import StageSelectScreen
from src.scenes.game_play import GameplayScreen

def main():
    pygame.init()
    
    # コントローラー初期化
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        joy = pygame.joystick.Joystick(0)
        joy.init()
        print(f"Controller connected: {joy.get_name()}")

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.CAPTION)
    clock = pygame.time.Clock()

    # 最初のシーン
    current_scene = TitleScreen()

    running = True
    while running:
        # 1. イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. 時間計算
        dt = clock.tick(config.FPS) / 1000

        # 3. シーン更新
        result = current_scene.update(dt)

        # --- シーン遷移ロジック ---
        if result is not None:
            next_scene_name = result
            data = None
            
            # タプル ("GAME", "volcano") の場合
            if isinstance(result, tuple):
                next_scene_name = result[0]
                data = result[1]

            if next_scene_name == "TITLE":
                current_scene = TitleScreen()
            elif next_scene_name == "STAGE_SELECT":
                current_scene = StageSelectScreen()
            elif next_scene_name == "GAME":
                current_scene = GameplayScreen(data)
        # ------------------------

        # 4. 描画
        current_scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()