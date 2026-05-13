import pygame
import math
from game.constants import WIDTH, HEIGHT


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, radius=4, color=(255, 255, 255), damage=1, is_player=False):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.radius = radius
        self.color = color
        self.damage = damage
        self.is_player = is_player
        self.grazed = False

        s = radius * 2 + 6
        self.image = pygame.Surface((s, s), pygame.SRCALPHA)
        cx = cy = s // 2
        # Dim outer halo
        pygame.draw.circle(self.image, (*color[:3], 60), (cx, cy), radius + 2)
        # Main body
        pygame.draw.circle(self.image, color, (cx, cy), radius)
        # Bright core
        core_r = max(1, radius // 2)
        bright = tuple(min(255, c + 90) for c in color[:3])
        pygame.draw.circle(self.image, bright, (cx, cy), core_r)

        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        self.pos += self.vel
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if (self.pos.x < -40 or self.pos.x > WIDTH + 40 or
                self.pos.y < -40 or self.pos.y > HEIGHT + 40):
            self.kill()


class HomingBullet(Bullet):
    def __init__(self, x, y, vx, vy, player_ref, turn_rate=0.03, **kwargs):
        super().__init__(x, y, vx, vy, **kwargs)
        self.player_ref = player_ref
        self.turn_rate = turn_rate
        self.speed = max(0.5, self.vel.length())

    def update(self):
        if self.player_ref is not None:
            target = self.player_ref.pos
            diff = target - self.pos
            if diff.length() > 0:
                desired = diff.normalize() * self.speed
                self.vel += (desired - self.vel) * self.turn_rate
                if self.vel.length() > 0:
                    self.vel.scale_to_length(self.speed)
        super().update()
