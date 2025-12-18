# src/entities/player.py
import pygame
from pygame.math import Vector2
import config

class Player(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y):
        super().__init__()
        # 画像の代わりに赤い四角形を作成 (後で画像読み込みに差し替えます)
        self.image = pygame.Surface((config.PLAYER_SIZE, config.PLAYER_SIZE))
        self.image.fill(config.RED)
        
        # 当たり判定用のRect取得
        self.rect = self.image.get_rect()
        
        # 【重要】位置をベクトル(小数)で管理
        self.pos = Vector2(start_x, start_y)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        self.speed = config.PLAYER_SPEED

    def update(self, dt):
        """
        dt: 前フレームからの経過時間(秒)
        """
        self.input(dt)

# src/entities/player.py

    def input(self, dt):
        keys = pygame.key.get_pressed()
        
        # 移動ベクトルの計算
        direction = Vector2(0, 0)
        
        # 1. キーボード入力
        if keys[pygame.K_w]: direction.y = -1
        if keys[pygame.K_s]: direction.y = 1
        if keys[pygame.K_a]: direction.x = -1
        if keys[pygame.K_d]: direction.x = 1

        # 2. コントローラー入力 (キー入力がない場合のみ、または合算)
        # コントローラーが接続されているか確認
        if direction.length() == 0 and pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0) # 1つ目のコントローラーを取得
            
            # 左スティックの横軸(0)と縦軸(1)を取得 (-1.0 〜 1.0 の小数)
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)

            # デッドゾーン設定 (スティックの微妙なブレを無視する閾値)
            deadzone = 0.1
            if abs(axis_x) > deadzone:
                direction.x = axis_x
            if abs(axis_y) > deadzone:
                direction.y = axis_y

        # 斜め移動の速度補正 (長さが0より大きければ正規化して一定速度にする)
        if direction.length() > 0:
            direction = direction.normalize()
            
        # 位置更新
        self.pos += direction * self.speed * dt
        
        # ... (以下変更なし)
        
        # 画面外に出ないように制限 (簡易版)
        self.pos.x = max(0, min(self.pos.x, config.SCREEN_WIDTH))
        self.pos.y = max(0, min(self.pos.y, config.SCREEN_HEIGHT))

        # 描画位置への反映
        self.rect.center = (round(self.pos.x), round(self.pos.y))