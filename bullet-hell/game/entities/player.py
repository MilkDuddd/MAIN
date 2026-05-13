import pygame
import math
from game.constants import (
    WIDTH, HEIGHT, PLAY_TOP,
    PLAYER_SPEED, PLAYER_FOCUS_SPEED, PLAYER_HITBOX_R,
    PLAYER_LIVES, PLAYER_INVINCIBLE, PLAYER_SHOOT_FRAMES,
    POWER_PER_CRYSTAL, POWER_TIER_THRESHOLDS,
    WHITE, CYAN, YELLOW, RED,
)
from game.entities.bullet import Bullet


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT - 130)
        self.vel = pygame.math.Vector2(0, 0)
        self.lives = PLAYER_LIVES
        self.power = 0
        self.power_tier = 0
        self.invincible = 0
        self.shoot_timer = 0
        self.is_focused = False
        self._tick = 0

        self.image = self._make_image()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.hitbox = pygame.Rect(0, 0, PLAYER_HITBOX_R * 2, PLAYER_HITBOX_R * 2)
        self.hitbox.center = self.rect.center

    def _make_image(self):
        img = pygame.Surface((32, 40), pygame.SRCALPHA)
        pts = [(16, 1), (3, 39), (16, 29), (29, 39)]
        pygame.draw.polygon(img, WHITE, pts)
        pygame.draw.polygon(img, CYAN, pts, 1)
        pygame.draw.circle(img, CYAN, (10, 35), 4)
        pygame.draw.circle(img, CYAN, (22, 35), 4)
        pygame.draw.circle(img, (200, 240, 255), (16, 18), 3)
        return img

    def update(self, keys, new_bullets):
        self._tick += 1

        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        self.is_focused = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        spd = PLAYER_FOCUS_SPEED if self.is_focused else PLAYER_SPEED
        if dx and dy:
            spd /= math.sqrt(2)

        self.pos.x = max(18, min(WIDTH - 18, self.pos.x + dx * spd))
        self.pos.y = max(PLAY_TOP + 20, min(HEIGHT - 20, self.pos.y + dy * spd))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.rect.center

        self.shoot_timer = max(0, self.shoot_timer - 1)
        shooting = keys[pygame.K_z] or keys[pygame.K_SPACE]
        if shooting and self.shoot_timer == 0:
            self.shoot_timer = PLAYER_SHOOT_FRAMES[min(self.power_tier, 4)]
            new_bullets.extend(self._make_bullets())

        if self.invincible > 0:
            self.invincible -= 1

    def _make_bullets(self):
        x, y = self.pos.x, self.pos.y - 22
        t = self.power_tier
        bullets = []

        if t == 0:
            bullets.append(Bullet(x, y, 0, -13, radius=3, color=CYAN, damage=1, is_player=True))

        elif t == 1:
            bullets.append(Bullet(x, y, 0, -13, radius=3, color=CYAN, damage=1, is_player=True))
            bullets.append(Bullet(x - 12, y + 6, -1.2, -12.9, radius=2, color=CYAN, damage=1, is_player=True))
            bullets.append(Bullet(x + 12, y + 6,  1.2, -12.9, radius=2, color=CYAN, damage=1, is_player=True))

        elif t == 2:
            bullets.append(Bullet(x - 4, y, 0, -13, radius=3, color=CYAN, damage=1, is_player=True))
            bullets.append(Bullet(x + 4, y, 0, -13, radius=3, color=CYAN, damage=1, is_player=True))
            bullets.append(Bullet(x - 15, y + 6, -1.8, -12.8, radius=2, color=YELLOW, damage=1, is_player=True))
            bullets.append(Bullet(x + 15, y + 6,  1.8, -12.8, radius=2, color=YELLOW, damage=1, is_player=True))

        elif t == 3:
            for off in [-20, -10, 0, 10, 20]:
                rad = math.radians(-90 + off)
                spd = 13.5
                bullets.append(Bullet(x, y, math.cos(rad) * spd, math.sin(rad) * spd,
                                       radius=3, color=CYAN, damage=1, is_player=True))
            bullets.append(Bullet(x - 18, y + 10, -2.5, -12.5, radius=2, color=YELLOW, damage=1, is_player=True))
            bullets.append(Bullet(x + 18, y + 10,  2.5, -12.5, radius=2, color=YELLOW, damage=1, is_player=True))

        else:  # tier 4
            for off in [-30, -18, -8, 0, 8, 18, 30]:
                rad = math.radians(-90 + off)
                spd = 14
                bullets.append(Bullet(x, y, math.cos(rad) * spd, math.sin(rad) * spd,
                                       radius=3, color=CYAN, damage=2, is_player=True))
            bullets.append(Bullet(x - 20, y + 8, -3, -12.5, radius=2, color=YELLOW, damage=1, is_player=True))
            bullets.append(Bullet(x + 20, y + 8,  3, -12.5, radius=2, color=YELLOW, damage=1, is_player=True))

        return bullets

    def take_hit(self):
        if self.invincible > 0:
            return False
        self.lives -= 1
        self.invincible = PLAYER_INVINCIBLE
        self.power = max(0, self.power - 25)
        self._recalc_tier()
        return True

    def add_power(self, amount):
        self.power += amount
        self._recalc_tier()

    def _recalc_tier(self):
        tier = 0
        for i, thresh in enumerate(POWER_TIER_THRESHOLDS):
            if self.power >= thresh:
                tier = i
        self.power_tier = tier

    def draw(self, surface):
        if self.invincible > 0 and (self._tick // 4) % 2 == 0:
            return
        surface.blit(self.image, self.rect)
        if self.is_focused:
            hx, hy = self.hitbox.center
            pygame.draw.circle(surface, RED, (hx, hy), PLAYER_HITBOX_R + 2, 1)
            pygame.draw.circle(surface, WHITE, (hx, hy), PLAYER_HITBOX_R)
