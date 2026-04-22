"""
ui/login_screen.py
------------------
Google Sign-In screen using the Device Authorization Flow.

Flow:
1. User taps "Sign in with Google"
2. App requests a device code from Google
3. Screen shows a short code and URL for the user to visit
4. App polls Google in the background
5. Once approved → navigate to home
6. User can also skip login (guest mode)
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window

from data.auth import (
    DeviceFlowSession, is_logged_in, get_current_user,
    credentials_configured
)
from data.theme import T


class LoginScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session = None

    def on_pre_enter(self):
        self.clear_widgets()
        # If already logged in, skip straight through
        if is_logged_in():
            Clock.schedule_once(lambda dt: self._proceed(), 0)
            return
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    def _build_ui(self, status_msg="", code=None, url=None, polling=False):
        root = BoxLayout(orientation="vertical", padding=dp(32), spacing=dp(16))

        with root.canvas.before:
            Color(*T("bg"))
            bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        root.add_widget(Widget(size_hint_y=0.12))

        # App title
        root.add_widget(Label(
            text="FocusFlow",
            font_size=dp(42), bold=True,
            color=T("accent"),
            size_hint_y=None, height=dp(64)
        ))
        root.add_widget(Label(
            text="Train your attention.",
            font_size=dp(14), color=T("text3"),
            size_hint_y=None, height=dp(28)
        ))

        root.add_widget(Widget(size_hint_y=0.06))

        # ── Device code card (shown after sign-in starts) ─────────────────
        if code and url:
            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None, height=dp(160),
                padding=dp(18), spacing=dp(10)
            )
            with card.canvas.before:
                Color(*T("bg2"))
                card_bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(14)])
            card.bind(
                size=lambda w, v: setattr(card_bg, 'size', v),
                pos=lambda w, v: setattr(card_bg, 'pos', v)
            )
            card.add_widget(Label(
                text="1. Open this URL on any device:",
                font_size=dp(13), color=T("text3"),
                size_hint_y=None, height=dp(22)
            ))
            card.add_widget(Label(
                text=url,
                font_size=dp(14), bold=True, color=T("accent"),
                size_hint_y=None, height=dp(26)
            ))
            card.add_widget(Label(
                text="2. Enter this code:",
                font_size=dp(13), color=T("text3"),
                size_hint_y=None, height=dp(22)
            ))
            card.add_widget(Label(
                text=code,
                font_size=dp(36), bold=True, color=T("text"),
                size_hint_y=None, height=dp(52)
            ))
            root.add_widget(card)

        # ── Status message ────────────────────────────────────────────────
        if status_msg:
            root.add_widget(Label(
                text=status_msg,
                font_size=dp(13), color=T("text2"),
                halign="center", text_size=(dp(320), None),
                size_hint_y=None, height=dp(44)
            ))

        root.add_widget(Widget(size_hint_y=1))

        # ── Buttons ───────────────────────────────────────────────────────
        if not polling:
            if not credentials_configured():
                # Show setup instructions instead of button
                root.add_widget(Label(
                    text="Google Sign-In not configured.\nSee google_credentials.json to set up.",
                    font_size=dp(13), color=T("text3"),
                    halign="center", text_size=(dp(310), None),
                    size_hint_y=None, height=dp(52)
                ))
            else:
                signin_btn = self._make_btn("Sign in with Google", filled=True)
                signin_btn.bind(on_press=self._start_signin)
                root.add_widget(signin_btn)

        else:
            # Cancel button while polling
            cancel_btn = self._make_btn("Cancel", filled=False)
            cancel_btn.bind(on_press=self._cancel_signin)
            root.add_widget(cancel_btn)

        # Guest / skip button
        guest_btn = Button(
            text="Continue as Guest",
            font_size=dp(13),
            background_color=(0, 0, 0, 0),
            color=T("text3"),
            size_hint_y=None, height=dp(36)
        )
        guest_btn.bind(on_press=lambda *a: self._proceed())
        root.add_widget(guest_btn)

        root.add_widget(Widget(size_hint_y=0.04))
        self.add_widget(root)

    def _make_btn(self, text, filled=True):
        btn = Button(
            text=text, font_size=dp(17), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text") if filled else T("accent"),
            size_hint=(0.85, None), height=dp(54),
            pos_hint={"center_x": 0.5}
        )
        if filled:
            with btn.canvas.before:
                Color(*T("accent"))
                bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(14)])
            btn.bind(
                size=lambda w, v: setattr(bg, 'size', v),
                pos=lambda w, v: setattr(bg, 'pos', v)
            )
        else:
            with btn.canvas.before:
                Color(*T("accent")[:3], 0.15)
                bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(14)])
            btn.bind(
                size=lambda w, v: setattr(bg, 'size', v),
                pos=lambda w, v: setattr(bg, 'pos', v)
            )
        return btn

    def _start_signin(self, *args):
        self._session = DeviceFlowSession()
        ok, err = self._session.start()

        if not ok:
            self.clear_widgets()
            self._build_ui(status_msg=f"Error: {err}")
            return

        code = self._session.user_code
        url  = self._session.verification_url

        self.clear_widgets()
        self._build_ui(
            code=code, url=url,
            status_msg="Waiting for you to approve in the browser...",
            polling=True
        )

        self._session.poll(
            on_success=self._on_login_success,
            on_error=self._on_login_error
        )

    def _cancel_signin(self, *args):
        if self._session:
            self._session.cancel()
            self._session = None
        self.clear_widgets()
        self._build_ui()

    def _on_login_success(self, user_info):
        """Called from polling thread — schedule UI update on main thread."""
        Clock.schedule_once(lambda dt: self._handle_success(user_info), 0)

    def _handle_success(self, user_info):
        name = user_info.get("name", "User")
        self.clear_widgets()
        self._build_ui(status_msg=f"Welcome, {name}! Signing you in...")
        Clock.schedule_once(lambda dt: self._proceed(), 1.2)

    def _on_login_error(self, message):
        Clock.schedule_once(lambda dt: self._handle_error(message), 0)

    def _handle_error(self, message):
        self.clear_widgets()
        self._build_ui(status_msg=f"Sign-in failed: {message}")

    def _proceed(self):
        """Go to interest screen (first launch) or home."""
        from data.settings import load_settings
        settings = load_settings()
        self.manager.transition.direction = "left"
        self.manager.current = "interest" if not settings.get("interest") else "home"
