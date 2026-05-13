"""
All dialogue. Speaker codes:
  [HIM]    - the protagonist
  [???]    - the voice that breaks the fourth wall (addresses the player directly)
  [ENEMY:X]- a boss speaking
"""

LINES = {
    # ── MENU ──────────────────────────────────────────────────────────────────
    "menu_first_visit": ("[???]", "You don't have to do this, you know."),
    "menu_return":      ("[???]", "You came back. You always come back."),

    # ── WAVE 1 ────────────────────────────────────────────────────────────────
    "wave_1_start": (
        "[???]",
        "You there. Yes, you. Don't look away. This is yours now.",
    ),
    "wave_2_start": (
        "[HIM]",
        "Space is quiet. But quiet isn't the same as safe. I know that now.",
    ),

    # ── CONFLICT arc ──────────────────────────────────────────────────────────
    "wave_3_start": (
        "[HIM]",
        "Fear ran my life for thirty years. Made every choice for me. Even this one.",
    ),
    "wave_4_start": (
        "[???]",
        "He took this mission because staying felt worse than dying. Think about that.",
    ),

    # ── RISING ACTION ─────────────────────────────────────────────────────────
    "wave_5_start": (
        "[HIM]",
        "I'm still alive. I don't know how. I don't know how much longer.",
    ),
    "wave_6_start": (
        "[???]",
        "Breathe. You're not in danger. He is.",
    ),
    "wave_7_start": (
        "[HIM]",
        "There's something strange about surviving something that was meant to kill you.",
    ),
    "wave_8_start": (
        "[???]",
        "He's getting tired. Can you feel it through the controller? Probably not.",
    ),
    "wave_9_start": (
        "[HIM]",
        "I keep waiting for it to feel like strength. It just feels like luck.",
    ),

    # ── BOSSES ────────────────────────────────────────────────────────────────
    "boss_1_spawn": (
        "[ENEMY: THE GATEKEEPER]",
        "Turn back. There is nothing here worth dying for.",
    ),
    "boss_1_phase": (
        "[ENEMY: THE GATEKEEPER]",
        "...You're still here.",
    ),
    "boss_1_death": (
        "[???]",
        "He thought you'd protect him. You did. For now.",
    ),

    "boss_2_spawn": (
        "[ENEMY: THE MIRROR]",
        "Look at yourself. Is this who you wanted to become?",
    ),
    "boss_2_phase": (
        "[ENEMY: THE MIRROR]",
        "The person pressing those keys — do they look at you and feel proud?",
    ),
    "boss_2_death": (
        "[HIM]",
        "I don't recognize myself anymore. I'm not sure if that's good.",
    ),

    "boss_3_spawn": (
        "[ENEMY: THE WOUND]",
        "Fear brought you here. Fear will end you.",
    ),
    "boss_3_phase": (
        "[ENEMY: THE WOUND]",
        "You can't outrun what lives inside you.",
    ),
    "boss_3_death": (
        "[???]",
        "You're getting better at this. At watching someone hurt.",
    ),

    "boss_4_spawn": (
        "[ENEMY: THE ARCHITECT]",
        "I built this place for people like you. Purposeless. Drifting.",
    ),
    "boss_4_phase": (
        "[ENEMY: THE ARCHITECT]",
        "Every bullet I fire — you told him to dodge. Not me.",
    ),
    "boss_4_death": (
        "[HIM]",
        "Halfway. God, I'm only halfway.",
    ),

    "boss_5_spawn": (
        "[ENEMY: THE LAST DOUBT]",
        "You almost stopped. Three times in the last hour. I counted.",
    ),
    "boss_5_phase": (
        "[ENEMY: THE LAST DOUBT]",
        "He wants to give up. The only reason he hasn't is sitting in that chair.",
    ),
    "boss_5_death": (
        "[???]",
        "Why are you still here? I'm genuinely asking.",
    ),

    "boss_6_spawn": (
        "[ENEMY: THE DARK]",
        "You know what happens when you win? Nothing changes. For you.",
    ),
    "boss_6_phase_1": (
        "[ENEMY: THE DARK]",
        "He's terrified. Look at him. But he won't stop because you won't let him.",
    ),
    "boss_6_phase_2": (
        "[ENEMY: THE DARK]",
        "This is the last thing standing between him and whatever comes after.",
    ),
    "boss_6_phase_3": (
        "[HIM]",
        "I don't want to die. I don't want to die. I don't want to die.",
    ),

    # ── CLIMAX arc ────────────────────────────────────────────────────────────
    "wave_10_start": (
        "[???]",
        "You're still here. Interesting. Why?",
    ),
    "wave_14_start": (
        "[HIM]",
        "I can feel it now. Whatever's at the end. It's pulling me forward.",
    ),
    "wave_17_start": (
        "[???]",
        "He knows it's too late to turn back. Do you?",
    ),
    "wave_19_start": (
        "[HIM]",
        "I'm scared. I've been scared this whole time. I think that's okay.",
    ),

    # ── FALLING ACTION ────────────────────────────────────────────────────────
    "wave_21_start": (
        "[HIM]",
        "Blood. Sweat. Tears. The clichés exist because they're true.",
    ),
    "wave_25_start": (
        "[???]",
        "He's going to make it. You made sure of that. Sit with that.",
    ),
    "wave_28_start": (
        "[HIM]",
        "Almost done. Almost done. Almost done.",
    ),

    # ── DEATHS / RESPAWN ──────────────────────────────────────────────────────
    "death_1": (
        "[???]",
        "Pain? No. You just pressed a button. He felt it.",
    ),
    "death_2": (
        "[HIM]",
        "Still here. Get up. Get up.",
    ),
    "death_3": (
        "[???]",
        "You'll try again. He won't remember.",
    ),
    "death_many": (
        "[???]",
        "Every time you respawn him, he wakes up somewhere he's already been.",
    ),

    # ── SYSTEM / META ─────────────────────────────────────────────────────────
    "first_pause": (
        "[???]",
        "Going somewhere? He doesn't get to pause.",
    ),
    "new_high_score": (
        "[???]",
        "You're getting better at watching someone suffer.",
    ),
    "focus_first_use": (
        "[HIM]",
        "Slow down. Breathe. Find the gaps.",
    ),

    # ── ENDING ────────────────────────────────────────────────────────────────
    "ending_1": ("[HIM]", "It's over."),
    "ending_2": ("[HIM]", "I won. I think. I'm still here."),
    "ending_3": ("[HIM]", "I'm going home."),
    "ending_4": ("[HIM]", "I'm going to sleep for a week."),
    "ending_5": ("[HIM]", "I vowed, in that moment, never again."),
    "ending_6": ("[HIM]", "No more missions. No more war. No more."),
    "ending_7": ("[HIM]", "He went home. He never spoke of it."),
    "ending_8": ("[HIM]", "Some nights he still hears them."),
    "ending_meta": ("[???]", "You can close the window now."),
}

