import pygame
import math
import random
from game.constants import WIDTH, HEIGHT, WHITE, CYAN, RED, GRAY, DIM_GRAY, BLACK, NEAR_BLACK


class Star:
    __slots__ = ['x', 'y', 'speed', 'size', 'bright']

    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.3, 2.0)
        self.size = 1 if self.speed < 0.8 else (2 if self.speed < 1.5 else 3)
        self.bright = int(80 + self.speed * 60)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)


class MenuScreen:
    OPTS = ["START", "QUIT"]

    def __init__(self):
        self.font_title  = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_sub    = pygame.font.SysFont("monospace", 14, bold=True)
        self.font_opt    = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_sm     = pygame.font.SysFont("monospace", 11)
        self.cursor      = 0
        self._tick       = 0
        self._stars      = [Star() for _ in range(90)]
        self._is_return  = False

    def set_return(self, val: bool):
        self._is_return = val

    def handle_event(self, event) -> str | None:
        """Return 'start' or 'quit', or None."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.cursor = (self.cursor - 1) % len(self.OPTS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.cursor = (self.cursor + 1) % len(self.OPTS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                return self.OPTS[self.cursor].lower()
        return None

    def update(self):
        self._tick += 1
        for s in self._stars:
            s.update()

    def draw(self, surface, high_score: int):
        surface.fill(BLACK)

        # Starfield
        for s in self._stars:
            c = (s.bright, s.bright, min(255, s.bright + 30))
            pygame.draw.circle(surface, c, (int(s.x), int(s.y)), s.size)

        # Title with vertical oscillation
        osc = math.sin(self._tick * 0.04) * 6
        title = self.font_title.render("VOID", True, WHITE)
        tx = WIDTH // 2 - title.get_width() // 2
        ty = int(160 + osc)
        surface.blit(title, (tx, ty))

        # Subtitle
        sub = self.font_sub.render("A BULLET HELL", True, CYAN)
        surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, ty + 58))

        # Hi score
        hi = self.font_sm.render(f"HI-SCORE  {high_score:>08d}", True, (180, 180, 120))
        surface.blit(hi, (WIDTH // 2 - hi.get_width() // 2, HEIGHT // 2 - 30))

        # Menu options
        for i, opt in enumerate(self.OPTS):
            selected = (i == self.cursor)
            color = CYAN if selected else GRAY
            prefix = "> " if selected else "  "
            ts = self.font_opt.render(prefix + opt, True, color)
            surface.blit(ts, (WIDTH // 2 - ts.get_width() // 2, HEIGHT // 2 + 20 + i * 42))

        # Controls hint
        ctrl = self.font_sm.render("ARROWS/WASD  Z/SPACE=shoot  SHIFT=focus  ESC=pause", True, DIM_GRAY)
        surface.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, HEIGHT - 40))

        # Blink prompt if return visit
        if self._is_return:
            t = self._tick // 30
            if t % 2 == 0:
                msg = self.font_sm.render("IT'S OVER. WHY ARE YOU STILL HERE?", True, (160, 80, 80))
                surface.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 60))
