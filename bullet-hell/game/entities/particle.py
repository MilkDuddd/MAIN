import pygame
import random
import math


class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'size', 'lifetime', 'age', 'alive']

    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = float(size)
        self.lifetime = lifetime
        self.age = 0
        self.alive = True

    def update(self):
        self.age += 1
        if self.age >= self.lifetime:
            self.alive = False
            return
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.91
        self.vy *= 0.91

    def draw(self, surface):
        if not self.alive:
            return
        t = self.age / self.lifetime
        alpha = int(255 * (1.0 - t))
        cur_size = max(1, int(self.size * (1.0 - t * 0.6)))
        s = cur_size * 2 + 2
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (s // 2, s // 2), cur_size)
        surface.blit(surf, (int(self.x) - s // 2, int(self.y) - s // 2))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def add_explosion(self, x, y, color, count=22, speed_range=(2, 8)):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(*speed_range)
            size = random.uniform(2, 5)
            lt = random.randint(20, 45)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, color, size, lt)
            )

    def add_hit_flash(self, x, y, color, count=8):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(1, 4)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, color, 2, 14)
            )

    def add_death_ring(self, x, y, color, count=16):
        for i in range(count):
            angle = (math.tau / count) * i
            spd = random.uniform(3, 6)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, color, 3, 30)
            )

    def add_shockwave(self, x, y, color):
        for i in range(24):
            angle = (math.tau / 24) * i
            spd = random.uniform(5, 10)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, color, 4, 20)
            )

    def update(self):
        live = []
        for p in self.particles:
            p.update()
            if p.alive:
                live.append(p)
        self.particles = live

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()
