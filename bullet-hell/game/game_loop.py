import pygame
import math
import random
from game import state as S
from game.constants import (
    WIDTH, HEIGHT, FPS, TITLE, PLAY_TOP,
    BLACK, NEAR_BLACK, WHITE, CYAN, RED, GRAY, DIM_GRAY, YELLOW,
    SCORE_SCOUT, SCORE_ZIGZAG, SCORE_HOVER, SCORE_TANK, SCORE_SWARMER,
    SCORE_BOSS_PHASE, POWER_PER_CRYSTAL,
)
from game.entities.player import Player
from game.entities.bullet import Bullet
from game.entities.particle import ParticleSystem
from game.systems.wave_manager import WaveManager
from game.systems.collision import (
    check_player_hit, check_graze,
    check_player_bullets_vs_enemies, check_player_bullets_vs_boss,
    check_powerup_pickup,
)
from game.systems.scoring import Scoring
from game.ui.hud import HUD
from game.ui.menu import MenuScreen
from game.ui.game_over import GameOverScreen
from game.narrative.dialogue import DialogueBox
from game.narrative.narrator import NarratorSystem


# ── PowerUp sprite ────────────────────────────────────────────────────────────

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, CYAN,  [(6, 0), (12, 6), (6, 12), (0, 6)])
        pygame.draw.polygon(self.image, WHITE, [(6, 0), (12, 6), (6, 12), (0, 6)], 1)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.pos  = pygame.math.Vector2(x, y)

    def update(self):
        self.pos.y += 1.2
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.pos.y > HEIGHT + 30:
            self.kill()


# ── Starfield ─────────────────────────────────────────────────────────────────

class _StarLayer:
    def __init__(self, count, speed, size, bright):
        self.speed = speed
        self.size = size
        self.bright = bright
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT))
                      for _ in range(count)]

    def update(self):
        self.stars = [
            (x, (y + self.speed) % HEIGHT) for x, y in self.stars
        ]

    def draw(self, surface):
        c = (self.bright, self.bright, min(255, self.bright + 25))
        for x, y in self.stars:
            pygame.draw.circle(surface, c, (int(x), int(y)), self.size)


