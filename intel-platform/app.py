#!/usr/bin/env python3
"""
Intel Platform — GUI launcher
Usage: python app.py
Double-click "Intel Platform.command/.bat/.sh" for terminal-free launch.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import database
from core.settings import SETTINGS_PATH


def _seed_static_data():
    try:
        from modules.uap.congress_uap import populate_db as seed_hearings
        from modules.uap.declassified import populate_db as seed_docs
        from modules.uap.faa_reports import populate_db as seed_faa
        seed_hearings()
        seed_docs()
        seed_faa()
    except Exception:
        pass


if __name__ == "__main__":
    database.init_db()
    _seed_static_data()

    if not SETTINGS_PATH.exists():
        # First run — show setup wizard
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard()
        wizard.mainloop()
    else:
        from gui.app_window import launch
        launch()
