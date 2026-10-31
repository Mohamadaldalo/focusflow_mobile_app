

import time
import uuid
import json

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False
    print("[firebase] WARNING: run  pip install requests")

# ── CONFIGURE THIS ────────────────────────────────────────────────────────────
FIREBASE_URL = "https://focusflow-6a056-default-rtdb.europe-west1.firebasedatabase.app"

# ─────────────────────────────────────────────────────────────────────────────

# How many seconds before a user is considered offline
PRESENCE_TIMEOUT = 20


def _url(path):
    """Build a full Firebase REST URL for a given path."""
    return f"{FIREBASE_URL}/{path}.json"


def _get(path):
    """Read data from Firebase. Returns dict/value or None on error."""
    if not _REQUESTS_OK:
        return None
    try:
        r = requests.get(_url(path), timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[firebase] GET error: {e}")
    return None


def _put(path, data):
    """Write (overwrite) data at a path."""
    if not _REQUESTS_OK:
        return False
    try:
        r = requests.put(_url(path), json=data, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"[firebase] PUT error: {e}")
        return False


def _patch(path, data):
    """Update specific fields at a path (merge, not overwrite)."""
    if not _REQUESTS_OK:
        return False
    try:
        r = requests.patch(_url(path), json=data, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"[firebase] PATCH error: {e}")
        return False


def _post(path, data):
    """Push data to a list (Firebase generates a unique key)."""
    if not _REQUESTS_OK:
        return None
    try:
        r = requests.post(_url(path), json=data, timeout=5)
        if r.status_code == 200:
            return r.json().get("name")   # returns the generated key
    except Exception as e:
        print(f"[firebase] POST error: {e}")
    return None


def _delete(path):
    """Delete data at a path."""
    if not _REQUESTS_OK:
        return False
    try:
        r = requests.delete(_url(path), timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"[firebase] DELETE error: {e}")
        return False


# ── Room management ───────────────────────────────────────────────────────────

def generate_room_code():
    """Generate a short 6-character room code like 'AB12CD'."""
    import random, string
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_room(room_name, user_id, user_name):
    """
    Create a new room. Returns room_code on success, None on failure.
    Also joins the creator as the first user.
    """
    code = generate_room_code()
    now  = int(time.time())

    room_data = {
        "name":       room_name,
        "created_at": now,
        "timer": {
            "start_ts": now,
            "duration": 25 * 60,   # 25 minutes
            "phase":    "focus",
            "running":  False,
        },
        "users": {
            user_id: {
                "name":      user_name,
                "joined_at": now,
                "last_ping": now,
            }
        },
    }

    if _put(f"rooms/{code}", room_data):
        return code
    return None


def join_room(room_code, user_id, user_name):
    """
    Join an existing room. Returns True on success.
    Returns False if room doesn't exist.
    """
    room = _get(f"rooms/{room_code}/name")
    if room is None:
        return False   # room not found

    now = int(time.time())
    return _put(f"rooms/{room_code}/users/{user_id}", {
        "name":      user_name,
        "joined_at": now,
        "last_ping": now,
    })


def leave_room(room_code, user_id):
    """Remove user from a room."""
    _delete(f"rooms/{room_code}/users/{user_id}")


def ping_presence(room_code, user_id):
    """
    Call this every ~10 seconds to mark the user as online.
    Users whose last_ping is older than PRESENCE_TIMEOUT are considered offline.
    """
    _patch(f"rooms/{room_code}/users/{user_id}", {
        "last_ping": int(time.time())
    })


def get_online_users(room_code):
    """
    Return list of dicts for users who pinged recently.
    Each dict: {"id": ..., "name": ..., "joined_at": ...}
    """
    users_data = _get(f"rooms/{room_code}/users") or {}
    now = int(time.time())
    online = []
    for uid, info in users_data.items():
        last_ping = info.get("last_ping", 0)
        if now - last_ping < PRESENCE_TIMEOUT:
            online.append({
                "id":        uid,
                "name":      info.get("name", "Unknown"),
                "joined_at": info.get("joined_at", 0),
            })
    return online


def get_room_name(room_code):
    """Return the room name string."""
    return _get(f"rooms/{room_code}/name") or room_code


# ── Chat ──────────────────────────────────────────────────────────────────────

def send_message(room_code, user_name, text):
    """Send a chat message. Returns message key or None."""
    if not text.strip():
        return None
    return _post(f"rooms/{room_code}/messages", {
        "user": user_name,
        "text": text.strip(),
        "ts":   int(time.time()),
    })


def get_messages(room_code, since_ts=0):
    """
    Fetch messages newer than since_ts.
    Returns list of dicts sorted by timestamp:
      [{"user": "Alice", "text": "Hi", "ts": 1700000000}, ...]
    """
    all_msgs = _get(f"rooms/{room_code}/messages") or {}
    result = []
    for key, msg in all_msgs.items():
        if msg.get("ts", 0) > since_ts:
            result.append({
                "key":  key,
                "user": msg.get("user", "?"),
                "text": msg.get("text", ""),
                "ts":   msg.get("ts", 0),
            })
    result.sort(key=lambda m: m["ts"])
    return result


# ── Shared Pomodoro timer ─────────────────────────────────────────────────────

def get_timer_state(room_code):
    """
    Return the timer state dict:
      {
        "start_ts": 1700000000,   # when the current phase started
        "duration": 1500,         # total seconds for this phase
        "phase":    "focus",      # "focus" or "break"
        "running":  True,
      }
    Returns None if room not found.
    """
    return _get(f"rooms/{room_code}/timer")


def start_timer(room_code, phase="focus"):
    """
    Start (or restart) the shared timer for all users.
    phase: "focus" (25 min) or "break" (5 min)
    """
    duration = 25 * 60 if phase == "focus" else 5 * 60
    return _put(f"rooms/{room_code}/timer", {
        "start_ts": int(time.time()),
        "duration": duration,
        "phase":    phase,
        "running":  True,
    })


def stop_timer(room_code):
    """Pause/stop the shared timer."""
    state = get_timer_state(room_code) or {}
    elapsed = 0
    if state.get("running"):
        elapsed = int(time.time()) - state.get("start_ts", int(time.time()))
    return _patch(f"rooms/{room_code}/timer", {
        "running": False,
    })


def compute_remaining(timer_state):
    """
    Given a timer_state dict, compute how many seconds remain.
    Works for all users because it uses the server timestamp.
    Returns (remaining_seconds, phase).
    """
    if not timer_state:
        return 25 * 60, "focus"

    duration  = timer_state.get("duration", 25 * 60)
    start_ts  = timer_state.get("start_ts", int(time.time()))
    running   = timer_state.get("running", False)
    phase     = timer_state.get("phase", "focus")

    if running:
        elapsed   = int(time.time()) - start_ts
        remaining = max(0, duration - elapsed)
    else:
        remaining = duration

    return remaining, phase
