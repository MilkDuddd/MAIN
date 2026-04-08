#!/usr/bin/env python3
"""
Intel Platform — GUI launcher
Usage: python app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import launch

if __name__ == "__main__":
    launch()
