import pygame
import math
import random
from game.constants import (
    WIDTH, HEIGHT, PLAY_TOP,
    WHITE, RED, CYAN, PURPLE, ORANGE, YELLOW, PINK, BLUE, GREEN,
    BULLET_BASE_SPEED, SCORE_BOSS_PHASE, POWER_DROP_CHANCE,
)
from game.entities.bullet import Bullet, HomingBullet


_BOSS_DATA = [
    # name,                max_hp, num_phases, size, base_color
    ("THE GATEKEEPER",     500,    2,           32,  (200, 60,  60)),
    ("THE MIRROR",         900,    3,           36,  (80,  80, 220)),
    ("THE WOUND",          1400,   3,           38,  (220, 50,  80)),
    ("THE ARCHITECT",      2000,   4,           42,  (60, 200,  80)),
    ("THE LAST DOUBT",     2800,   5,           45,  (220, 160,  0)),
    ("THE DARK",           4500,   6,           50,  (160,  50, 220)),
]

_PHASE_COLORS = [
    (200, 60, 60), (255, 110, 40), (100, 50, 255),
    (50, 200, 200), (255, 50, 50), (220, 220, 255),
]

_PHASE_PATTERNS = [
    ["radial_8",  "aimed_3"],
    ["radial_12", "spiral_2", "aimed_3"],
    ["radial_16", "spiral_4", "aimed_5", "wall"],
    ["radial_20", "spiral_6", "homing",  "wall",  "aimed_5"],
    ["radial_24", "spiral_8", "homing",  "wall_n", "dense"],
    ["radial_32", "spiral_12","homing_d","wall_n", "dense", "chaos"],
]


