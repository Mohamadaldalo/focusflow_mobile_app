"""
ui/home_screen.py
-----------------
Home screen — theme toggle, streak card, todo shortcut, study room button.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window

from logic.adaptive import suggest_duration, format_duration
from logic.strings import S
from data.storage import get_recent_sessions, get_streak
from data.theme import T, toggle_theme, mode_label
from data.todo_storage import get_stats as todo_stats


class HomeScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        suggested, _ = suggest_duration()
        self.selected_duration = suggested

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    def _build_ui(self):
        suggested, suggestion_msg = suggest_duration()
        self.selected_duration = suggested

        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))

        with root.canvas.before:
            Color(*T("bg"))
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg_rect, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg_rect, 'pos', v))

        # ── Top bar: title + theme toggle ─────────────────────────────────
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(50), spacing=dp(8)
        )
        top_bar.add_widget(Label(
            text=S("app_title"),
            font_size=dp(32), bold=True,
            color=T("accent"),
            halign="left", valign="middle",
            size_hint_x=1
        ))
        mode_btn = Button(
            text=mode_label(),
            font_size=dp(12),
            background_color=(0, 0, 0, 0),
            color=T("mode_btn_txt"),
            size_hint=(None, None),
            size=(dp(96), dp(32)),
            pos_hint={"center_y": 0.5}
        )
        with mode_btn.canvas.before:
            Color(*T("mode_btn_bg"))
            mode_bg = RoundedRectangle(size=mode_btn.size, pos=mode_btn.pos, radius=[dp(10)])
        mode_btn.bind(
            size=lambda w, v: setattr(mode_bg, 'size', v),
            pos=lambda w, v: setattr(mode_bg, 'pos', v)
        )
        mode_btn.bind(on_press=self._toggle_theme)
        top_bar.add_widget(mode_btn)
        root.add_widget(top_bar)

        # ── Tagline ───────────────────────────────────────────────────────
        root.add_widget(Label(
            text=S("app_tagline"),
            font_size=dp(12), color=T("text3"),
            size_hint_y=None, height=dp(20),
            halign="left", text_size=(dp(340), None)
        ))

        # ── Streak card ───────────────────────────────────────────────────
        root.add_widget(self._streak_card())

        # ── Suggestion ────────────────────────────────────────────────────
        root.add_widget(Label(
            text=suggestion_msg,
            font_size=dp(13), color=T("text2"),
            halign="center", size_hint_y=None, height=dp(32),
            text_size=(dp(320), None)
        ))

        # ── Duration display ──────────────────────────────────────────────
        self.duration_label = Label(
            text=self._fmt(self.selected_duration),
            font_size=dp(50), bold=True, color=T("text"),
            size_hint_y=None, height=dp(64)
        )
        root.add_widget(self.duration_label)
        root.add_widget(Label(
            text=S("duration_sub"),
            font_size=dp(12), color=T("text3"),
            size_hint_y=None, height=dp(16)
        ))

        # ── Slider ────────────────────────────────────────────────────────
        root.add_widget(Label(
            text=S("adjust_duration"),
            font_size=dp(12), color=T("text3"),
            size_hint_y=None, height=dp(16)
        ))
        self.slider = Slider(
            min=60, max=3600, value=self.selected_duration,
            step=60, size_hint_y=None, height=dp(38),
            cursor_size=(dp(20), dp(20))
        )
        self.slider.bind(value=self._on_slider)
        root.add_widget(self.slider)

        # ── Stats ─────────────────────────────────────────────────────────
        root.add_widget(self._stats_label())

        root.add_widget(Widget(size_hint_y=1))

        # ── Start Session button ──────────────────────────────────────────
        start_btn = self._accent_btn(S("start_btn"), dp(56), dp(20))
        start_btn.bind(on_press=self._start_session)
        root.add_widget(start_btn)

        # ── Bottom row: Settings | My Tasks ──────────────────────────────
        bottom_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(38),
            spacing=dp(12)
        )
        settings_btn = Button(
            text=S("settings_btn"),
            font_size=dp(12),
            background_color=(0, 0, 0, 0),
            color=T("text3")
        )
        settings_btn.bind(on_press=lambda *a: self._goto_settings())

        _, _, pending = todo_stats()
        todo_label = "My Tasks" if pending == 0 else f"My Tasks ({pending})"
        todo_btn = Button(
            text=todo_label,
            font_size=dp(12), bold=(pending > 0),
            background_color=(0, 0, 0, 0),
            color=T("accent") if pending > 0 else T("text3")
        )
        todo_btn.bind(on_press=lambda *a: self._goto_todo())

        bottom_row.add_widget(settings_btn)
        bottom_row.add_widget(todo_btn)
        root.add_widget(bottom_row)

        # ── Study Room button ─────────────────────────────────────────────
        study_btn = Button(
            text="Study Room  [live]",
            font_size=dp(13),
            background_color=(0, 0, 0, 0),
            color=T("accent"),
            size_hint_y=None,
            height=dp(32),
        )
        study_btn.bind(on_press=lambda *a: self._goto_study_room())
        root.add_widget(study_btn)

        self.add_widget(root)

    # ── Streak card ───────────────────────────────────────────────────────

    def _streak_card(self):
        streak, done_today = get_streak()

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(78),
            padding=(dp(14), dp(8)), spacing=dp(12)
        )
        with card.canvas.before:
            Color(*T("streak_bg"))
            card_rect = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(14)])
        card.bind(
            size=lambda w, v: setattr(card_rect, 'size', v),
            pos=lambda w, v: setattr(card_rect, 'pos', v)
        )

        # Left: streak number
        left = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1), width=dp(56),
            spacing=0
        )
        left.add_widget(Label(
            text=str(streak),
            font_size=dp(32), bold=True,
            color=T("streak_text"),
            size_hint_y=None, height=dp(44),
            valign="bottom"
        ))
        left.add_widget(Label(
            text="days",
            font_size=dp(10),
            color=T("streak_sub"),
            size_hint_y=None, height=dp(16),
            valign="top"
        ))
        card.add_widget(left)

        # Vertical divider
        div = Widget(size_hint=(None, 1), width=dp(1))
        with div.canvas:
            Color(*T("streak_sub")[:3], 0.4)
            div._rect = Rectangle(size=(dp(1), dp(44)), pos=(0, 0))
        def _upd(w, *a):
            w._rect.pos  = (w.x, w.y + (w.height - dp(44)) / 2)
            w._rect.size = (dp(1), dp(44))
        div.bind(pos=_upd, size=_upd)
        card.add_widget(div)

        # Right: title + subtitle + badge
        right = BoxLayout(orientation="vertical", spacing=dp(2))

        if streak == 0:
            title = S("streak_none")
            sub   = "Complete a session to begin"
        else:
            title = S("streak_day", n=streak)
            sub   = S("streak_today_done") if done_today else S("streak_today_go")

        right.add_widget(Label(
            text=title,
            font_size=dp(14), bold=True,
            color=T("streak_text"),
            halign="left", valign="bottom",
            text_size=(dp(210), None),
            size_hint_y=None, height=dp(26)
        ))
        right.add_widget(Label(
            text=sub,
            font_size=dp(11), color=T("streak_sub"),
            halign="left", text_size=(dp(210), None),
            size_hint_y=None, height=dp(18)
        ))

        badge = _streak_badge(streak)
        if badge:
            right.add_widget(Label(
                text=badge,
                font_size=dp(10), bold=True,
                color=T("streak_sub"),
                halign="left", text_size=(dp(210), None),
                size_hint_y=None, height=dp(14)
            ))

        card.add_widget(right)
        return card

    # ── Helpers ───────────────────────────────────────────────────────────

    def _accent_btn(self, text, height, font_size):
        btn = Button(
            text=text, font_size=font_size, bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(0.88, None), height=height,
            pos_hint={"center_x": 0.5}
        )
        with btn.canvas.before:
            Color(*T("accent"))
            bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(14)])
        btn.bind(
            size=lambda w, v: setattr(bg, 'size', v),
            pos=lambda w, v: setattr(bg, 'pos', v)
        )
        return btn

    def _fmt(self, seconds):
        return f"{seconds // 60:02d}:00"

    def _on_slider(self, slider, value):
        self.selected_duration = int(value)
        self.duration_label.text = self._fmt(self.selected_duration)

    def _start_session(self, *args):
        ss = self.manager.get_screen("session")
        ss.start_session(self.selected_duration)
        self.manager.transition.direction = "left"
        self.manager.current = "session"

    def _goto_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def _goto_todo(self):
        self.manager.transition.direction = "left"
        self.manager.current = "todo"

    def _goto_study_room(self):
        self.manager.transition.direction = "left"
        self.manager.current = "study_room"

    def _toggle_theme(self, *args):
        toggle_theme()
        Window.clearcolor = T("bg")
        self.clear_widgets()
        self._build_ui()

    def _stats_label(self):
        sessions = get_recent_sessions(5)
        if not sessions:
            text = S("no_sessions")
        else:
            w = sum(1 for s in sessions if s["success"])
            t = len(sessions)
            d = format_duration(sessions[0]["duration"])
            text = S("recent_stats", w=w, t=t, d=d)
        return Label(
            text=text, font_size=dp(12),
            color=T("text3"),
            size_hint_y=None, height=dp(20)
        )


def _streak_badge(streak):
    milestones = [
        (365, "[ 1 YEAR ]"), (100, "[ CENTURY ]"), (30, "[ 30 DAYS ]"),
        (21,  "[ 21 DAYS ]"), (14, "[ 2 WEEKS ]"), (7, "[ 1 WEEK ]"),
        (3,   "[ 3 DAYS ]"),  (1,  "[ Day 1 ]"),
    ]
    for threshold, label in milestones:
        if streak >= threshold:
            return label
    return ""