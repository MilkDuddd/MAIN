import random
import pygame
from game.constants import WIDTH, PLAY_TOP, BOSS_EVERY
from game.entities.enemy import ScoutEnemy, ZigzagEnemy, HoverEnemy, TankEnemy, SwarmerEnemy
from game.entities.boss import Boss


def compute_difficulty(wave: int) -> float:
    """0.0 at wave 1, asymptotically approaches 1.0. ~0.5 at wave 20."""
    return 1.0 - 1.0 / (1.0 + wave * 0.045)


class WaveManager:
    def __init__(self, player_ref):
        self.wave = 0
        self.player_ref = player_ref
        self._spawn_queue: list[dict] = []
        self._spawn_timer = 0
        self._wave_delay = 0      # countdown between waves
        self.boss_active = False
        self.boss_index = 0
        self._pending_boss_spawn = False

    def start_wave(self, wave_num, enemies_group, all_sprites):
        self.wave = wave_num
        diff = compute_difficulty(wave_num)

        if wave_num % BOSS_EVERY == 0:
            self._pending_boss_spawn = True
            self._spawn_queue = []
            self._spawn_timer = 0
            return None  # boss spawned separately by game_loop

        # Build spawn queue
        self._spawn_queue = self._build_queue(wave_num, diff)
        self._spawn_timer = 0
        return None

    def _build_queue(self, wave: int, diff: float) -> list[dict]:
        queue = []
        interval = max(12, 40 - wave)  # frames between spawns, gets faster

        # Determine enemy mix
        scout_n   = max(2, 4 + wave // 2)
        zigzag_n  = max(0, (wave - 2) // 2) if wave >= 3 else 0
        hover_n   = max(0, (wave - 4) // 3) if wave >= 5 else 0
        tank_n    = max(0, (wave - 7) // 4) if wave >= 8 else 0
        swarmer_n = max(0, (wave - 3) // 2) if wave >= 4 else 0

        # Cap total
        total = min(20, scout_n + zigzag_n + hover_n + tank_n + swarmer_n)

        pool = (
            [ScoutEnemy]   * scout_n +
            [ZigzagEnemy]  * zigzag_n +
            [HoverEnemy]   * hover_n +
            [TankEnemy]    * tank_n +
            [SwarmerEnemy] * swarmer_n
        )[:total]
        random.shuffle(pool)

        delay = 0
        for cls in pool:
            x = random.randint(30, WIDTH - 30)
            y = PLAY_TOP - 20
            queue.append({"cls": cls, "x": x, "y": y, "delay": delay, "diff": diff})
            delay += interval

        return queue

    def update(self, enemies_group, all_sprites) -> list:
        """Tick spawner. Returns newly spawned enemies."""
        spawned = []
        if not self._spawn_queue:
            return spawned

        self._spawn_timer += 1
        remaining = []
        for entry in self._spawn_queue:
            if self._spawn_timer >= entry["delay"]:
                e = entry["cls"](entry["x"], entry["y"], entry["diff"])
                enemies_group.add(e)
                all_sprites.add(e)
                spawned.append(e)
            else:
                remaining.append(entry)
        self._spawn_queue = remaining
        return spawned

    def spawn_boss(self, all_sprites) -> Boss:
        diff = compute_difficulty(self.wave)
        idx = self.boss_index
        self.boss_index = min(self.boss_index + 1, 5)
        boss = Boss(idx, diff, self.player_ref)
        all_sprites.add(boss)
        self.boss_active = True
        self._pending_boss_spawn = False
        return boss

    def is_pending_boss(self) -> bool:
        return self._pending_boss_spawn

    def is_wave_clear(self, enemies_group) -> bool:
        return len(self._spawn_queue) == 0 and len(enemies_group) == 0

    def next_wave(self):
        self._wave_delay = 70

    def tick_delay(self) -> bool:
        """Returns True when delay has elapsed."""
        if self._wave_delay > 0:
            self._wave_delay -= 1
            return self._wave_delay == 0
        return False

    def has_delay(self) -> bool:
        return self._wave_delay > 0
