

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

from data.settings import set_value as save_setting


class LanguageScreen(Screen):
    """Choose app language: English or Arabic."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(40), spacing=dp(20))

        with root.canvas.before:
            Color(0.07, 0.07, 0.12, 1)
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        root.add_widget(Widget(size_hint_y=0.15))

        # Globe icon (text-based, safe on all systems)
        root.add_widget(Label(
            text="( * )",
            font_size=dp(40),
            color=(0.4, 0.9, 0.7, 1),
            size_hint_y=None,
            height=dp(60)
        ))

        root.add_widget(Label(
            text="Choose Language  /  اختر اللغة",
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(50),
            halign="center",
            text_size=(dp(340), None)
        ))

        root.add_widget(Widget(size_hint_y=0.05))

        # ── English button ────────────────────────────────────────────────
        en_btn = self._make_btn("English", primary=True)
        en_btn.bind(on_press=lambda *a: self._choose("en"))

        # ── Arabic button ─────────────────────────────────────────────────
        ar_btn = self._make_btn("العربية", primary=False)
        ar_btn.bind(on_press=lambda *a: self._choose("ar"))

        root.add_widget(en_btn)
        root.add_widget(ar_btn)
        root.add_widget(Widget(size_hint_y=1))

        self.add_widget(root)

    def _make_btn(self, text, primary):
        """Create a styled choice button."""
        btn = Button(
            text=text,
            font_size=dp(22),
            bold=True,
            background_color=(0, 0, 0, 0),
            color=(0.07, 0.07, 0.12, 1) if primary else (0.4, 0.9, 0.7, 1),
            size_hint=(0.8, None),
            height=dp(64),
            pos_hint={"center_x": 0.5}
        )
        if primary:
            # Filled green button
            with btn.canvas.before:
                Color(0.4, 0.9, 0.7, 1)
                bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(14)])
            btn.bind(
                size=lambda w, v: setattr(bg, 'size', v),
                pos=lambda w, v: setattr(bg, 'pos', v)
            )
        else:
            # Outlined button
            btn.color = (0.4, 0.9, 0.7, 1)
            with btn.canvas.before:
                Color(0.4, 0.9, 0.7, 0.3)
                bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(14)])
            btn.bind(
                size=lambda w, v: setattr(bg, 'size', v),
                pos=lambda w, v: setattr(bg, 'pos', v)
            )
        return btn

    def _choose(self, lang):
        """Save choice and go to interest screen."""
        save_setting("language", lang)
        # Also prime the TTS engine for this language
        try:
            from logic.voice import set_language
            set_language(lang)
        except Exception:
            pass
        self.manager.transition.direction = "left"
        self.manager.current = "interest"
