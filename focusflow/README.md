# FocusFlow 🎯
### Adaptive Focus & Attention Training App

A clean, minimal Kivy mobile app that helps you build your attention span through timed focus sessions, rotating facts, and adaptive difficulty.

---

## 📁 Project Structure

```
focusflow/
├── main.py                  # App entry point — run this
├── requirements.txt         # Python dependencies
├── buildozer.spec           # Android APK build config
│
├── ui/                      # All screen UI code
│   ├── home_screen.py       # Landing screen: duration picker + start button
│   ├── session_screen.py    # Active session: timer ring + facts
│   └── result_screen.py     # Results: success/failure + next suggestion
│
├── logic/                   # App logic (no UI)
│   ├── timer.py             # Countdown timer with Kivy Clock
│   ├── facts.py             # "Did You Know?" fact pool
│   └── adaptive.py          # Session duration suggestion engine
│
└── data/
    ├── storage.py           # JSON read/write for session history
    └── sessions.json        # Auto-created on first session
```

---

## 🚀 How to Run

### 1. Install Python 3.9+ and pip

### 2. Install Kivy
```bash
pip install kivy
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
cd focusflow
python main.py
```

A 390×844 window (iPhone-sized) will open for desktop testing.

---

## 📱 Build to APK (Android)

### Prerequisites
- Linux or macOS (WSL2 works on Windows)
- Python 3.9+

### Steps
```bash
# Install buildozer
pip install buildozer

# Inside the focusflow/ folder:
buildozer android debug

# The .apk will be in:
# bin/focusflow-1.0-debug.apk
```

**First build takes 20–30 minutes** (downloads Android SDK/NDK automatically).

### Install on device
```bash
buildozer android debug deploy run
```
Or copy the APK to your phone and install manually (enable "Unknown Sources").

---

## 🎮 How to Use

1. **Home Screen** — App suggests a session duration based on your history. Adjust with the slider if you like.
2. **Session Screen** — Hit **Start Session**. A countdown ring appears along with rotating focus facts every 60–120 seconds.
3. **End Session** — Either complete it ✅ or tap **End Session** early ❌.
4. **Result Screen** — See your stats and an adaptive suggestion for your next session.

---

## 🧠 Adaptive Logic

| Situation | Suggestion |
|-----------|-----------|
| All recent sessions succeeded | Add 1 minute |
| More failures than successes | Drop to last success + 1 min |
| All failures | Reduce to 80% of last duration |
| First session ever | Default 10 minutes |

Session history is stored in `data/sessions.json`.

---

## 🔧 Customization

| What | Where | How |
|------|-------|-----|
| Add more facts | `logic/facts.py` | Add strings to `FACTS` list |
| Change default duration | `logic/adaptive.py` | Edit `DEFAULT_DURATION` |
| Adjust fact rotation speed | `logic/timer.py` | Edit `FACT_INTERVAL_MIN/MAX` |
| Change colors | Each `ui/` screen | Edit `Color(r, g, b, a)` values |

---

## 📦 Dependencies

- **Kivy 2.2+** — cross-platform UI framework
- **Python stdlib only** — `json`, `os`, `random`, `datetime`, `math`

No external APIs, no internet required.

---

## 🛠 Future Improvements

- [ ] Sound/vibration on completion
- [ ] Session streaks and badges
- [ ] Custom fact categories
- [ ] Background music integration
- [ ] iCloud/Google Drive sync for session history
