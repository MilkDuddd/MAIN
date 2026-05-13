from game.narrative.story_data import (
    LINES, WAVE_LINES, BOSS_SPAWN_LINES, BOSS_PHASE_LINES, BOSS_DEATH_LINES,
    ENDING_SEQUENCE,
)
from game.narrative.dialogue import DialogueBox


class NarratorSystem:
    def __init__(self, dialogue_box: DialogueBox):
        self.box = dialogue_box
        self._deaths = 0
        self._paused_once = False
        self._focused_once = False
        self._visited_menu = False
        self._ending_idx = 0
        self._boss_phase_indices: dict[int, int] = {}

    def _say(self, key: str):
        if key not in LINES:
            return
        speaker, text = LINES[key]
        self.box.show(speaker, text)

    # ── Trigger points called by game_loop ────────────────────────────────────

    def on_menu(self, first_time: bool):
        if first_time and not self._visited_menu:
            self._visited_menu = True
            self._say("menu_first_visit")
        elif not first_time:
            self._say("menu_return")

    def on_wave_start(self, wave: int):
        key = WAVE_LINES.get(wave)
        if key:
            self._say(key)

    def on_boss_spawn(self, boss_index: int):
        key = BOSS_SPAWN_LINES.get(boss_index)
        if key:
            self._say(key)

    def on_boss_phase(self, boss_index: int):
        lines = BOSS_PHASE_LINES.get(boss_index, [])
        if not lines:
            return
        idx = self._boss_phase_indices.get(boss_index, 0)
        self._say(lines[idx % len(lines)])
        self._boss_phase_indices[boss_index] = idx + 1

    def on_boss_death(self, boss_index: int):
        key = BOSS_DEATH_LINES.get(boss_index)
        if key:
            self._say(key)

    def on_player_death(self):
        self._deaths += 1
        if self._deaths == 1:
            self._say("death_1")
        elif self._deaths == 2:
            self._say("death_2")
        elif self._deaths == 3:
            self._say("death_3")
        else:
            self._say("death_many")

    def on_pause(self):
        if not self._paused_once:
            self._paused_once = True
            self._say("first_pause")

    def on_focus_first_use(self):
        if not self._focused_once:
            self._focused_once = True
            self._say("focus_first_use")

    def on_new_high_score(self):
        self._say("new_high_score")

    def on_ending_tick(self) -> bool:
        """Advance ending sequence. Returns True when fully done."""
        if not self.box.active and self._ending_idx < len(ENDING_SEQUENCE):
            key = ENDING_SEQUENCE[self._ending_idx]
            self._say(key)
            self._ending_idx += 1
            return False
        return self._ending_idx >= len(ENDING_SEQUENCE) and not self.box.active

    def reset_ending(self):
        self._ending_idx = 0
