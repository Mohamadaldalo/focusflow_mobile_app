"""
data/theme.py
-------------
Light / Dark theme palette.
All screens import colors from here so a single toggle repaints everything.

Usage:
    from data.theme import T, toggle_theme, is_dark
    bg_color = T("bg")
"""

from data.settings import get as get_setting, set_value as save_setting

# ── Palettes ──────────────────────────────────────────────────────────────────
_DARK = {
    "bg":           (0.07, 0.07, 0.12, 1),   # deep navy
    "bg2":          (0.12, 0.12, 0.22, 1),   # card surface
    "bg3":          (0.16, 0.16, 0.28, 1),   # elevated card
    "text":         (1.00, 1.00, 1.00, 1),   # primary text
    "text2":        (0.75, 0.75, 0.90, 1),   # secondary text
    "text3":        (0.50, 0.50, 0.70, 1),   # muted text
    "accent":       (0.40, 0.90, 0.70, 1),   # mint green
    "accent_text":  (0.07, 0.07, 0.12, 1),   # text ON accent buttons
    "danger":       (0.80, 0.30, 0.30, 1),   # red / end session
    "ring_track":   (0.20, 0.20, 0.30, 1),   # progress ring bg
    "streak_bg":    (0.18, 0.13, 0.07, 1),   # warm card for streak
    "streak_text":  (1.00, 0.75, 0.30, 1),   # golden streak number
    "streak_sub":   (0.80, 0.60, 0.30, 1),   # streak label
    "mode_btn_bg":  (0.18, 0.18, 0.30, 1),   # theme toggle button bg
    "mode_btn_txt": (0.85, 0.85, 0.95, 1),   # theme toggle button text
}

_LIGHT = {
    "bg":           (0.96, 0.96, 0.98, 1),   # near-white
    "bg2":          (1.00, 1.00, 1.00, 1),   # card surface
    "bg3":          (0.90, 0.92, 0.96, 1),   # elevated card
    "text":         (0.10, 0.10, 0.16, 1),   # primary text
    "text2":        (0.25, 0.25, 0.38, 1),   # secondary text
    "text3":        (0.50, 0.50, 0.62, 1),   # muted text
    "accent":       (0.10, 0.70, 0.50, 1),   # deeper mint for visibility on white
    "accent_text":  (1.00, 1.00, 1.00, 1),   # text ON accent buttons
    "danger":       (0.80, 0.20, 0.20, 1),
    "ring_track":   (0.82, 0.85, 0.90, 1),
    "streak_bg":    (1.00, 0.97, 0.90, 1),   # warm cream
    "streak_text":  (0.80, 0.50, 0.05, 1),   # amber
    "streak_sub":   (0.60, 0.40, 0.10, 1),
    "mode_btn_bg":  (0.86, 0.88, 0.92, 1),
    "mode_btn_txt": (0.20, 0.20, 0.30, 1),
}


def is_dark():
    """Return True if dark mode is active (default)."""
    val = get_setting("theme")
    if val is None:
        return True          # Default = dark
    return val == "dark"


def T(key):
    """Return the RGBA tuple for the given color key in the active theme."""
    palette = _DARK if is_dark() else _LIGHT
    return palette.get(key, (1, 1, 1, 1))


def toggle_theme():
    """Flip between dark and light and persist the choice."""
    save_setting("theme", "light" if is_dark() else "dark")


def mode_label():
    """Human-readable label for the toggle button."""
    return "Light Mode" if is_dark() else "Dark Mode"
