"""
logic/strings.py  —  English only
"""

_STRINGS = {
    "interest_title":       "What interests you?",
    "interest_sub":         "We'll show you facts on this topic during your focus sessions.",
    "app_title":            "FocusFlow",
    "app_tagline":          "Train your attention, one session at a time.",
    "duration_sub":         "session duration",
    "adjust_duration":      "Adjust duration",
    "start_btn":            "Start Session",
    "no_sessions":          "No sessions yet - let's start!",
    "recent_stats":         "Recent: {w}/{t} completed  |  Last: {d}",
    "settings_btn":         "Settings",
    "focusing_tag":         "F O C U S I N G",
    "end_session":          "End Session",
    "fact_prefix":          "Fact: ",
    "mute_btn":             "Mute Voice",
    "unmute_btn":           "Voice On",
    "result_success_title": "Session Complete!",
    "result_fail_title":    "Session Ended",
    "focused_for":          "You focused for {d}",
    "partial_focus":        "Focused {e} of {d} ({p}%)",
    "next_suggestion":      "Next Session Suggestion",
    "back_home":            "Back to Home",
    "settings_title":       "Settings",
    "change_interest":      "Interest Topic",
    "save_settings":        "Save",
    "back_btn":             "Back",
    "suggest_default":      "Start with a 10-minute focus session.",
    "suggest_up":           "Great streak! Try {m} minutes this time.",
    "suggest_build":        "Let's build up to {m} min - you got this!",
    "suggest_shorter":      "Let's try a shorter {m}-minute session.",
    "suggest_steady":       "Steady progress! {m} minutes is a good next step.",
    # ── Streak ────────────────────────────────────────────────────────────
    "streak_none":          "No streak yet - start today!",
    "streak_day":           "{n} Day Streak",
    "streak_fire":          "Keep the fire going!",
    "streak_new":           "New record - keep it up!",
    "streak_today_done":    "Session done today!",
    "streak_today_go":      "Session not done today",
    # ── Success / Failure ─────────────────────────────────────────────────
    "success_1": "You locked in. That's how champions are built.",
    "success_2": "Full session complete. Your brain just got stronger.",
    "success_3": "Focus unlocked. Keep stacking these wins!",
    "success_4": "Discipline is freedom - and you just proved it.",
    "success_5": "Session complete. Another rep for your attention muscle.",
    "fail_1": "Every attempt counts. Try a shorter session next time.",
    "fail_2": "You showed up - that's already winning. Adjust and retry.",
    "fail_3": "Focus is a skill. You're still training. Try again!",
    "fail_4": "No shame in stopping. Shorter sessions build the habit.",
    "fail_5": "The hardest part is starting. You did that. Try again soon.",
}


def S(key, **fmt):
    text = _STRINGS.get(key, key)
    if fmt:
        try:
            text = text.format(**fmt)
        except KeyError:
            pass
    return text


def SUCCESS_MSGS():
    return [S(f"success_{i}") for i in range(1, 6)]

def FAILURE_MSGS():
    return [S(f"fail_{i}") for i in range(1, 6)]
