"""
data/settings.py
----------------
Stores persistent user preferences: interest + theme.
"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

INTERESTS = [
    ("science",    "Science"),
    ("history",    "History"),
    ("tech",       "Technology"),
    ("health",     "Health"),
    ("space",      "Space"),
    ("psychology", "Psychology"),
]

_DEFAULTS = {
    "interest": None,
    "theme":    "dark",   # "dark" | "light"
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(_DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, IOError):
        return dict(_DEFAULTS)


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def get(key):
    return load_settings().get(key)


def set_value(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)
