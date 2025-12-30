import pygame
import config
from src.scenes.title_screen import TitleScreen
from src.scenes.game_play import GameplayScreen
# ★追加: ステージ選択画面をインポート
from src.scenes.stage_select import StageSelectScreen
# ジョイスティック（コントローラー）用
from pygame.locals import *

def main():
    pygame.init()
    pygame.mixer.init()

    # --- フルスクリーン設定とスケーリング計算 ---
    info = pygame.display.Info()
    monitor_width = info.current_w
    monitor_height = info.current_h

    # configを更新
    config.SCREEN_WIDTH = monitor_width
    config.SCREEN_HEIGHT = monitor_height
    
    # ★追加: 倍率の計算 (現在の幅 / 基準の幅)
    # 例: 1920pxのモニターなら 1920 / 800 = 2.4倍 になる
    config.GLOBAL_SCALE = monitor_width / config.BASE_SCREEN_WIDTH
    
    print(f"Screen: {monitor_width}x{monitor_height}, Scale: {config.GLOBAL_SCALE:.2f}")

    screen = pygame.display.set_mode((monitor_width, monitor_height), pygame.FULLSCREEN)
    pygame.display.set_caption(config.CAPTION)
    # ----------------------------------------
    
    # ... (以下変更なし) ...
    # -----------------------------

    clock = pygame.time.Clock()

    # コントローラーの初期化
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")
    else:
        print("No controller detected.")

    # シーン管理
    scenes = {
        "TITLE": TitleScreen(),
        "STAGE_SELECT": StageSelectScreen(), # ★追加: ステージ選択画面を登録
        "GAMEPLAY": None 
    }
    current_scene_key = "TITLE"
    current_scene = scenes["TITLE"]

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # シーンごとのイベント処理
            # シーンから次のアクションを受け取る
            action = current_scene.handle_events(events)
            
            if action:
                # パターンA: タイトルでスタート -> ステージ選択へ
                if action == "START_GAME":
                    print("Transition: Title -> Stage Select")
                    current_scene_key = "STAGE_SELECT"
                    current_scene = scenes["STAGE_SELECT"]
                
                # パターンB: ステージ選択で決定 -> ゲーム開始
                # ステージ選択画面からは ("GAMEPLAY", "stage_key") というタプルが返ってくる想定
                elif isinstance(action, tuple) and action[0] == "GAMEPLAY":
                    stage_key = action[1]
                    print(f"Transition: Stage Select -> Gameplay ({stage_key})")
                    
                    # 選ばれたステージでゲーム画面を初期化
                    scenes["GAMEPLAY"] = GameplayScreen(stage_key)
                    current_scene_key = "GAMEPLAY"
                    current_scene = scenes["GAMEPLAY"]

                # パターンC: タイトルへ戻る
                elif action == "TITLE":
                    print("Transition: -> Title")
                    current_scene_key = "TITLE"
                    current_scene = scenes["TITLE"]

        # 更新
        result = current_scene.update(dt)
        if result == "TITLE":
            current_scene_key = "TITLE"
            current_scene = scenes["TITLE"]

        # 描画
        current_scene.draw(screen)
        pygame.display.flip()

        # ESCキー長押しなどで終了できるようにしておくと便利（今回は×ボタンで終了）
        keys = pygame.key.get_pressed()
        # タイトル画面でESCを押したらゲーム終了にする安全装置
        if current_scene_key == "TITLE" and keys[pygame.K_ESCAPE]:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()