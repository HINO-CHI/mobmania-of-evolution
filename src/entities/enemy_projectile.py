import pygame
import os
import math

def load_attack_image(filename):
    if not filename: return None
    path = os.path.join("assets", "images", "attack", filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        return img
    except (FileNotFoundError, pygame.error):
        return None

class EnemyProjectile(pygame.sprite.Sprite):
    # 引数に scale_size=None があることを確認
    def __init__(self, pos, target_pos, speed, damage, groups, image_name, scale_size=None):
        super().__init__(groups)
        
        raw_img = load_attack_image(image_name)
        
        if raw_img is None:
            self.image = pygame.Surface((20, 20))
            self.image.fill((255, 255, 0))
            pygame.draw.circle(self.image, (255, 0, 0), (10, 10), 5)
        else:
            # ★★★ ここが一番重要です！ ★★★
            # scale_size が指定されている場合、画像をそのサイズに拡大・縮小します
            if scale_size:
                self.image = pygame.transform.scale(raw_img, scale_size)
            else:
                self.image = raw_img
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        self.damage = damage
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 5000 

        # ターゲットに向かうベクトル計算
        direction = pygame.math.Vector2(target_pos) - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * speed
        else:
            self.velocity = pygame.math.Vector2(1, 0) * speed

        # 画像を進行方向に向ける
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()