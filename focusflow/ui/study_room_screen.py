"""
ui/study_room_screen.py
------------------------
Lobby screen: Create a room or join with a code.
Matches FocusFlow dark/light theme.
"""

import uuid
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window

from data.theme import T
from data.settings import get as get_setting

# Reuse same user ID across sessions (stored in settings)
from data.settings import get as get_setting, set_value as save_setting


def get_or_create_user_id():
    """Persist a unique user ID so the same user is recognised across sessions."""
    uid = get_setting("user_id")
    if not uid:
        uid = str(uuid.uuid4())[:8]
        save_setting("user_id", uid)
    return uid


class StudyRoomScreen(Screen):
    """Lobby: enter name, create or join a room."""

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    def _build_ui(self):
        W   = Window.width
        pad = W * 0.07
        tw  = W - pad * 2

        root = BoxLayout(
            orientation="vertical",
            padding=[pad, dp(24), pad, dp(16)],
            spacing=dp(14),
        )
        with root.canvas.before:
            Color(*T("bg"))
            bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        # ── Back ──────────────────────────────────────────────────────────
        back_btn = Button(
            text="< Back",
            font_size=dp(14), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent"),
            size_hint=(None, None), size=(dp(70), dp(36)),
        )
        back_btn.bind(on_press=lambda *a: self._go_back())
        root.add_widget(back_btn)

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Title ─────────────────────────────────────────────────────────
        root.add_widget(Label(
            text="Study Room",
            font_size=dp(34), bold=True,
            color=T("accent"),
            size_hint_y=None, height=dp(50),
            halign="center", text_size=(tw, None),
        ))
        root.add_widget(Label(
            text="Study together in real time",
            font_size=dp(13),
            color=T("text3"),
            size_hint_y=None, height=dp(24),
            halign="center", text_size=(tw, None),
        ))

        root.add_widget(Widget(size_hint_y=0.03))

        # ── Your name ─────────────────────────────────────────────────────
        root.add_widget(self._section_label("Your display name"))
        self._name_input = self._text_field("e.g. Alice")
        root.add_widget(self._name_input)

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Create room ───────────────────────────────────────────────────
        root.add_widget(self._section_label("Create a new room"))
        self._room_name_input = self._text_field("Room name (optional)")
        root.add_widget(self._room_name_input)

        create_btn = self._green_btn("Create Room")
        create_btn.bind(on_press=self._create_room)
        root.add_widget(create_btn)

        # ── Divider ───────────────────────────────────────────────────────
        root.add_widget(Label(
            text="— or —",
            font_size=dp(13), color=T("text3"),
            size_hint_y=None, height=dp(28),
            halign="center", text_size=(tw, None),
        ))

        # ── Join room ─────────────────────────────────────────────────────
        root.add_widget(self._section_label("Join with a room code"))
        self._code_input = self._text_field("6-letter code (e.g. AB12CD)")
        root.add_widget(self._code_input)

        join_btn = self._outline_btn("Join Room")
        join_btn.bind(on_press=self._join_room)
        root.add_widget(join_btn)

        # ── Status label ──────────────────────────────────────────────────
        self._status_label = Label(
            text="",
            font_size=dp(13),
            color=T("danger"),
            size_hint_y=None, height=dp(30),
            halign="center", text_size=(tw, None),
        )
        root.add_widget(self._status_label)

        root.add_widget(Widget(size_hint_y=1))
        self.add_widget(root)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _section_label(self, text):
        return Label(
            text=text,
            font_size=dp(12), color=T("text3"),
            size_hint_y=None, height=dp(20),
            halign="left", text_size=(Window.width * 0.86, None),
        )

    def _text_field(self, hint):
        return TextInput(
            hint_text=hint,
            font_size=dp(15),
            multiline=False,
            size_hint_y=None, height=dp(46),
            background_color=T("bg2"),
            foreground_color=T("text"),
            hint_text_color=T("text3"),
            cursor_color=T("accent"),
            padding=[dp(12), dp(12)],
        )

    def _green_btn(self, text):
        btn = Button(
            text=text,
            font_size=dp(16), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(1, None), height=dp(50),
        )
        with btn.canvas.before:
            Color(*T("accent"))
            bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(12)])
        btn.bind(
            size=lambda w, v: setattr(bg, 'size', v),
            pos=lambda w, v: setattr(bg, 'pos', v),
        )
        return btn

    def _outline_btn(self, text):
        btn = Button(
            text=text,
            font_size=dp(16), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent"),
            size_hint=(1, None), height=dp(50),
        )
        with btn.canvas.before:
            Color(*T("accent")[:3], 0.15)
            bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(12)])
        btn.bind(
            size=lambda w, v: setattr(bg, 'size', v),
            pos=lambda w, v: setattr(bg, 'pos', v),
        )
        return btn

    def _set_status(self, msg, error=True):
        self._status_label.color = T("danger") if error else (0.4, 0.85, 0.5, 1)
        self._status_label.text  = msg

    # ── Actions ───────────────────────────────────────────────────────────

    def _create_room(self, *args):
        from network.firebase import create_room

        user_name = self._name_input.text.strip() or "Anon"
        room_name = self._room_name_input.text.strip() or f"{user_name}'s Room"
        user_id   = get_or_create_user_id()

        self._set_status("Creating room...", error=False)

        import threading
        def _bg():
            code = create_room(room_name, user_id, user_name)
            from kivy.clock import Clock
            if code:
                Clock.schedule_once(lambda dt: self._enter_room(code, user_id, user_name))
            else:
                Clock.schedule_once(lambda dt: self._set_status("Failed. Check Firebase URL."))
        threading.Thread(target=_bg, daemon=True).start()

    def _join_room(self, *args):
        from network.firebase import join_room

        user_name = self._name_input.text.strip() or "Anon"
        code      = self._code_input.text.strip().upper()
        user_id   = get_or_create_user_id()

        if len(code) != 6:
            self._set_status("Enter a valid 6-character code.")
            return

        self._set_status("Joining room...", error=False)

        import threading
        def _bg():
            ok = join_room(code, user_id, user_name)
            from kivy.clock import Clock
            if ok:
                Clock.schedule_once(lambda dt: self._enter_room(code, user_id, user_name))
            else:
                Clock.schedule_once(lambda dt: self._set_status("Room not found. Check the code."))
        threading.Thread(target=_bg, daemon=True).start()

    def _enter_room(self, room_code, user_id, user_name):
        """Navigate to the room screen."""
        room_screen = self.manager.get_screen("room")
        room_screen.setup(room_code, user_id, user_name)
        self.manager.transition.direction = "left"
        self.manager.current = "room"

    def _go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
