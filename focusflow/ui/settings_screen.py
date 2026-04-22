"""
ui/settings_screen.py  —  theme-aware, with Google account section
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window

from data.settings import get as get_setting, INTERESTS
from data.auth import get_current_user, sign_out, credentials_configured
from logic.strings import S
from data.theme import T


class SettingsScreen(Screen):

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    def _build_ui(self):
        interest_key = get_setting("interest") or "health"
        interest_label = next(
            (label for k, label in INTERESTS if k == interest_key),
            interest_key
        )
        user = get_current_user()

        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))

        with root.canvas.before:
            Color(*T("bg"))
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        root.add_widget(Widget(size_hint_y=0.04))
        root.add_widget(Label(
            text=S("settings_title"),
            font_size=dp(28), bold=True,
            color=T("accent"),
            size_hint_y=None, height=dp(48)
        ))

        # ── Account section ───────────────────────────────────────────────
        root.add_widget(self._section_title("Account"))
        root.add_widget(self._account_card(user))

        # ── Preferences section ───────────────────────────────────────────
        root.add_widget(self._section_title(S("change_interest")))
        int_btn = self._row_button(interest_label)
        int_btn.bind(on_press=lambda *a: self._goto_interest())
        root.add_widget(int_btn)

        root.add_widget(Widget(size_hint_y=1))

        # ── Back button ───────────────────────────────────────────────────
        back_btn = Button(
            text=S("back_btn"), font_size=dp(18), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(0.8, None), height=dp(54),
            pos_hint={"center_x": 0.5}
        )
        with back_btn.canvas.before:
            Color(*T("accent"))
            bb = RoundedRectangle(size=back_btn.size, pos=back_btn.pos, radius=[dp(14)])
        back_btn.bind(
            size=lambda w, v: setattr(bb, 'size', v),
            pos=lambda w, v: setattr(bb, 'pos', v)
        )
        back_btn.bind(on_press=lambda *a: self._go_back())
        root.add_widget(back_btn)
        root.add_widget(Widget(size_hint_y=0.03))

        self.add_widget(root)

    def _section_title(self, text):
        return Label(
            text=text,
            font_size=dp(12), color=T("text3"),
            size_hint_y=None, height=dp(22),
            halign="left", text_size=(dp(340), None)
        )

    def _account_card(self, user):
        """Show logged-in user info OR sign-in prompt."""
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(100) if user else dp(68),
            padding=dp(14), spacing=dp(8)
        )
        with card.canvas.before:
            Color(*T("bg2"))
            c_bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(12)])
        card.bind(
            size=lambda w, v: setattr(c_bg, 'size', v),
            pos=lambda w, v: setattr(c_bg, 'pos', v)
        )

        if user:
            name  = user.get("name", "User")
            email = user.get("email", "")
            card.add_widget(Label(
                text=name, font_size=dp(15), bold=True,
                color=T("text"), halign="left",
                text_size=(dp(310), None),
                size_hint_y=None, height=dp(26)
            ))
            card.add_widget(Label(
                text=email, font_size=dp(12),
                color=T("text3"), halign="left",
                text_size=(dp(310), None),
                size_hint_y=None, height=dp(20)
            ))
            signout_btn = Button(
                text="Sign Out",
                font_size=dp(13),
                background_color=(0, 0, 0, 0),
                color=T("danger"),
                size_hint_y=None, height=dp(28),
                halign="left"
            )
            signout_btn.bind(on_press=self._sign_out)
            card.add_widget(signout_btn)
        else:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
            row.add_widget(Label(
                text="Not signed in",
                font_size=dp(14), color=T("text3"),
                size_hint_x=1, halign="left",
                text_size=(dp(200), None)
            ))
            if credentials_configured():
                signin_btn = Button(
                    text="Sign in with Google",
                    font_size=dp(13), bold=True,
                    background_color=(0, 0, 0, 0),
                    color=T("accent"),
                    size_hint=(None, 1), width=dp(160)
                )
                signin_btn.bind(on_press=lambda *a: self._goto_login())
                row.add_widget(signin_btn)
            card.add_widget(row)

        return card

    def _row_button(self, value_text):
        btn = Button(
            text=f"{value_text}  >>",
            font_size=dp(16),
            background_color=(0, 0, 0, 0),
            color=T("text"),
            size_hint=(1, None), height=dp(50)
        )
        with btn.canvas.before:
            Color(*T("bg2"))
            bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(10)])
        btn.bind(
            size=lambda w, v: setattr(bg, 'size', v),
            pos=lambda w, v: setattr(bg, 'pos', v)
        )
        return btn

    def _sign_out(self, *args):
        sign_out()
        self.clear_widgets()
        self._build_ui()

    def _goto_login(self):
        self.manager.transition.direction = "left"
        self.manager.current = "login"

    def _goto_interest(self):
        self.manager.get_screen("interest").from_settings = True
        self.manager.transition.direction = "left"
        self.manager.current = "interest"

    def _go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
