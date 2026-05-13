import json
import os
from game.constants import SAVE_PATH


class Scoring:
    def __init__(self):
        self.score = 0
        self.graze_count = 0
        self.high_score = self._load_high_score()
        self._new_high = False

    def add(self, points):
        self.score += points
        if self.score > self.high_score:
            self._new_high = True
            self.high_score = self.score

    def graze(self):
        from game.constants import SCORE_GRAZE
        self.graze_count += 1
        self.add(SCORE_GRAZE)

    def is_new_high(self):
        return self._new_high

    def save(self):
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        try:
            data = {}
            if os.path.exists(SAVE_PATH):
                with open(SAVE_PATH) as f:
                    data = json.load(f)
            data["high_score"] = self.high_score
            with open(SAVE_PATH, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_high_score(self):
        try:
            with open(SAVE_PATH) as f:
                return json.load(f).get("high_score", 0)
        except Exception:
            return 0
