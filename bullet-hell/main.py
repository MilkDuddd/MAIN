#!/usr/bin/env python3
"""
VOID — A Bullet Hell
Run: python main.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

def main():
    pygame.init()
    pygame.display.set_caption("VOID")
    from game.game_loop import Game
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