# ── Main Game class ───────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()

        self._stars = [
            _StarLayer(50, 0.4, 1, 70),
            _StarLayer(30, 1.0, 1, 110),
            _StarLayer(12, 2.2, 2, 160),
        ]

        self.menu_screen    = MenuScreen()
        self.game_over_screen = GameOverScreen()
        self.hud            = HUD()
        self.dialogue_box   = DialogueBox()
        self.narrator       = NarratorSystem(self.dialogue_box)

        self._game_state    = S.MENU
        self._first_menu    = True
        self._paused_once   = False
        self._focused_once  = False
        self._ending_done   = False
        self._menu_return   = False

        self._init_play_objects()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_play_objects(self):
        self.player         = Player()
        self.all_sprites    = pygame.sprite.Group()
        self.enemies        = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets  = pygame.sprite.Group()
        self.powerups       = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.particles      = ParticleSystem()
        self.wave_manager   = WaveManager(self.player)
        self.scoring        = Scoring()
        self.hud            = HUD()
        self.boss           = None
        self._wave          = 0
        self._between_waves = False
        self._next_wave_timer = 0
        self._game_over_new_hi = False

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()

    # ── Events ────────────────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if self._game_state == S.MENU:
                result = self.menu_screen.handle_event(event)
                if result == "start":
                    self._start_game()
                elif result == "quit":
                    self._quit()

            elif self._game_state == S.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._game_state = S.PAUSED
                        if not self._paused_once:
                            self._paused_once = True
                            self.narrator.on_pause()
                    elif event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
                        if self.dialogue_box.active:
                            self.dialogue_box.skip()

            elif self._game_state == S.PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._game_state = S.PLAYING

            elif self._game_state == S.GAME_OVER:
                result = self.game_over_screen.handle_event(event)
                if result == "retry":
                    self._start_game()
                elif result == "menu":
                    self._menu_return = True
                    self._game_state = S.MENU
                    self.menu_screen.set_return(True)

            elif self._game_state == S.ENDING:
                if event.type == pygame.KEYDOWN:
                    if self.dialogue_box.active:
                        self.dialogue_box.skip()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()

    def _quit(self):
        self.scoring.save()
        pygame.quit()
        raise SystemExit

    # ── Start / Restart ───────────────────────────────────────────────────────

    def _start_game(self):
        self._init_play_objects()
        self._game_state = S.PLAYING
        self._wave = 0
        self._between_waves = False
        self._next_wave_timer = 0
        self._paused_once = False
        self._focused_once = False
        self._ending_done = False
        self.narrator = NarratorSystem(self.dialogue_box)
        self.dialogue_box.active = False
        self._advance_wave()

    def _advance_wave(self):
        self._wave += 1
        self.wave_manager.start_wave(self._wave, self.enemies, self.all_sprites)
        self.narrator.on_wave_start(self._wave)
        self._between_waves = False

        # If boss wave, spawn boss immediately after a short delay
        if self.wave_manager.is_pending_boss():
            self._next_wave_timer = 90  # 1.5s dramatic pause
            self._between_waves = True

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self):
        if self._game_state == S.MENU:
            self.menu_screen.update()
            self.dialogue_box.update()

        elif self._game_state == S.PLAYING:
            self._update_playing()

        elif self._game_state == S.GAME_OVER:
            self.game_over_screen.update()

        elif self._game_state == S.ENDING:
            self._update_ending()

    def _update_playing(self):
        keys = pygame.key.get_pressed()

        # Detect first focus use
        focused = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if focused and not self._focused_once:
            self._focused_once = True
            self.narrator.on_focus_first_use()

        # Player
        new_player_bullets: list[Bullet] = []
        self.player.update(keys, new_player_bullets)
        for b in new_player_bullets:
            self.player_bullets.add(b)
            self.all_sprites.add(b)

        # Starfield
        for layer in self._stars:
            layer.update()

        # Between-wave timer (boss spawn delay)
        if self._between_waves:
            self._next_wave_timer -= 1
            if self._next_wave_timer <= 0:
                if self.wave_manager.is_pending_boss():
                    self.boss = self.wave_manager.spawn_boss(self.all_sprites)
                    self.narrator.on_boss_spawn(self.boss.boss_index)
                self._between_waves = False
            return  # don't process enemies during dramatic pause

        # Wave manager spawning
        self.wave_manager.update(self.enemies, self.all_sprites)

        # Enemies + boss
        new_enemy_bullets: list[Bullet] = []

        if self.boss:
            old_phase = self.boss.phase
            self.boss.update(new_enemy_bullets)
            if self.boss.phase != old_phase:
                self.narrator.on_boss_phase(self.boss.boss_index)
        else:
            for enemy in list(self.enemies):
                enemy.update(self.player.pos, new_enemy_bullets)

        for b in new_enemy_bullets:
            self.enemy_bullets.add(b)
            self.all_sprites.add(b)

        # Bullets move
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.powerups.update()
        self.particles.update()

        # ── Collisions ────────────────────────────────────────────────────────

        # Player bullets vs enemies
        hits = check_player_bullets_vs_enemies(self.player_bullets, self.enemies)
        for enemy, bullet in hits:
            self.particles.add_hit_flash(bullet.pos.x, bullet.pos.y, (255, 180, 80))
            if enemy.take_damage(bullet.damage):
                self._on_enemy_death(enemy)

        # Player bullets vs boss
        if self.boss:
            dmg = check_player_bullets_vs_boss(self.player_bullets, self.boss)
            if dmg:
                self.particles.add_hit_flash(self.boss.pos.x, self.boss.pos.y, (255, 220, 100))
                if self.boss.take_damage(dmg):
                    self._on_boss_death()

        # Enemy bullets vs player
        if check_player_hit(self.player, self.enemy_bullets):
            if self.player.take_hit():
                self._on_player_death()
            else:
                self.particles.add_hit_flash(self.player.pos.x, self.player.pos.y, RED)

        # Graze
        grazes = check_graze(self.player, self.enemy_bullets)
        for _ in range(grazes):
            self.scoring.graze()

        # Powerups
        collected = check_powerup_pickup(self.player, self.powerups)
        for pu in collected:
            self.player.add_power(POWER_PER_CRYSTAL)
            self.scoring.add(50)

        # Dialogue tick
        self.dialogue_box.update()

        # New high score notification
        if self.scoring.is_new_high() and not self._game_over_new_hi:
            self._game_over_new_hi = True
            self.narrator.on_new_high_score()

        # Wave clear check
        if not self.boss and self.wave_manager.is_wave_clear(self.enemies):
            self._on_wave_clear()

    def _on_enemy_death(self, enemy):
        self.scoring.add(enemy.SCORE)
        self.particles.add_explosion(enemy.pos.x, enemy.pos.y, enemy.COLOR)
        if enemy.should_drop_power():
            pu = PowerUp(enemy.pos.x, enemy.pos.y)
            self.powerups.add(pu)
            self.all_sprites.add(pu)
        enemy.kill()

    def _on_boss_death(self):
        self.scoring.add(SCORE_BOSS_PHASE * (self.boss.phase + 1))
        self.particles.add_shockwave(self.boss.pos.x, self.boss.pos.y, self.boss.base_color)
        self.particles.add_explosion(self.boss.pos.x, self.boss.pos.y, self.boss.base_color, count=60)
        # Drop several power pickups
        for _ in range(5):
            ox = self.boss.pos.x + random.uniform(-40, 40)
            oy = self.boss.pos.y + random.uniform(-20, 20)
            pu = PowerUp(ox, oy)
            self.powerups.add(pu)
            self.all_sprites.add(pu)

        self.narrator.on_boss_death(self.boss.boss_index)
        self.boss.kill()
        self.boss = None
        self.wave_manager.boss_active = False

        # Clear all enemy bullets (phase clear)
        self.enemy_bullets.empty()

        # Check if this was the final boss (wave 30)
        if self._wave >= 30:
            self._game_state = S.ENDING
            self.narrator.reset_ending()
            return

        self._between_waves = True
        self._next_wave_timer = 80
        self._advance_wave()

    def _on_player_death(self):
        self.particles.add_death_ring(self.player.pos.x, self.player.pos.y, CYAN)
        self.particles.add_explosion(self.player.pos.x, self.player.pos.y, WHITE, count=30)
        self.narrator.on_player_death()
        if self.player.lives <= 0:
            self._game_over()

    def _on_wave_clear(self):
        self._between_waves = True
        self._next_wave_timer = 65
        self._advance_wave()

    def _game_over(self):
        self.scoring.save()
        self._game_over_new_hi = self.scoring.is_new_high()
        self.game_over_screen.reset()
        self._game_state = S.GAME_OVER

    def _update_ending(self):
        self.dialogue_box.update()
        for layer in self._stars:
            layer.update()
        done = self.narrator.on_ending_tick()
        if done:
            self._menu_return = True
            self._game_state = S.MENU
            self.menu_screen.set_return(True)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self):
        if self._game_state == S.MENU:
            self.menu_screen.draw(self.screen, self.scoring.high_score)
            self.dialogue_box.draw(self.screen)

        elif self._game_state in (S.PLAYING, S.PAUSED):
            self._draw_game()
            if self._game_state == S.PAUSED:
                self._draw_pause_overlay()

        elif self._game_state == S.GAME_OVER:
            self._draw_game()
            self.game_over_screen.draw(
                self.screen, self.scoring.score, self._wave,
                self.scoring.high_score, self._game_over_new_hi,
            )

        elif self._game_state == S.ENDING:
            self._draw_ending()

    def _draw_game(self):
        self.screen.fill(BLACK)

        # Starfield
        for layer in self._stars:
            layer.draw(self.screen)

        # Powerups
        self.powerups.draw(self.screen)

        # Enemies
        for enemy in self.enemies:
            self.screen.blit(enemy.image, enemy.rect)
            if enemy.MAX_HP > 1:
                self._draw_enemy_hp(enemy)

        # Boss
        if self.boss:
            self.boss.draw(self.screen)

        # Player bullets
        self.player_bullets.draw(self.screen)

        # Enemy bullets
        self.enemy_bullets.draw(self.screen)

        # Player
        self.player.draw(self.screen)

        # Particles
        self.particles.draw(self.screen)

        # HUD (topmost)
        self.hud.draw(
            self.screen,
            self.scoring.score,
            self.scoring.high_score,
            self.player.lives,
            self.player.power_tier,
            self.player.power,
            self._wave,
            boss_active=self.boss is not None,
            is_focused=self.player.is_focused,
        )

        # Dialogue
        self.dialogue_box.draw(self.screen)

    def _draw_enemy_hp(self, enemy):
        bar_w = enemy.rect.width
        bx = enemy.rect.x
        by = enemy.rect.bottom + 2
        frac = enemy.hp / enemy.MAX_HP
        pygame.draw.rect(self.screen, (80, 0, 0),   (bx, by, bar_w, 3))
        pygame.draw.rect(self.screen, RED,           (bx, by, int(bar_w * frac), 3))

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont("monospace", 28, bold=True)
        t = font.render("PAUSED", True, WHITE)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 14))
        small = pygame.font.SysFont("monospace", 13)
        sub = small.render("ESC to resume", True, GRAY)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 22))

    def _draw_ending(self):
        self.screen.fill(BLACK)
        for layer in self._stars:
            layer.draw(self.screen)
        self.dialogue_box.draw(self.screen)
