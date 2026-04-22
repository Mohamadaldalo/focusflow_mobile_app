"""
ui/interest_screen.py  —  theme-aware
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window

from data.settings import set_value as save_setting, get as get_setting, INTERESTS
from logic.strings import S
from data.theme import T

INTEREST_ICONS = {
    "science":    "[Sci]",
    "history":    "[His]",
    "tech":       "[Tec]",
    "health":     "[Hlt]",
    "space":      "[Spc]",
    "psychology": "[Psy]",
}


class InterestScreen(Screen):

    def __init__(self, from_settings=False, **kwargs):
        super().__init__(**kwargs)
        self.from_settings = from_settings

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(14))

        with root.canvas.before:
            Color(*T("bg"))
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        root.add_widget(Widget(size_hint_y=0.04))
        root.add_widget(Label(
            text=S("interest_title"),
            font_size=dp(26), bold=True, color=T("text"),
            size_hint_y=None, height=dp(48)
        ))
        root.add_widget(Label(
            text=S("interest_sub"),
            font_size=dp(13), color=T("text3"),
            size_hint_y=None, height=dp(44),
            halign="center", text_size=(dp(320), None)
        ))
        root.add_widget(Widget(size_hint_y=0.02))

        grid = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        current = get_setting("interest")

        for key, label_text in INTERESTS:
            icon = INTEREST_ICONS.get(key, "[ ]")
            is_selected = (key == current)
            btn = Button(
                text=f"{icon}\n{label_text}",
                font_size=dp(14), bold=is_selected,
                background_color=(0, 0, 0, 0),
                color=T("accent_text") if is_selected else T("text"),
                size_hint_y=None, height=dp(78)
            )
            fill = T("accent") if is_selected else T("bg2")
            with btn.canvas.before:
                Color(*fill)
                bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(12)])
            btn.bind(
                size=lambda w, v, b=bg: setattr(b, 'size', v),
                pos=lambda w, v, b=bg: setattr(b, 'pos', v)
            )
            btn.bind(on_press=lambda _, k=key: self._choose(k))
            grid.add_widget(btn)

        root.add_widget(grid)
        root.add_widget(Widget(size_hint_y=1))

        confirm_btn = Button(
            text=S("save_settings") if self.from_settings else "Continue",
            font_size=dp(18), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(0.8, None), height=dp(56),
            pos_hint={"center_x": 0.5}
        )
        with confirm_btn.canvas.before:
            Color(*T("accent"))
            cb = RoundedRectangle(size=confirm_btn.size, pos=confirm_btn.pos, radius=[dp(14)])
        confirm_btn.bind(
            size=lambda w, v: setattr(cb, 'size', v),
            pos=lambda w, v: setattr(cb, 'pos', v)
        )
        confirm_btn.bind(on_press=self._confirm)
        root.add_widget(confirm_btn)
        root.add_widget(Widget(size_hint_y=0.03))
        self.add_widget(root)

    def _choose(self, key):
        save_setting("interest", key)
        self.clear_widgets()
        self._build_ui()

    def _confirm(self, *args):
        if not get_setting("interest"):
            save_setting("interest", "health")
        self.manager.transition.direction = "left"
        self.manager.current = "settings" if self.from_settings else "home"
