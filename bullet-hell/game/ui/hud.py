import pygame
from game.constants import WIDTH, PLAY_TOP, WHITE, CYAN, RED, GRAY, DIM_GRAY, BLACK, YELLOW


class HUD:
    def __init__(self):
        self.font_big  = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_sm   = pygame.font.SysFont("monospace", 11)
        self._ship_img = self._make_ship()

    def _make_ship(self):
        img = pygame.Surface((14, 18), pygame.SRCALPHA)
        pts = [(7, 0), (1, 17), (7, 12), (13, 17)]
        pygame.draw.polygon(img, WHITE, pts)
        return img

    def draw(self, surface, score, high_score, lives, power_tier, power,
             wave, boss_active=False, is_focused=False):
        # HUD background bar
        bar = pygame.Surface((WIDTH, PLAY_TOP), pygame.SRCALPHA)
        bar.fill((5, 5, 20, 200))
        surface.blit(bar, (0, 0))
        pygame.draw.line(surface, CYAN, (0, PLAY_TOP - 1), (WIDTH, PLAY_TOP - 1), 1)

        # Score (left)
        sc_text = self.font_big.render(f"{score:>08d}", True, WHITE)
        surface.blit(sc_text, (8, 5))

        # High score (center-ish)
        hi_label = self.font_sm.render("HI", True, GRAY)
        hi_val   = self.font_sm.render(f"{high_score:>08d}", True, YELLOW)
        surface.blit(hi_label, (WIDTH // 2 - 54, 8))
        surface.blit(hi_val,   (WIDTH // 2 - 32, 8))

        # Wave (right)
        stage_text = self.font_sm.render(f"WAVE {wave:02d}", True, CYAN)
        surface.blit(stage_text, (WIDTH - 70, 8))

        # Lives (bottom-left of HUD row, actually draw row 2)
        for i in range(max(0, lives)):
            surface.blit(self._ship_img, (8 + i * 18, PLAY_TOP - 20))

        # Power bar
        self._draw_power(surface, power_tier, power)

        # Focus indicator
        if is_focused:
            f_surf = self.font_sm.render("FOCUS", True, RED)
            fx = WIDTH // 2 - f_surf.get_width() // 2
            surface.blit(f_surf, (fx, PLAY_TOP - 18))

    def _draw_power(self, surface, tier, raw_power):
        from game.constants import POWER_TIER_THRESHOLDS
        bar_w = 80
        bx = WIDTH - bar_w - 8
        by = PLAY_TOP - 18
        bh = 8

        max_p = POWER_TIER_THRESHOLDS[-1]
        fill = min(bar_w, int(bar_w * raw_power / max_p))

        pygame.draw.rect(surface, DIM_GRAY, (bx, by, bar_w, bh))
        color = [GRAY, CYAN, (80, 220, 255), YELLOW, (255, 200, 0)][min(tier, 4)]
        pygame.draw.rect(surface, color, (bx, by, fill, bh))
        pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bh), 1)

        p_label = pygame.font.SysFont("monospace", 10).render(f"PWR", True, GRAY)
        surface.blit(p_label, (bx - 28, by))
