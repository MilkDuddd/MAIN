#!/usr/bin/env python3
"""
Job Hunter — Automated Job Application Suite
Usage: python app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import database
from core.settings import SETTINGS_PATH


def main():
    database.init_db()

    if not SETTINGS_PATH.exists():
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard()
        wizard.mainloop()
    else:
        from gui.app_window import launch
        launch()


if __name__ == "__main__":
    main()