# Ordered ending sequence
ENDING_SEQUENCE = [
    "ending_1", "ending_2", "ending_3", "ending_4",
    "ending_5", "ending_6", "ending_7", "ending_8", "ending_meta",
]

# Wave start lines (keyed by wave number)
WAVE_LINES = {
    1: "wave_1_start",
    2: "wave_2_start",
    3: "wave_3_start",
    4: "wave_4_start",
    5: "wave_5_start",
    6: "wave_6_start",
    7: "wave_7_start",
    8: "wave_8_start",
    9: "wave_9_start",
    10: "wave_10_start",
    14: "wave_14_start",
    17: "wave_17_start",
    19: "wave_19_start",
    21: "wave_21_start",
    25: "wave_25_start",
    28: "wave_28_start",
}

BOSS_SPAWN_LINES = {
    0: "boss_1_spawn",
    1: "boss_2_spawn",
    2: "boss_3_spawn",
    3: "boss_4_spawn",
    4: "boss_5_spawn",
    5: "boss_6_spawn",
}

BOSS_PHASE_LINES = {
    0: ["boss_1_phase"],
    1: ["boss_2_phase"],
    2: ["boss_3_phase"],
    3: ["boss_4_phase"],
    4: ["boss_5_phase"],
    5: ["boss_6_phase_1", "boss_6_phase_2", "boss_6_phase_3"],
}

BOSS_DEATH_LINES = {
    0: "boss_1_death",
    1: "boss_2_death",
    2: "boss_3_death",
    3: "boss_4_death",
}
