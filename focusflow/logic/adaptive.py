"""
logic/adaptive.py
-----------------
Adaptive session duration suggestion engine (English only).
"""

from data.storage import get_recent_sessions

MIN_DURATION = 60
MAX_DURATION = 3600
DEFAULT_DURATION = 600
STEP_UP = 60
STEP_DOWN = 120


def suggest_duration():
    """Return (duration_seconds, message_string)."""
    from logic.strings import S

    sessions = get_recent_sessions(count=5)
    if not sessions:
        return DEFAULT_DURATION, S("suggest_default")

    successes = [s for s in sessions if s["success"]]
    failures  = [s for s in sessions if not s["success"]]
    last_duration = sessions[0]["duration"]

    if len(successes) == len(sessions):
        new_duration = min(last_duration + STEP_UP, MAX_DURATION)
        return new_duration, S("suggest_up", m=new_duration // 60)

    if len(failures) > len(successes):
        if successes:
            best = min(s["duration"] for s in successes)
            new_duration = max(best + STEP_UP, MIN_DURATION)
            return new_duration, S("suggest_build", m=new_duration // 60)
        else:
            new_duration = max(int(last_duration * 0.8), MIN_DURATION)
            return new_duration, S("suggest_shorter", m=new_duration // 60)

    new_duration = min(last_duration + (STEP_UP // 2), MAX_DURATION)
    return new_duration, S("suggest_steady", m=new_duration // 60)


def format_duration(seconds):
    """Convert seconds to a readable string like '10 min'."""
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    rem = minutes % 60
    return f"{hours} hr {rem} min" if rem else f"{hours} hr"
