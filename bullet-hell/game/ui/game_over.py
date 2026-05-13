import pygame
import math
from game.constants import WIDTH, HEIGHT, WHITE, CYAN, RED, GRAY, DIM_GRAY, BLACK, YELLOW


class GameOverScreen:
    def __init__(self):
        self.font_big  = pygame.font.SysFont("monospace", 40, bold=True)
        self.font_med  = pygame.font.SysFont("monospace", 18, bold=True)
        self.font_sm   = pygame.font.SysFont("monospace", 13)
        self.font_xs   = pygame.font.SysFont("monospace", 11)
        self._tick     = 0
        self._alpha    = 0
        self._overlay  = pygame.Surface((WIDTH, HEIGHT))
        self._overlay.fill(BLACK)

    def reset(self):
        self._tick  = 0
        self._alpha = 0

    def handle_event(self, event) -> str | None:
        """Return 'retry' or 'menu', or None."""
        if self._alpha < 200:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return "retry"
            if event.key == pygame.K_ESCAPE:
                return "menu"
        return None

    def update(self):
        self._tick += 1
        self._alpha = min(240, self._alpha + 4)

    def draw(self, surface, score, wave, high_score, is_new_hi: bool):
        self._overlay.set_alpha(self._alpha)
        surface.blit(self._overlay, (0, 0))

        if self._alpha < 60:
            return

        osc = math.sin(self._tick * 0.05) * 4

        # "GAME OVER"
        go = self.font_big.render("GAME OVER", True, RED)
        surface.blit(go, (WIDTH // 2 - go.get_width() // 2, int(140 + osc)))

        if is_new_hi:
            nh = self.font_med.render("* NEW HIGH SCORE *", True, YELLOW)
            surface.blit(nh, (WIDTH // 2 - nh.get_width() // 2, 210))

        # Stats
        sc = self.font_med.render(f"SCORE    {score:>08d}", True, WHITE)
        wv = self.font_med.render(f"WAVE     {wave:>02d}", True, WHITE)
        hi = self.font_med.render(f"HI-SCORE {high_score:>08d}", True, CYAN)
        y = 270
        for t in [sc, wv, hi]:
            surface.blit(t, (WIDTH // 2 - t.get_width() // 2, y))
            y += 30

        # Prompt (blink)
        if self._tick > 60:
            tick_b = self._tick // 28
            if tick_b % 2 == 0:
                r = self.font_sm.render("[ R ]  RETRY", True, WHITE)
                m = self.font_sm.render("[ ESC ]  MAIN MENU", True, GRAY)
                surface.blit(r, (WIDTH // 2 - r.get_width() // 2, 390))
                surface.blit(m, (WIDTH // 2 - m.get_width() // 2, 415))

        # Fourth-wall line
        fw = self.font_xs.render("You'll try again. He won't remember.", True, DIM_GRAY)
        surface.blit(fw, (WIDTH // 2 - fw.get_width() // 2, HEIGHT - 50))
