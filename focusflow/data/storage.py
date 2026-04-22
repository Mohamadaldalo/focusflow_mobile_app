"""
data/storage.py
---------------
Session history (JSON) + streak calculation.

Streak = number of consecutive calendar days that have
         at least one SUCCESSFUL session, ending today or yesterday.
"""

import json
import os
from datetime import datetime, date, timedelta

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "sessions.json")


def load_sessions():
    if not os.path.exists(SESSIONS_FILE):
        return []
    try:
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_session(duration_seconds, success):
    sessions = load_sessions()
    record = {
        "duration": duration_seconds,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    sessions.append(record)
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)
    return record


def get_recent_sessions(count=10):
    sessions = load_sessions()
    return list(reversed(sessions))[:count]


def get_streak():
    """
    Calculate the current daily streak.

    Returns:
        streak (int): Number of consecutive days with >= 1 successful session.
        is_active_today (bool): True if the user already completed a session today.

    Rules:
        - Only SUCCESSFUL sessions count.
        - Days are calendar days (date only, not time).
        - The streak is 0 if the most recent success was 2+ days ago.
        - The streak counts backwards from today (or yesterday if nothing today yet).
    """
    sessions = load_sessions()

    # Collect unique dates that had at least one success
    success_dates = set()
    for s in sessions:
        if s.get("success"):
            try:
                d = datetime.fromisoformat(s["timestamp"]).date()
                success_dates.add(d)
            except (ValueError, KeyError):
                pass

    if not success_dates:
        return 0, False

    today = date.today()
    is_active_today = today in success_dates

    # Walk backwards from today; break on first missing day
    streak = 0
    check = today
    while check in success_dates:
        streak += 1
        check -= timedelta(days=1)

    # If today has no session yet, also check if there's a running streak from yesterday
    if not is_active_today:
        check = today - timedelta(days=1)
        while check in success_dates:
            streak += 1
            check -= timedelta(days=1)

    return streak, is_active_today
