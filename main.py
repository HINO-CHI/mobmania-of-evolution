# main.py
import pygame
import sys
import config
from src.entities.player import Player

# main.py の修正箇所（冒頭部分）

def main():
    # Pygameの初期化
    pygame.init()
    
    # --- 【追加】コントローラー（ジョイスティック）の初期化 ---
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        joystick.init()
    # ----------------------------------------------------

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    # ... (以下変更なし)
    pygame.display.set_caption(config.CAPTION)
    clock = pygame.time.Clock()

    # プレイヤーの生成 (画面中央)
    player = Player(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
    
    # スプライトグループの作成 (管理しやすくするため)
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    running = True
    while running:
        # 1. イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. 更新処理 (dt = 経過時間[秒])
        dt = clock.tick(config.FPS) / 1000
        all_sprites.update(dt)

        # 3. 描画処理
        screen.fill(config.BG_COLOR) # 背景を塗りつぶす
        all_sprites.draw(screen)     # 全スプライトを描画
        
        # 画面を更新
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()