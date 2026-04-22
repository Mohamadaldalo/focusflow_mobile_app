"""
ui/room_screen.py
-----------------
Main study room screen.

Layout (top to bottom):
  [Header: room name + code + leave button]
  [Users bar: avatars of online members]
  [Pomodoro timer: big countdown + phase label + start/stop]
  [Chat: scrollable messages + input field]

Polling schedule:
  - Users + timer: every 3 seconds
  - Messages:      every 3 seconds
  - Presence ping: every 10 seconds
"""

import threading
import time

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock

from data.theme import T


class RoomScreen(Screen):

    # ── Setup (called before entering screen) ─────────────────────────────
    def setup(self, room_code, user_id, user_name):
        self._room_code  = room_code
        self._user_id    = user_id
        self._user_name  = user_name
        self._last_msg_ts = 0          # only fetch new messages
        self._poll_event  = None
        self._ping_event  = None
        self._timer_running = False
        self._messages   = []

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")
        # Start polling every 3 seconds
        self._poll_event = Clock.schedule_interval(self._poll, 3)
        # Presence ping every 10 seconds
        self._ping_event = Clock.schedule_interval(self._send_ping, 10)
        # First poll immediately
        self._poll(0)

    def on_leave(self):
        # Stop all polling
        if self._poll_event:
            self._poll_event.cancel()
        if self._ping_event:
            self._ping_event.cancel()
        # Leave room in background
        threading.Thread(target=self._bg_leave, daemon=True).start()

    def _bg_leave(self):
        from network.firebase import leave_room
        leave_room(self._room_code, self._user_id)

    # ── Build UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        W   = Window.width
        pad = W * 0.04

        root = BoxLayout(
            orientation="vertical",
            spacing=0,
        )
        with root.canvas.before:
            Color(*T("bg"))
            bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        root.add_widget(self._build_header(pad))
        root.add_widget(self._build_users_bar(pad))
        root.add_widget(self._build_timer_section(pad))
        root.add_widget(self._build_chat_section(pad))
        root.add_widget(self._build_chat_input(pad))

        self.add_widget(root)

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self, pad):
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(56),
            padding=[pad, dp(8), pad, dp(8)],
            spacing=dp(8),
        )
        with header.canvas.before:
            Color(*T("bg2"))
            h_bg = Rectangle(size=header.size, pos=header.pos)
        header.bind(
            size=lambda w, v: setattr(h_bg, 'size', v),
            pos=lambda w, v: setattr(h_bg, 'pos', v),
        )

        # Room name
        self._room_name_lbl = Label(
            text=f"Room: {self._room_code}",
            font_size=dp(16), bold=True,
            color=T("text"),
            halign="left", text_size=(Window.width * 0.5, None),
        )
        header.add_widget(self._room_name_lbl)

        # Code badge
        code_lbl = Label(
            text=f"Code: {self._room_code}",
            font_size=dp(12),
            color=T("accent"),
            size_hint=(None, 1), width=dp(100),
        )
        header.add_widget(code_lbl)

        # Leave button
        leave_btn = Button(
            text="Leave",
            font_size=dp(13), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("danger"),
            size_hint=(None, 1), width=dp(56),
        )
        with leave_btn.canvas.before:
            Color(*T("danger")[:3], 0.18)
            l_bg = RoundedRectangle(size=leave_btn.size, pos=leave_btn.pos, radius=[dp(8)])
        leave_btn.bind(
            size=lambda w, v: setattr(l_bg, 'size', v),
            pos=lambda w, v: setattr(l_bg, 'pos', v),
        )
        leave_btn.bind(on_press=self._leave)
        header.add_widget(leave_btn)

        return header

    # ── Users bar ─────────────────────────────────────────────────────────

    def _build_users_bar(self, pad):
        container = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(66),
            padding=[pad, dp(4), pad, dp(4)],
        )
        with container.canvas.before:
            Color(*T("bg3"))
            c_bg = Rectangle(size=container.size, pos=container.pos)
        container.bind(
            size=lambda w, v: setattr(c_bg, 'size', v),
            pos=lambda w, v: setattr(c_bg, 'pos', v),
        )

        self._users_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None, height=dp(58),
        )
        container.add_widget(self._users_layout)
        return container

    def _refresh_users(self, users):
        """Rebuild the users bar with current online list."""
        self._users_layout.clear_widgets()
        for u in users[:10]:   # max 10 shown
            name = u["name"]
            initial = name[0].upper() if name else "?"

            col = BoxLayout(
                orientation="vertical",
                size_hint=(None, 1), width=dp(44),
                spacing=dp(2),
            )
            # Avatar circle
            avatar = Widget(size_hint=(None, None), size=(dp(32), dp(32)))
            # Pick a colour from name hash
            hue = hash(name) % 6
            avatar_colors = [
                (0.4, 0.9, 0.7, 1),   # mint
                (0.4, 0.6, 1.0, 1),   # blue
                (1.0, 0.7, 0.3, 1),   # orange
                (0.9, 0.4, 0.6, 1),   # pink
                (0.6, 0.5, 1.0, 1),   # purple
                (0.4, 0.85, 0.5, 1),  # green
            ]
            av_col = avatar_colors[hue]
            with avatar.canvas:
                Color(*av_col)
                Ellipse(size=avatar.size, pos=avatar.pos)
            av_lbl = Label(
                text=initial,
                font_size=dp(14), bold=True,
                color=(0.07, 0.07, 0.12, 1),
                size_hint=(None, None), size=(dp(32), dp(32)),
            )
            # Stack avatar and label using a FloatLayout trick
            from kivy.uix.floatlayout import FloatLayout
            fl = FloatLayout(size_hint=(None, None), size=(dp(32), dp(32)))
            fl.add_widget(avatar)
            av_lbl.pos_hint = {"center_x": 0.5, "center_y": 0.5}
            fl.add_widget(av_lbl)

            col.add_widget(Widget(size_hint_y=1))
            col.add_widget(fl)
            col.add_widget(Label(
                text=name[:6],
                font_size=dp(9),
                color=T("text3"),
                size_hint_y=None, height=dp(14),
                halign="center",
            ))
            col.add_widget(Widget(size_hint_y=1))
            self._users_layout.add_widget(col)

        if not users:
            self._users_layout.add_widget(Label(
                text="No one online yet...",
                font_size=dp(12), color=T("text3"),
            ))

    # ── Timer ─────────────────────────────────────────────────────────────

    def _build_timer_section(self, pad):
        section = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(160),
            padding=[pad, dp(8), pad, dp(8)],
            spacing=dp(4),
        )
        with section.canvas.before:
            Color(*T("bg2"))
            s_bg = Rectangle(size=section.size, pos=section.pos)
        section.bind(
            size=lambda w, v: setattr(s_bg, 'size', v),
            pos=lambda w, v: setattr(s_bg, 'pos', v),
        )

        # Phase label
        self._phase_lbl = Label(
            text="FOCUS",
            font_size=dp(12), bold=True,
            color=T("accent"),
            size_hint_y=None, height=dp(20),
        )
        section.add_widget(self._phase_lbl)

        # Big timer
        self._timer_lbl = Label(
            text="25:00",
            font_size=dp(46), bold=True,
            color=T("text"),
            size_hint_y=None, height=dp(68),
        )
        section.add_widget(self._timer_lbl)

        # Control buttons
        btn_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(40),
            spacing=dp(12),
        )
        btn_row.add_widget(Widget(size_hint_x=1))

        self._start_btn = self._small_btn("Start Focus", accent=True)
        self._start_btn.bind(on_press=lambda *a: self._start_timer("focus"))
        btn_row.add_widget(self._start_btn)

        self._break_btn = self._small_btn("Start Break", accent=False)
        self._break_btn.bind(on_press=lambda *a: self._start_timer("break"))
        btn_row.add_widget(self._break_btn)

        btn_row.add_widget(Widget(size_hint_x=1))
        section.add_widget(btn_row)

        return section

    def _small_btn(self, text, accent=True):
        btn = Button(
            text=text,
            font_size=dp(13), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text") if accent else T("accent"),
            size_hint=(None, None), size=(dp(120), dp(36)),
        )
        col = T("accent") if accent else (*T("accent")[:3], 0.2)
        with btn.canvas.before:
            Color(*col)
            bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(10)])
        btn.bind(
            size=lambda w, v: setattr(bg, 'size', v),
            pos=lambda w, v: setattr(bg, 'pos', v),
        )
        return btn

    def _refresh_timer(self, timer_state):
        """Update timer display from fetched state."""
        from network.firebase import compute_remaining
        remaining, phase = compute_remaining(timer_state)

        mins = remaining // 60
        secs = remaining % 60
        self._timer_lbl.text  = f"{mins:02d}:{secs:02d}"
        self._phase_lbl.text  = "FOCUS" if phase == "focus" else "BREAK"
        self._phase_lbl.color = T("accent") if phase == "focus" else (1.0, 0.72, 0.2, 1)

        # Auto-advance phase when timer hits 0
        if remaining == 0 and timer_state and timer_state.get("running"):
            next_phase = "break" if phase == "focus" else "focus"
            threading.Thread(
                target=lambda: self._bg_start_timer(next_phase), daemon=True
            ).start()

    # ── Chat ──────────────────────────────────────────────────────────────

    def _build_chat_section(self, pad):
        self._chat_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
        )
        self._chat_layout = GridLayout(
            cols=1, spacing=dp(4),
            size_hint_y=None,
            padding=[pad, dp(6), pad, dp(6)],
        )
        self._chat_layout.bind(minimum_height=self._chat_layout.setter("height"))
        self._chat_scroll.add_widget(self._chat_layout)
        return self._chat_scroll

    def _build_chat_input(self, pad):
        area = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(54),
            padding=[pad, dp(8), pad, dp(8)],
            spacing=dp(8),
        )
        with area.canvas.before:
            Color(*T("bg2"))
            a_bg = Rectangle(size=area.size, pos=area.pos)
        area.bind(
            size=lambda w, v: setattr(a_bg, 'size', v),
            pos=lambda w, v: setattr(a_bg, 'pos', v),
        )

        self._chat_input = TextInput(
            hint_text="Message the room...",
            font_size=dp(14),
            multiline=False,
            size_hint=(1, None), height=dp(38),
            background_color=T("bg3"),
            foreground_color=T("text"),
            hint_text_color=T("text3"),
            cursor_color=T("accent"),
            padding=[dp(10), dp(8)],
        )
        self._chat_input.bind(on_text_validate=self._send_message)
        area.add_widget(self._chat_input)

        send_btn = Button(
            text="Send",
            font_size=dp(14), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(None, None), size=(dp(60), dp(38)),
        )
        with send_btn.canvas.before:
            Color(*T("accent"))
            sb = RoundedRectangle(size=send_btn.size, pos=send_btn.pos, radius=[dp(10)])
        send_btn.bind(
            size=lambda w, v: setattr(sb, 'size', v),
            pos=lambda w, v: setattr(sb, 'pos', v),
        )
        send_btn.bind(on_press=self._send_message)
        area.add_widget(send_btn)

        return area

    def _add_message_bubble(self, user, text, is_mine):
        """Add a single chat bubble to the layout."""
        halign = "right" if is_mine else "left"
        name_color = T("accent") if is_mine else (0.7, 0.7, 0.9, 1)
        bubble_color = (*T("accent")[:3], 0.18) if is_mine else T("bg3")

        W = Window.width
        max_w = W * 0.75

        row = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
            padding=[dp(4), dp(2)],
        )

        name_lbl = Label(
            text=user,
            font_size=dp(10), bold=True,
            color=name_color,
            size_hint_y=None, height=dp(16),
            halign=halign,
            text_size=(W - dp(24), None),
        )
        row.add_widget(name_lbl)

        bubble = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            padding=[dp(10), dp(6)],
        )
        # Align bubble left or right
        if is_mine:
            bubble.pos_hint = {"right": 0.98}
        else:
            bubble.pos_hint = {"x": 0.02}

        txt_lbl = Label(
            text=text,
            font_size=dp(14),
            color=T("text"),
            halign=halign, valign="middle",
            text_size=(max_w - dp(20), None),
            size_hint_y=None,
        )
        txt_lbl.bind(texture_size=lambda w, v: setattr(txt_lbl, 'height', v[1]))
        bubble.add_widget(txt_lbl)

        # Calculate bubble height after texture
        def _set_sizes(lbl, ts):
            bubble.width  = min(ts[0] + dp(20), max_w)
            bubble.height = ts[1] + dp(12)
            row.height    = dp(16) + bubble.height + dp(8)

        txt_lbl.bind(texture_size=_set_sizes)

        with bubble.canvas.before:
            Color(*bubble_color)
            b_bg = RoundedRectangle(size=bubble.size, pos=bubble.pos, radius=[dp(10)])
        bubble.bind(
            size=lambda w, v: setattr(b_bg, 'size', v),
            pos=lambda w, v: setattr(b_bg, 'pos', v),
        )

        row.add_widget(bubble)
        row.height = dp(60)   # temporary; updated by texture callback
        self._chat_layout.add_widget(row)

        # Scroll to bottom
        Clock.schedule_once(lambda dt: setattr(self._chat_scroll, 'scroll_y', 0), 0.1)

    def _refresh_messages(self, messages):
        """Add only new messages to the chat layout."""
        for msg in messages:
            is_mine = (msg["user"] == self._user_name)
            self._add_message_bubble(msg["user"], msg["text"], is_mine)
            self._last_msg_ts = max(self._last_msg_ts, msg["ts"])

    # ── Polling ───────────────────────────────────────────────────────────

    def _poll(self, dt):
        """Fetch users, timer, and messages in a background thread."""
        threading.Thread(target=self._bg_poll, daemon=True).start()

    def _bg_poll(self):
        from network.firebase import (
            get_online_users, get_timer_state, get_messages, get_room_name
        )
        code = self._room_code

        users      = get_online_users(code)
        timer_state = get_timer_state(code)
        messages   = get_messages(code, since_ts=self._last_msg_ts)
        room_name  = get_room_name(code)

        # Update UI on the main thread
        Clock.schedule_once(lambda dt: self._apply_poll(
            users, timer_state, messages, room_name
        ))

    def _apply_poll(self, users, timer_state, messages, room_name):
        self._room_name_lbl.text = f"{room_name}  [{self._room_code}]"
        self._refresh_users(users)
        self._refresh_timer(timer_state)
        if messages:
            self._refresh_messages(messages)

    def _send_ping(self, dt):
        """Keep presence alive."""
        threading.Thread(target=self._bg_ping, daemon=True).start()

    def _bg_ping(self):
        from network.firebase import ping_presence
        ping_presence(self._room_code, self._user_id)

    # ── Actions ───────────────────────────────────────────────────────────

    def _send_message(self, *args):
        text = self._chat_input.text.strip()
        if not text:
            return
        self._chat_input.text = ""
        # Optimistic: show immediately
        self._add_message_bubble(self._user_name, text, is_mine=True)
        # Send in background
        threading.Thread(
            target=self._bg_send, args=(text,), daemon=True
        ).start()

    def _bg_send(self, text):
        from network.firebase import send_message
        send_message(self._room_code, self._user_name, text)

    def _start_timer(self, phase):
        threading.Thread(
            target=self._bg_start_timer, args=(phase,), daemon=True
        ).start()

    def _bg_start_timer(self, phase):
        from network.firebase import start_timer
        start_timer(self._room_code, phase)

    def _leave(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "study_room"
