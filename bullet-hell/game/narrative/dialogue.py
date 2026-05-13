import pygame
from game.constants import WIDTH, HEIGHT, WHITE, CYAN, RED, GRAY, BLACK


class DialogueBox:
    BAR_H = 88
    FONT_SIZE = 14
    CHARS_PER_FRAME = 2

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", self.FONT_SIZE)
        self.label_font = pygame.font.SysFont("monospace", 11, bold=True)
        self.active = False
        self._full = ""
        self._shown = ""
        self._idx = 0
        self._speaker = ""
        self._char_timer = 0
        self._hold = 0
        self._hold_max = 200
        self._done_typing = False

    def show(self, speaker: str, text: str):
        self._speaker = speaker
        self._full = text
        self._shown = ""
        self._idx = 0
        self._char_timer = 0
        self._hold = 0
        self._done_typing = False
        self.active = True

    def skip(self):
        if not self._done_typing:
            self._shown = self._full
            self._idx = len(self._full)
            self._done_typing = True
            self._hold = self._hold_max // 2

    def update(self):
        if not self.active:
            return
        if not self._done_typing:
            self._char_timer += 1
            if self._char_timer >= 1:
                self._char_timer = 0
                for _ in range(self.CHARS_PER_FRAME):
                    if self._idx < len(self._full):
                        self._shown += self._full[self._idx]
                        self._idx += 1
                if self._idx >= len(self._full):
                    self._done_typing = True
        else:
            self._hold += 1
            if self._hold >= self._hold_max:
                self.active = False

    def draw(self, surface):
        if not self.active:
            return
        y = HEIGHT - self.BAR_H

        # Background panel
        panel = pygame.Surface((WIDTH, self.BAR_H), pygame.SRCALPHA)
        panel.fill((4, 4, 18, 215))
        surface.blit(panel, (0, y))
        pygame.draw.line(surface, CYAN, (0, y), (WIDTH, y), 1)

        # Speaker label color
        sp = self._speaker
        if sp == "[???]":
            lc = (190, 160, 255)
        elif sp == "[HIM]":
            lc = CYAN
        elif "ENEMY" in sp:
            lc = (255, 90, 90)
        else:
            lc = (150, 150, 170)

        label = self.label_font.render(sp, True, lc)
        surface.blit(label, (12, y + 7))

        # Body text
        lines = self._wrap(self._shown, 50)
        text_color = WHITE if sp == "[HIM]" else (215, 215, 235)
        for i, line in enumerate(lines[:3]):
            ts = self.font.render(line, True, text_color)
            surface.blit(ts, (12, y + 26 + i * 18))

        # Blinking cursor while typing
        if not self._done_typing:
            t = pygame.time.get_ticks() // 280
            if t % 2 == 0:
                last = lines[-1] if lines else ""
                cx = 12 + len(last) * 8
                ci = min(len(lines) - 1, 2)
                cy = y + 26 + ci * 18
                pygame.draw.rect(surface, WHITE, (cx, cy + 1, 7, 13))

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + (1 if cur else 0) <= width:
                cur = (cur + " " + w).strip()
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or [""]
