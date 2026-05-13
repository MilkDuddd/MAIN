import pygame
import math
from game.constants import PLAYER_HITBOX_R, GRAZE_RADIUS


def check_player_hit(player, enemy_bullets):
    """Return True if player is hit by any enemy bullet (uses real hitbox, not sprite rect)."""
    if player.invincible > 0:
        return False
    hx, hy = player.hitbox.center
    for bullet in list(enemy_bullets):
        bx, by = int(bullet.pos.x), int(bullet.pos.y)
        dist = math.hypot(bx - hx, by - hy)
        if dist <= PLAYER_HITBOX_R + bullet.radius - 2:
            bullet.kill()
            return True
    return False


def check_graze(player, enemy_bullets):
    """Return number of new grazes this frame."""
    hx, hy = player.hitbox.center
    count = 0
    for bullet in enemy_bullets:
        if bullet.grazed:
            continue
        bx, by = int(bullet.pos.x), int(bullet.pos.y)
        dist = math.hypot(bx - hx, by - hy)
        if PLAYER_HITBOX_R < dist <= GRAZE_RADIUS + bullet.radius:
            bullet.grazed = True
            count += 1
    return count


def check_player_bullets_vs_enemies(player_bullets, enemies):
    """Return list of (enemy, bullet) pairs that collided."""
    hits = []
    for bullet in list(player_bullets):
        for enemy in list(enemies):
            if bullet.rect.colliderect(enemy.rect):
                hits.append((enemy, bullet))
                bullet.kill()
                break
    return hits


def check_player_bullets_vs_boss(player_bullets, boss):
    """Return total damage dealt to boss this frame."""
    damage = 0
    for bullet in list(player_bullets):
        bx, by = int(bullet.pos.x), int(bullet.pos.y)
        dist = math.hypot(bx - boss.rect.centerx, by - boss.rect.centery)
        if dist <= boss.size + bullet.radius:
            damage += bullet.damage
            bullet.kill()
    return damage


def check_powerup_pickup(player, powerups):
    """Return list of powerups collected."""
    collected = []
    for pu in list(powerups):
        if player.rect.colliderect(pu.rect):
            collected.append(pu)
            pu.kill()
    return collected
