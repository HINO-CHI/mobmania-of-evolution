# src/entities/bullet.py
import pygame
import config

class Bullet(pygame.sprite.Sprite):
    # ★変更: image 引数を追加 (Noneならデフォルトの黄色い丸)
    def __init__(self, pos, dir, damage, image=None):
        super().__init__()
        self.damage = damage
        self.pos = pygame.math.Vector2(pos)
        self.dir = dir
        self.speed = 600  # 弾速
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 2000 # 2秒で消える

        if image:
            # 画像がある場合
            self.image = image
            # 進行方向に回転させるとより良いですが、まずはそのまま表示
        else:
            # 画像がない場合（デフォルト）
            self.image = pygame.Surface((10, 10))
            self.image.fill(config.YELLOW)
        
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

    def update(self, dt):
        self.pos += self.dir * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
        
        # 画面外に出たら消す
        if (self.rect.right < 0 or self.rect.left > config.SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > config.SCREEN_HEIGHT):
            self.kill()