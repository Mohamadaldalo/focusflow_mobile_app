
from kivy.clock import Clock


class FocusTimer:

    FACT_INTERVAL_MIN = 60
    FACT_INTERVAL_MAX = 120

    def __init__(self, duration, on_tick=None, on_fact_rotate=None, on_complete=None):
        self.total_duration  = duration
        self.remaining       = duration
        self.elapsed         = 0
        self.on_tick         = on_tick
        self.on_fact_rotate  = on_fact_rotate
        self.on_complete     = on_complete
        self._clock_event    = None
        self._fact_timer     = 0
        self._next_fact_at   = self._new_fact_interval()
        self.running         = False
        self.completed       = False

    def _new_fact_interval(self):
        import random
        return random.randint(self.FACT_INTERVAL_MIN, self.FACT_INTERVAL_MAX)

    def start(self):
        if self.running:
            return
        self.running = True
        self._clock_event = Clock.schedule_interval(self._tick, 1)

    def stop(self):
        self.running = False
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def reset(self, new_duration=None):
        self.stop()
        self.total_duration  = new_duration or self.total_duration
        self.remaining       = self.total_duration
        self.elapsed         = 0
        self._fact_timer     = 0
        self._next_fact_at   = self._new_fact_interval()
        self.completed       = False

    def _tick(self, dt):
        """Called every second by Kivy Clock (main thread — safe)."""
        if not self.running:
            return

        self.elapsed      += 1
        self.remaining    -= 1
        self._fact_timer  += 1

        # ── on_tick — schedule on main thread to be safe ──────────────────
        if self.on_tick:
            elapsed   = self.elapsed
            remaining = self.remaining
            Clock.schedule_once(lambda dt: self.on_tick(elapsed, remaining), 0)

        # ── fact rotation ──────────────────────────────────────────────────
        if self._fact_timer >= self._next_fact_at:
            self._fact_timer   = 0
            self._next_fact_at = self._new_fact_interval()
            if self.on_fact_rotate:
                Clock.schedule_once(lambda dt: self.on_fact_rotate(), 0)

        # ── completion — THIS was the crash source ─────────────────────────
        if self.remaining <= 0:
            self.running   = False
            self.completed = True
            if self._clock_event:
                self._clock_event.cancel()
                self._clock_event = None
            if self.on_complete:
                # Schedule on main thread — never call UI code from Clock callback directly
                Clock.schedule_once(lambda dt: self.on_complete(), 0)

    @staticmethod
    def format_time(seconds):
        seconds  = max(0, int(seconds))
        minutes  = seconds // 60
        secs     = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    @property
    def progress(self):
        if self.total_duration == 0:
            return 1.0
        return self.elapsed / self.total_duration
