"""
ui/result_screen.py  —  theme-aware, shows streak on success
"""

import random
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window

from logic.adaptive import suggest_duration, format_duration
from logic.strings import S, SUCCESS_MSGS, FAILURE_MSGS
from data.storage import get_streak
from data.theme import T


class ResultScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ui_built = False

    def on_enter(self):
        Window.clearcolor = T("bg")

    def show_result(self, success, duration, elapsed):
        if self._ui_built:
            self.clear_widgets()
        self._build_ui(success, duration, elapsed)
        self._ui_built = True

    def _build_ui(self, success, duration, elapsed):
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(12))

        with root.canvas.before:
            Color(*T("bg"))
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        root.add_widget(Widget(size_hint_y=0.06))

        # ── Result icon ───────────────────────────────────────────────────
        icon_color = T("accent") if success else T("danger")
        icon_label = Label(
            text="[ DONE ]" if success else "[ STOP ]",
            font_size=dp(34), bold=True, color=icon_color,
            size_hint_y=None, height=dp(62)
        )
        root.add_widget(icon_label)

        root.add_widget(Label(
            text=S("result_success_title") if success else S("result_fail_title"),
            font_size=dp(26), bold=True, color=icon_color,
            size_hint_y=None, height=dp(46)
        ))

        # ── Stats ─────────────────────────────────────────────────────────
        if success:
            stats_text = S("focused_for", d=format_duration(duration))
        else:
            pct = int((elapsed / duration) * 100) if duration > 0 else 0
            stats_text = S("partial_focus",
                           e=format_duration(elapsed),
                           d=format_duration(duration),
                           p=pct)
        root.add_widget(Label(
            text=stats_text, font_size=dp(14),
            color=T("text2"),
            size_hint_y=None, height=dp(30),
            halign="center", text_size=(dp(320), None)
        ))

        # ── Motivational message ──────────────────────────────────────────
        root.add_widget(Label(
            text=random.choice(SUCCESS_MSGS() if success else FAILURE_MSGS()),
            font_size=dp(13), color=T("text2"),
            halign="center", text_size=(dp(310), None),
            size_hint_y=None, height=dp(56)
        ))

        # ── Streak card (shown on success) ────────────────────────────────
        if success:
            root.add_widget(self._streak_card())
        else:
            root.add_widget(Widget(size_hint_y=0.02))

        # ── Adaptive suggestion card ──────────────────────────────────────
        _, next_msg = suggest_duration()
        card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(80),
            padding=dp(12), spacing=dp(4)
        )
        with card.canvas.before:
            Color(*T("bg2"))
            card_bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(12)])
        card.bind(
            size=lambda w, v: setattr(card_bg, 'size', v),
            pos=lambda w, v: setattr(card_bg, 'pos', v)
        )
        card.add_widget(Label(
            text=S("next_suggestion"),
            font_size=dp(11), color=T("text3"),
            size_hint_y=None, height=dp(20)
        ))
        card.add_widget(Label(
            text=next_msg, font_size=dp(14), color=T("accent"),
            size_hint_y=None, height=dp(28),
            halign="center", text_size=(dp(290), None)
        ))
        root.add_widget(card)
        root.add_widget(Widget(size_hint_y=1))

        # ── Home button ───────────────────────────────────────────────────
        home_btn = Button(
            text=S("back_home"), font_size=dp(18), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(0.85, None), height=dp(54),
            pos_hint={"center_x": 0.5}
        )
        with home_btn.canvas.before:
            Color(*T("accent"))
            hb = RoundedRectangle(size=home_btn.size, pos=home_btn.pos, radius=[dp(14)])
        home_btn.bind(
            size=lambda w, v: setattr(hb, 'size', v),
            pos=lambda w, v: setattr(hb, 'pos', v)
        )
        home_btn.bind(on_press=lambda *a: self._go_home())
        root.add_widget(home_btn)
        root.add_widget(Widget(size_hint_y=0.03))

        self.add_widget(root)

        icon_label.opacity = 0
        Animation(opacity=1, duration=0.5).start(icon_label)

    def _streak_card(self):
        """Celebratory streak card shown after a successful session."""
        streak, _ = get_streak()

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(72),
            padding=(dp(16), dp(8)), spacing=dp(12)
        )
        with card.canvas.before:
            Color(*T("streak_bg"))
            cr = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(12)])
        card.bind(
            size=lambda w, v: setattr(cr, 'size', v),
            pos=lambda w, v: setattr(cr, 'pos', v)
        )
        with card.canvas.after:
            Color(*T("streak_text")[:3], 0.4)
            Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(12)), width=1.2)

        # Flame indicator
        card.add_widget(Label(
            text="***",
            font_size=dp(22), bold=True,
            color=T("streak_text"),
            size_hint=(None, 1), width=dp(48)
        ))

        # Text block
        info = BoxLayout(orientation="vertical")
        info.add_widget(Label(
            text=S("streak_day", n=streak) if streak > 0 else S("streak_none"),
            font_size=dp(15), bold=True,
            color=T("streak_text"),
            halign="left", text_size=(dp(220), None),
            size_hint_y=None, height=dp(26)
        ))
        info.add_widget(Label(
            text=S("streak_fire") if streak >= 3 else "Keep going!",
            font_size=dp(11),
            color=T("streak_sub"),
            halign="left", text_size=(dp(220), None),
            size_hint_y=None, height=dp(18)
        ))
        card.add_widget(info)
        return card

    def _go_home(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
