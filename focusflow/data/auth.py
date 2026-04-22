"""
data/auth.py
------------
Google OAuth2 authentication using the Device Authorization Flow.

WHY DEVICE FLOW (not redirect):
  - Works on desktop and mobile without a browser redirect URI
  - User visits a short URL on any device and enters a code
  - No local HTTP server or deep-link handling required
  - Standard OAuth2 RFC 8628

SETUP (one-time, free):
  1. Go to https://console.cloud.google.com
  2. Create a project → APIs & Services → Credentials
  3. Create an OAuth 2.0 Client ID → choose "TVs and Limited Input devices"
  4. Copy the Client ID and Client Secret into this file (or credentials.json)

SCOPES used:
  - openid         → identity
  - email          → user's email address
  - profile        → display name + avatar URL

All tokens are stored locally in data/auth_token.json.
"""

import json
import os
import time
import threading
import urllib.request
import urllib.parse
import urllib.error

# ── File paths ────────────────────────────────────────────────────────────────
_DIR        = os.path.dirname(__file__)
CREDS_FILE  = os.path.join(_DIR, "google_credentials.json")
TOKEN_FILE  = os.path.join(_DIR, "auth_token.json")

# ── Google OAuth endpoints ────────────────────────────────────────────────────
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL       = "https://oauth2.googleapis.com/token"
USERINFO_URL    = "https://www.googleapis.com/oauth2/v3/userinfo"
REVOKE_URL      = "https://oauth2.googleapis.com/revoke"
SCOPES          = "openid email profile"


# ─────────────────────────────────────────────────────────────────────────────
# Credentials helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_credentials():
    """
    Load client_id and client_secret from google_credentials.json.
    Returns (client_id, client_secret) or (None, None).

    Expected file format:
    {
      "client_id":     "xxxx.apps.googleusercontent.com",
      "client_secret": "GOCSPX-xxxx"
    }
    """
    if not os.path.exists(CREDS_FILE):
        return None, None
    try:
        with open(CREDS_FILE, "r") as f:
            d = json.load(f)
        return d.get("client_id"), d.get("client_secret")
    except Exception:
        return None, None


def credentials_configured():
    """Return True if google_credentials.json exists and has both fields."""
    cid, csec = load_credentials()
    return bool(cid and csec)


# ─────────────────────────────────────────────────────────────────────────────
# Token storage
# ─────────────────────────────────────────────────────────────────────────────

def _load_token():
    if not os.path.exists(TOKEN_FILE):
        return {}
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_token(data: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _clear_token():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers (stdlib only — no requests library needed)
# ─────────────────────────────────────────────────────────────────────────────

def _post(url, params: dict) -> dict:
    data    = urllib.parse.urlencode(params).encode()
    req     = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _get_json(url, access_token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────

def get_current_user():
    """
    Return the logged-in user dict or None.
    Dict keys: email, name, picture, sub (Google user ID).
    Refreshes the access token automatically if expired.
    """
    token = _load_token()
    if not token or "access_token" not in token:
        return None

    # Check expiry
    expires_at = token.get("expires_at", 0)
    if time.time() > expires_at - 60:
        # Try to refresh
        refreshed = _refresh_token(token)
        if not refreshed:
            return None
        token = _load_token()

    return token.get("user_info")


def is_logged_in():
    return get_current_user() is not None


def _refresh_token(token: dict) -> bool:
    """Use the refresh_token to get a new access_token. Returns True on success."""
    refresh = token.get("refresh_token")
    if not refresh:
        return False
    client_id, client_secret = load_credentials()
    if not client_id:
        return False
    try:
        resp = _post(TOKEN_URL, {
            "client_id":     client_id,
            "client_secret": client_secret,
            "refresh_token": refresh,
            "grant_type":    "refresh_token",
        })
        token["access_token"] = resp["access_token"]
        token["expires_at"]   = time.time() + resp.get("expires_in", 3600)
        _save_token(token)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Sign-in flow (Device Authorization)
# ─────────────────────────────────────────────────────────────────────────────

class DeviceFlowSession:
    """
    Manages a single Device Authorization Flow login attempt.

    Usage:
        session = DeviceFlowSession()
        ok, err = session.start()          # Gets device code from Google
        if ok:
            # Show session.user_code and session.verification_url to user
            session.poll(on_success=..., on_error=...)   # Non-blocking poll
    """

    def __init__(self):
        self.user_code         = None
        self.verification_url  = None
        self.device_code       = None
        self.interval          = 5
        self._polling          = False
        self._poll_thread      = None

    def start(self):
        """
        Request a device code from Google.
        Returns (True, None) on success or (False, error_message).
        """
        client_id, _ = load_credentials()
        if not client_id:
            return False, "google_credentials.json not found or incomplete."
        try:
            resp = _post(DEVICE_CODE_URL, {
                "client_id": client_id,
                "scope":     SCOPES,
            })
            self.device_code        = resp["device_code"]
            self.user_code          = resp["user_code"]
            self.verification_url   = resp.get("verification_url", "https://google.com/device")
            self.interval           = resp.get("interval", 5)
            self._expires_in        = resp.get("expires_in", 1800)
            self._started_at        = time.time()
            return True, None
        except Exception as e:
            return False, str(e)

    def poll(self, on_success, on_error):
        """
        Poll Google in a background thread until the user authorises or timeout.
        on_success(user_info_dict) — called on the polling thread (use Clock.schedule_once for UI).
        on_error(message)          — called on the polling thread.
        """
        self._polling = True

        def _loop():
            client_id, client_secret = load_credentials()
            deadline = self._started_at + self._expires_in

            while self._polling and time.time() < deadline:
                time.sleep(self.interval)
                if not self._polling:
                    break
                try:
                    resp = _post(TOKEN_URL, {
                        "client_id":     client_id,
                        "client_secret": client_secret,
                        "device_code":   self.device_code,
                        "grant_type":    "urn:ietf:params:oauth:grant-type:device_code",
                    })

                    if "error" in resp:
                        err = resp["error"]
                        if err == "authorization_pending":
                            continue       # User hasn't approved yet
                        elif err == "slow_down":
                            self.interval += 5
                            continue
                        else:
                            on_error(f"Google error: {err}")
                            return

                    # Success — save tokens
                    access_token  = resp["access_token"]
                    expires_in    = resp.get("expires_in", 3600)
                    refresh_token = resp.get("refresh_token", "")

                    # Fetch user profile
                    user_info = _get_json(USERINFO_URL, access_token)

                    token_data = {
                        "access_token":  access_token,
                        "refresh_token": refresh_token,
                        "expires_at":    time.time() + expires_in,
                        "user_info":     user_info,
                    }
                    _save_token(token_data)
                    self._polling = False
                    on_success(user_info)
                    return

                except Exception as e:
                    on_error(str(e))
                    return

            if self._polling:
                on_error("Login timed out. Please try again.")

        self._poll_thread = threading.Thread(target=_loop, daemon=True)
        self._poll_thread.start()

    def cancel(self):
        self._polling = False


def sign_out():
    """Revoke token and clear local storage."""
    token = _load_token()
    access_token = token.get("access_token")
    if access_token:
        try:
            _post(REVOKE_URL, {"token": access_token})
        except Exception:
            pass
    _clear_token()
