import pygame
import config
from src.scenes.title_screen import TitleScreen
from src.scenes.game_play_screen import GameplayScreen
from src.scenes.stage_select import StageSelectScreen
# ★追加: ゲームオーバー画面をインポート
from src.scenes.game_over import GameOverScreen
from pygame.locals import *

def main():
    pygame.init()
    pygame.mixer.init()

    # --- フルスクリーン設定とスケーリング計算 ---
    info = pygame.display.Info()
    monitor_width = info.current_w
    monitor_height = info.current_h

    config.SCREEN_WIDTH = monitor_width
    config.SCREEN_HEIGHT = monitor_height
    
    if hasattr(config, 'BASE_SCREEN_WIDTH'):
        config.GLOBAL_SCALE = monitor_width / config.BASE_SCREEN_WIDTH
    else:
        config.GLOBAL_SCALE = 1.0
    
    print(f"Screen: {monitor_width}x{monitor_height}, Scale: {config.GLOBAL_SCALE:.2f}")

    screen = pygame.display.set_mode((monitor_width, monitor_height), pygame.FULLSCREEN)
    pygame.display.set_caption(config.CAPTION)
    # ----------------------------------------

    clock = pygame.time.Clock()

    # コントローラー初期化
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Controller connected: {joystick.get_name()}")
    else:
        print("No controller detected.")

    # シーン管理
    # GAME_OVER は動的に生成するので辞書には入れなくても良いですが、管理上入れておきます
    scenes = {
        "TITLE": TitleScreen(),
        "STAGE_SELECT": StageSelectScreen(),
        "GAMEPLAY": None,
        "GAME_OVER": None # ★プレースホルダ
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
            action = current_scene.handle_events(events)
            
            # ... (前略)
            if action:
                # --- タイトル画面からの遷移 ---
                if action == "START_GAME":
                    print("Transition: Title -> Stage Select")
                    current_scene_key = "STAGE_SELECT"
                    scenes["STAGE_SELECT"] = StageSelectScreen()
                    current_scene = scenes["STAGE_SELECT"]
                
                # --- ステージ選択からの遷移 ---
                elif isinstance(action, tuple) and action[0] == "GAMEPLAY":
                    stage_key = action[1]
                    print(f"Transition: Stage Select -> Gameplay ({stage_key})")
                    scenes["GAMEPLAY"] = GameplayScreen(stage_key)
                    current_scene_key = "GAMEPLAY"
                    current_scene = scenes["GAMEPLAY"]

                # --- ★追加: ゲームオーバーからのリトライ (CONTINUE) ---
                # GameOverScreenが ("GAMEPLAY", "forest") のようなタプルを返している場合は上のブロックで動きますが、
                # 単に "GAMEPLAY" という文字列だけを返している場合はここが必要です。
                elif action == "GAMEPLAY":
                    # 直前のステージ情報をGameOverScreenが持っているはずですが、
                    # ここでは念のため "forest" などのデフォルトか、保存されたキーを使います
                    # (GameOverScreenの仕様に合わせて調整してください)
                    retry_stage = getattr(current_scene, 'retry_stage_key', 'forest')
                    print(f"Retry: Gameplay ({retry_stage})")
                    scenes["GAMEPLAY"] = GameplayScreen(retry_stage)
                    current_scene_key = "GAMEPLAY"
                    current_scene = scenes["GAMEPLAY"]

                # --- 共通: タイトルへ戻る ---
                elif action == "TITLE":
                    print("Transition: -> Title")
                    current_scene_key = "TITLE"
                    current_scene = scenes["TITLE"]
                
                # --- ゲーム終了 ---
                elif action == "QUIT":
                    running = False

        # 更新処理
        result = current_scene.update(dt)
        
        # --- ★追加: ゲームプレイ中の状態遷移チェック ---
        if result == "GAME_OVER":
            print("Transition: Gameplay -> Game Over")
            
            # ★修正: 直前のステージ名を取得して渡す
            # GameplayScreen が self.biome を持っている前提です
            last_stage_key = current_scene.biome 
            
            current_scene_key = "GAME_OVER"
            scenes["GAME_OVER"] = GameOverScreen(last_stage_key)          
            current_scene = scenes["GAME_OVER"]
            
        elif result == "TITLE":
            current_scene_key = "TITLE"
            current_scene = scenes["TITLE"]

        # 描画
        current_scene.draw(screen)
        pygame.display.flip()

        # 安全装置 (タイトルでESC)
        keys = pygame.key.get_pressed()
        if current_scene_key == "TITLE" and keys[pygame.K_ESCAPE]:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()