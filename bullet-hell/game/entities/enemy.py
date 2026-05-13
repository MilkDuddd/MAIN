import pygame
import math
import random
from game.constants import (
    WIDTH, HEIGHT, PLAY_TOP,
    RED, ORANGE, YELLOW, PURPLE, CYAN, WHITE, GREEN, BLUE, PINK,
    SCORE_SCOUT, SCORE_ZIGZAG, SCORE_HOVER, SCORE_TANK, SCORE_SWARMER,
    POWER_DROP_CHANCE, BULLET_BASE_SPEED,
)
from game.entities.bullet import Bullet


class Enemy(pygame.sprite.Sprite):
    SCORE = 0
    COLOR = RED
    SIZE  = 12
    MAX_HP = 1

    def __init__(self, x, y, difficulty=0.0):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.difficulty = max(0.0, difficulty)
        self.hp = self.MAX_HP
        self.shoot_timer = random.randint(20, 80)
        self.shoot_interval = max(25, 110 - int(self.difficulty * 75))
        self._tick = 0
        self.start_x = float(x)

        self.image = self._build_image()
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def _build_image(self):
        s = self.SIZE * 2 + 6
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        self._draw_shape(surf, s)
        return surf

    def _draw_shape(self, surf, s):
        pygame.draw.circle(surf, self.COLOR, (s // 2, s // 2), self.SIZE)

    def _bullet_speed(self):
        return BULLET_BASE_SPEED + BULLET_BASE_SPEED * self.difficulty * 4.5

    def update(self, player_pos, new_bullets):
        self._tick += 1
        self._move()
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval
            new_bullets.extend(self._shoot(player_pos))

        if self.pos.y > HEIGHT + 100:
            self.kill()

    def _move(self):
        self.pos.y += 1.6 + self.difficulty * 2.0

    def _shoot(self, player_pos):
        return []

    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0

    def should_drop_power(self):
        return random.random() < POWER_DROP_CHANCE


class ScoutEnemy(Enemy):
    COLOR  = (230, 60, 60)
    SIZE   = 10
    MAX_HP = 1
    SCORE  = SCORE_SCOUT

    def _draw_shape(self, surf, s):
        c = s // 2
        n = self.SIZE
        pts = [(c, c - n), (c + n, c), (c, c + n), (c - n, c)]
        pygame.draw.polygon(surf, self.COLOR, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)
        pygame.draw.circle(surf, (255, 150, 150), (c, c), 3)

    def _move(self):
        self.pos.y += 1.8 + self.difficulty * 2.2

    def _shoot(self, player_pos):
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        dist = max(1.0, math.hypot(dx, dy))
        spd = self._bullet_speed()
        return [Bullet(self.pos.x, self.pos.y, dx / dist * spd, dy / dist * spd,
                       radius=4, color=(255, 100, 100), damage=1)]


class ZigzagEnemy(Enemy):
    COLOR  = ORANGE
    SIZE   = 11
    MAX_HP = 2
    SCORE  = SCORE_ZIGZAG

    def _draw_shape(self, surf, s):
        c = s // 2
        n = self.SIZE
        pts = [(c, c - n), (c + n - 2, c - 2), (c + n - 4, c + n - 2),
               (c - n + 4, c + n - 2), (c - n + 2, c - 2)]
        pygame.draw.polygon(surf, self.COLOR, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)

    def _move(self):
        self.pos.y += 1.3 + self.difficulty * 1.8
        self.pos.x = self.start_x + math.sin(self._tick * 0.055) * 65
        self.pos.x = max(20, min(WIDTH - 20, self.pos.x))

    def _shoot(self, player_pos):
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        base_angle = math.atan2(dy, dx)
        spd = self._bullet_speed()
        n = 3 + int(self.difficulty * 4)
        spread = math.radians(14)
        bullets = []
        for i in range(n):
            a = base_angle + spread * (i - n // 2)
            bullets.append(Bullet(self.pos.x, self.pos.y,
                                   math.cos(a) * spd, math.sin(a) * spd,
                                   radius=4, color=ORANGE, damage=1))
        return bullets


class HoverEnemy(Enemy):
    COLOR  = PURPLE
    SIZE   = 14
    MAX_HP = 5
    SCORE  = SCORE_HOVER

    def __init__(self, x, y, difficulty=0.0):
        super().__init__(x, y, difficulty)
        self.hover_y = random.randint(int(PLAY_TOP + 80), int(HEIGHT // 2 - 60))
        self.hovering = False
        self.hover_tick = 0

    def _draw_shape(self, surf, s):
        c = s // 2
        n = self.SIZE
        pts = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            pts.append((c + math.cos(angle) * n, c + math.sin(angle) * n))
        pygame.draw.polygon(surf, self.COLOR, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)
        pygame.draw.circle(surf, CYAN, (c, c), 4)

    def _move(self):
        if not self.hovering:
            if self.pos.y < self.hover_y:
                self.pos.y += 2.2 + self.difficulty
            else:
                self.hovering = True
        else:
            self.hover_tick += 1
            self.pos.x = self.start_x + math.sin(self.hover_tick * 0.022) * 50
            self.pos.x = max(20, min(WIDTH - 20, self.pos.x))

    def _shoot(self, player_pos):
        n = 8 + int(self.difficulty * 8)
        spd = self._bullet_speed()
        bullets = []
        for i in range(n):
            angle = (math.tau / n) * i
            bullets.append(Bullet(self.pos.x, self.pos.y,
                                   math.cos(angle) * spd, math.sin(angle) * spd,
                                   radius=5, color=(190, 80, 255), damage=1))
        return bullets


class TankEnemy(Enemy):
    COLOR  = (100, 100, 210)
    SIZE   = 18
    MAX_HP = 10
    SCORE  = SCORE_TANK

    def _draw_shape(self, surf, s):
        c = s // 2
        n = self.SIZE
        pygame.draw.rect(surf, self.COLOR, (c - n, c - n, n * 2, n * 2))
        pygame.draw.rect(surf, WHITE, (c - n, c - n, n * 2, n * 2), 2)
        pygame.draw.circle(surf, CYAN, (c, c), 6)
        # Armor plating lines
        pygame.draw.line(surf, WHITE, (c - n, c), (c + n, c), 1)

    def _move(self):
        self.pos.y += 0.7 + self.difficulty * 0.6

    def _shoot(self, player_pos):
        n = 12 + int(self.difficulty * 8)
        spd = self._bullet_speed() * 0.85
        offset = (self._tick * 0.08) % math.tau
        bullets = []
        for i in range(n):
            angle = (math.tau / n) * i + offset
            bullets.append(Bullet(self.pos.x, self.pos.y,
                                   math.cos(angle) * spd, math.sin(angle) * spd,
                                   radius=5, color=(130, 130, 255), damage=1))
        return bullets


class SwarmerEnemy(Enemy):
    COLOR  = YELLOW
    SIZE   = 7
    MAX_HP = 1
    SCORE  = SCORE_SWARMER

    def __init__(self, x, y, difficulty=0.0):
        super().__init__(x, y, difficulty)
        self._vx = random.choice([-1, 1]) * random.uniform(0.8, 1.8)

    def _draw_shape(self, surf, s):
        c = s // 2
        pygame.draw.circle(surf, self.COLOR, (c, c), self.SIZE)
        pygame.draw.circle(surf, WHITE, (c, c), self.SIZE, 1)

    def _move(self):
        self.pos.x += self._vx * (1.4 + self.difficulty)
        self.pos.y += 1.6 + self.difficulty * 2.0
        if self.pos.x < 12 or self.pos.x > WIDTH - 12:
            self._vx *= -1

    def _shoot(self, player_pos):
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        dist = max(1.0, math.hypot(dx, dy))
        spd = self._bullet_speed()
        return [Bullet(self.pos.x, self.pos.y,
                       dx / dist * spd + random.uniform(-0.6, 0.6),
                       dy / dist * spd,
                       radius=3, color=YELLOW, damage=1)]