class Boss(pygame.sprite.Sprite):
    def __init__(self, boss_index, difficulty, player_ref):
        super().__init__()
        idx = min(boss_index, len(_BOSS_DATA) - 1)
        name, base_hp, num_phases, size, color = _BOSS_DATA[idx]

        self.name = name
        self.max_hp = base_hp + int(difficulty * 600)
        self.hp = self.max_hp
        self.size = size
        self.base_color = color
        self.difficulty = difficulty
        self.player_ref = player_ref
        self.boss_index = idx

        self.pos = pygame.math.Vector2(WIDTH // 2, -size - 10)
        self.target_y = PLAY_TOP + size + 50
        self.entering = True

        self.num_phases = num_phases
        self.phase = 0
        # e.g. 2 phases → thresholds [0.5]  3 phases → [0.666, 0.333]
        self.phase_thresholds = [
            1.0 - (i + 1) / num_phases for i in range(num_phases - 1)
        ]
        self._phase_triggered = [False] * len(self.phase_thresholds)

        self.transitioning = False
        self.transition_timer = 0

        self.attack_timer = 0
        self.attack_interval = max(35, 85 - int(difficulty * 42))
        self.pattern_index = 0
        self._tick = 0
        self.move_dir = 1

        self.image = self._make_image(color)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _make_image(self, color):
        s = self.size * 2 + 20
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        c = s // 2
        n = self.size
        # Outer glow
        pygame.draw.circle(surf, (*color[:3], 50), (c, c), n + 6)
        # Body
        pygame.draw.circle(surf, color, (c, c), n)
        pygame.draw.circle(surf, WHITE, (c, c), n, 2)
        # Inner ring
        light = tuple(min(255, v + 50) for v in color[:3])
        pygame.draw.circle(surf, light, (c, c), n // 2)
        pygame.draw.circle(surf, WHITE, (c, c), n // 4)
        # Spikes
        for i in range(8):
            a = (math.tau / 8) * i
            x1 = c + math.cos(a) * (n - 2)
            y1 = c + math.sin(a) * (n - 2)
            x2 = c + math.cos(a) * (n + 10)
            y2 = c + math.sin(a) * (n + 10)
            pygame.draw.line(surf, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)
        return surf

    def update(self, new_bullets):
        self._tick += 1

        if self.entering:
            self.pos.y += 2.5
            if self.pos.y >= self.target_y:
                self.pos.y = self.target_y
                self.entering = False
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            return

        if self.transitioning:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.transitioning = False
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            return

        # Phase check
        hp_frac = self.hp / self.max_hp
        for i, thresh in enumerate(self.phase_thresholds):
            if not self._phase_triggered[i] and hp_frac <= thresh:
                self._phase_triggered[i] = True
                self.phase += 1
                self.pattern_index = 0
                self.attack_timer = 0
                self.transitioning = True
                self.transition_timer = 90
                color = _PHASE_COLORS[min(self.phase, len(_PHASE_COLORS) - 1)]
                self.image = self._make_image(color)
                return

        # Movement
        speed = 1.4 + self.phase * 0.4 + self.difficulty * 0.5
        self.pos.x += speed * self.move_dir
        if self.pos.x > WIDTH - self.size - 20 or self.pos.x < self.size + 20:
            self.move_dir *= -1
        self.pos.y = self.target_y + math.sin(self._tick * 0.02) * 22
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Attack
        self.attack_timer -= 1
        if self.attack_timer <= 0:
            self.attack_timer = self.attack_interval
            patterns = _PHASE_PATTERNS[min(self.phase, len(_PHASE_PATTERNS) - 1)]
            pattern = patterns[self.pattern_index % len(patterns)]
            self.pattern_index += 1
            new_bullets.extend(self._fire(pattern))

    def _fire(self, pattern):
        spd = min(11, BULLET_BASE_SPEED * (1 + self.difficulty * 0.55) + self.phase * 0.4)
        ox, oy = self.pos.x, self.pos.y
        player_pos = self.player_ref.pos if self.player_ref else pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        bullets = []

        if pattern.startswith("radial_"):
            n = int(pattern[7:])
            offset = self._tick * 0.015
            for i in range(n):
                a = (math.tau / n) * i + offset
                bullets.append(Bullet(ox, oy, math.cos(a) * spd, math.sin(a) * spd,
                                       radius=5, color=self._cur_color()))

        elif pattern.startswith("spiral_"):
            arms = int(pattern[7:])
            base_a = math.radians((self._tick * 3) % 360)
            for i in range(arms):
                a = base_a + (math.tau / arms) * i
                bullets.append(Bullet(ox, oy, math.cos(a) * spd, math.sin(a) * spd,
                                       radius=4, color=CYAN))

        elif pattern.startswith("aimed_"):
            n = int(pattern[6:])
            dx = player_pos.x - ox
            dy = player_pos.y - oy
            base_a = math.atan2(dy, dx)
            spread = math.radians(11)
            for i in range(n):
                a = base_a + spread * (i - n // 2)
                bullets.append(Bullet(ox, oy, math.cos(a) * spd * 1.15, math.sin(a) * spd * 1.15,
                                       radius=4, color=ORANGE))

        elif pattern == "wall":
            gap_x = player_pos.x + random.uniform(-35, 35)
            gap_x = max(55, min(WIDTH - 55, gap_x))
            gap_w = max(65, 100 - self.phase * 7)
            for x in range(0, WIDTH + 1, 22):
                if abs(x - gap_x) < gap_w / 2:
                    continue
                bullets.append(Bullet(x, oy + 20, 0, spd * 0.85, radius=4, color=PURPLE))

        elif pattern == "wall_n":
            gap_x = player_pos.x
            gap_w = max(42, 72 - self.phase * 5)
            for x in range(0, WIDTH + 1, 18):
                if abs(x - gap_x) < gap_w / 2:
                    continue
                bullets.append(Bullet(x, oy + 20, 0, spd * 0.9, radius=4, color=(210, 50, 210)))

        elif pattern == "homing":
            for _ in range(3 + self.phase):
                vx = random.uniform(-1.5, 1.5)
                vy = random.uniform(1, 2)
                bullets.append(HomingBullet(ox + random.uniform(-50, 50), oy,
                                             vx, vy, player_ref=self.player_ref,
                                             radius=5, color=YELLOW, turn_rate=0.03))

        elif pattern == "homing_d":
            for _ in range(5 + self.phase):
                vx = random.uniform(-2, 2)
                vy = random.uniform(0.8, 1.8)
                bullets.append(HomingBullet(ox + random.uniform(-70, 70), oy,
                                             vx, vy, player_ref=self.player_ref,
                                             radius=4, color=(255, 210, 0), turn_rate=0.04))

        elif pattern == "dense":
            for _ in range(8 + self.phase * 3):
                a = random.uniform(0, math.tau)
                s2 = spd * random.uniform(0.4, 1.0)
                bullets.append(Bullet(ox + random.uniform(-18, 18),
                                       oy + random.uniform(-5, 14),
                                       math.cos(a) * s2, abs(math.sin(a)) * s2,
                                       radius=3, color=(255, 60, 130)))

        elif pattern == "chaos":
            bullets.extend(self._fire(f"radial_{8 + self.phase * 2}"))
            bullets.extend(self._fire("aimed_3"))
            bullets.extend(self._fire("dense"))

        return bullets

    def _cur_color(self):
        return _PHASE_COLORS[min(self.phase, len(_PHASE_COLORS) - 1)]

    def take_damage(self, amount=1):
        self.hp = max(0, self.hp - amount)
        return self.hp <= 0

    def get_hp_frac(self):
        return self.hp / self.max_hp

    def draw(self, surface):
        if self.transitioning and (self.transition_timer // 4) % 2 == 0:
            return
        surface.blit(self.image, self.rect)

        # Boss HP bar (drawn below the standard HUD bar)
        bar_w = 380
        bar_x = (WIDTH - bar_w) // 2
        bar_y = PLAY_TOP + 8
        bar_h = 10
        pygame.draw.rect(surface, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * self.get_hp_frac())
        color = _PHASE_COLORS[min(self.phase, len(_PHASE_COLORS) - 1)]
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill, bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        font = pygame.font.SysFont("monospace", 11, bold=True)
        surf = font.render(self.name, True, WHITE)
        surface.blit(surf, (bar_x, bar_y + bar_h + 2))
