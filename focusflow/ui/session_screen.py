"""
ui/session_screen.py  —  theme-aware, with interactive Tasks panel
Tasks panel: toggle done, add new task, delete task
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.core.window import Window

from logic.timer import FocusTimer
from logic.facts import get_fact_sequence
from logic.strings import S
from data.storage import save_session
from data.theme import T


# ── Progress ring ─────────────────────────────────────────────────────────────

class ProgressRing(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0.0
        self.bind(size=self._draw, pos=self._draw)

    def update_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        radius = min(self.width, self.height) * 0.42
        thickness = dp(8)
        with self.canvas:
            Color(*T("ring_track"))
            Line(circle=(cx, cy, radius), width=thickness)
            if self.progress > 0:
                Color(*T("accent"))
                angle_end = 90 - (360 * self.progress)
                Line(
                    ellipse=(cx - radius, cy - radius,
                              radius * 2, radius * 2,
                              angle_end, 90),
                    width=thickness, cap="round",
                )


# ── Tasks panel ───────────────────────────────────────────────────────────────

class TasksPanel(FloatLayout):
    """
    Floating panel — toggle done, add, delete tasks without leaving session.
    """

    PRIORITY_COLORS = {
        "high":   (0.90, 0.30, 0.30, 1),
        "normal": (0.40, 0.70, 0.95, 1),
        "low":    (0.55, 0.75, 0.45, 1),
    }

    def __init__(self, on_close, **kwargs):
        super().__init__(**kwargs)
        self._on_close = on_close
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        W = Window.width
        H = Window.height

        # Dim overlay — tap outside panel to close
        overlay = Button(
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
        )
        with overlay.canvas.before:
            Color(0, 0, 0, 0.5)
            Rectangle(size=overlay.size, pos=overlay.pos)
        overlay.bind(on_press=lambda *a: self._on_close())
        self.add_widget(overlay)

        # Panel card
        self._panel_w = min(W * 0.88, dp(340))
        self._panel_h = min(H * 0.70, dp(500))

        self._panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(self._panel_w, self._panel_h),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
            spacing=0,
        )
        with self._panel.canvas.before:
            Color(*T("bg2"))
            p_bg = RoundedRectangle(
                size=self._panel.size, pos=self._panel.pos, radius=[dp(16)]
            )
        self._panel.bind(
            size=lambda w, v: setattr(p_bg, 'size', v),
            pos=lambda w, v: setattr(p_bg, 'pos', v),
        )

        self._panel.add_widget(self._build_header())
        self._panel.add_widget(self._build_list())
        self._panel.add_widget(self._build_add_row())

        self.add_widget(self._panel)

    def _build_header(self):
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(50),
            padding=[dp(16), dp(8), dp(10), dp(8)],
        )
        with header.canvas.before:
            Color(*T("bg3"))
            h_bg = RoundedRectangle(
                size=header.size, pos=header.pos,
                radius=[dp(16), dp(16), 0, 0],
            )
        header.bind(
            size=lambda w, v: setattr(h_bg, 'size', v),
            pos=lambda w, v: setattr(h_bg, 'pos', v),
        )
        header.add_widget(Label(
            text="My Tasks",
            font_size=dp(17), bold=True,
            color=T("text"),
            halign="left",
            text_size=(self._panel_w - dp(60), None),
        ))
        close_btn = Button(
            text="X",
            font_size=dp(15), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("text3"),
            size_hint=(None, 1), width=dp(38),
        )
        close_btn.bind(on_press=lambda *a: self._on_close())
        header.add_widget(close_btn)
        return header

    def _build_list(self):
        """Scrollable list — rebuilt on every change."""
        self._scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self._list_layout = GridLayout(
            cols=1, spacing=dp(6),
            size_hint_y=None,
            padding=[dp(10), dp(8), dp(10), dp(8)],
        )
        self._list_layout.bind(minimum_height=self._list_layout.setter("height"))
        self._populate_list()
        self._scroll.add_widget(self._list_layout)
        return self._scroll

    def _populate_list(self):
        self._list_layout.clear_widgets()
        try:
            from data.todo_storage import load_todos
            todos = load_todos()
        except Exception:
            todos = []

        if not todos:
            self._list_layout.add_widget(Label(
                text="No tasks yet.\nUse the field below to add one.",
                font_size=dp(13), color=T("text3"),
                halign="center",
                text_size=(self._panel_w - dp(24), None),
                size_hint_y=None, height=dp(60),
            ))
            return

        for todo in todos:
            self._list_layout.add_widget(self._task_row(todo))

    def _task_row(self, todo):
        is_done  = todo.get("done", False)
        priority = todo.get("priority", "normal")
        p_col    = self.PRIORITY_COLORS.get(priority, self.PRIORITY_COLORS["normal"])

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(48),
            spacing=dp(6),
            padding=[dp(8), dp(6), dp(6), dp(6)],
        )
        with row.canvas.before:
            Color(*T("bg")[:3], 0.5 if is_done else 1.0)
            r_bg = RoundedRectangle(size=row.size, pos=row.pos, radius=[dp(10)])
        row.bind(
            size=lambda w, v, b=r_bg: setattr(b, 'size', v),
            pos=lambda w, v, b=r_bg: setattr(b, 'pos', v),
        )

        # Priority colour bar
        bar = Widget(size_hint=(None, 1), width=dp(5))
        with bar.canvas:
            Color(*p_col[:3], 0.35 if is_done else 1.0)
            RoundedRectangle(
                size=(dp(4), dp(28)),
                pos=(bar.x, bar.y + dp(10)),
                radius=[dp(2)],
            )
        row.add_widget(bar)

        # ── Checkbox button — tap to toggle done ──────────────────────────
        check_btn = Button(
            text="[x]" if is_done else "[ ]",
            font_size=dp(14), bold=is_done,
            background_color=(0, 0, 0, 0),
            color=(0.35, 0.80, 0.45, 1) if is_done else T("text3"),
            size_hint=(None, 1), width=dp(36),
        )
        check_btn.bind(on_press=lambda _, tid=todo["id"]: self._toggle(tid))
        row.add_widget(check_btn)

        # Task text — tap to toggle done too
        task_btn = Button(
            text=todo.get("text", ""),
            font_size=dp(14),
            background_color=(0, 0, 0, 0),
            color=T("text3") if is_done else T("text"),
            halign="left", valign="middle",
            text_size=(self._panel_w - dp(120), None),
            strikethrough=is_done,
            size_hint=(1, 1),
        )
        task_btn.bind(on_press=lambda _, tid=todo["id"]: self._toggle(tid))
        row.add_widget(task_btn)

        # ── Delete button ─────────────────────────────────────────────────
        del_btn = Button(
            text="X",
            font_size=dp(13), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("danger"),
            size_hint=(None, 1), width=dp(32),
        )
        del_btn.bind(on_press=lambda _, tid=todo["id"]: self._delete(tid))
        row.add_widget(del_btn)

        return row

    def _build_add_row(self):
        """Text input + Add button at the bottom of the panel."""
        area = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(54),
            padding=[dp(10), dp(8), dp(10), dp(8)],
            spacing=dp(8),
        )
        with area.canvas.before:
            Color(*T("bg3"))
            a_bg = RoundedRectangle(
                size=area.size, pos=area.pos,
                radius=[0, 0, dp(16), dp(16)],
            )
        area.bind(
            size=lambda w, v: setattr(a_bg, 'size', v),
            pos=lambda w, v: setattr(a_bg, 'pos', v),
        )

        self._input = TextInput(
            hint_text="New task...",
            font_size=dp(14),
            multiline=False,
            size_hint=(1, None), height=dp(38),
            background_color=T("bg2"),
            foreground_color=T("text"),
            hint_text_color=T("text3"),
            cursor_color=T("accent"),
            padding=[dp(10), dp(8)],
        )
        self._input.bind(on_text_validate=self._add_task)
        area.add_widget(self._input)

        add_btn = Button(
            text="Add",
            font_size=dp(14), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(None, None), size=(dp(56), dp(38)),
        )
        with add_btn.canvas.before:
            Color(*T("accent"))
            ab_bg = RoundedRectangle(size=add_btn.size, pos=add_btn.pos, radius=[dp(10)])
        add_btn.bind(
            size=lambda w, v: setattr(ab_bg, 'size', v),
            pos=lambda w, v: setattr(ab_bg, 'pos', v),
        )
        add_btn.bind(on_press=self._add_task)
        area.add_widget(add_btn)

        return area

    # ── Actions ───────────────────────────────────────────────────────────

    def _toggle(self, todo_id):
        try:
            from data.todo_storage import toggle_todo
            toggle_todo(todo_id)
        except Exception:
            pass
        self._populate_list()

    def _delete(self, todo_id):
        try:
            from data.todo_storage import delete_todo
            delete_todo(todo_id)
        except Exception:
            pass
        self._populate_list()

    def _add_task(self, *args):
        text = self._input.text.strip()
        if not text:
            return
        try:
            from data.todo_storage import add_todo
            add_todo(text, priority="normal")
        except Exception:
            pass
        self._input.text = ""
        self._populate_list()


# ── Session screen ────────────────────────────────────────────────────────────

class SessionScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer        = None
        self._facts       = []
        self._fact_index  = 0
        self._ui_built    = False
        self._tasks_panel = None
        self._root        = None

    def on_enter(self):
        Window.clearcolor = T("bg")

    def start_session(self, duration_seconds):
        self._facts = get_fact_sequence()
        self._fact_index = 0
        if self._ui_built:
            self.clear_widgets()
            self._ui_built = False
        self._build_ui(duration_seconds)
        self._ui_built = True
        self.timer = FocusTimer(
            duration=duration_seconds,
            on_tick=self._on_tick,
            on_fact_rotate=self._rotate_fact,
            on_complete=self._on_complete,
        )
        self.timer.start()
        self._show_fact(self._facts[0])

    def _build_ui(self, duration_seconds):
        self._root = FloatLayout()
        root = self._root

        with root.canvas.before:
            Color(*T("bg"))
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        # Ring
        ring_size = min(Window.width * 0.65, dp(260))
        self.ring = ProgressRing(
            size_hint=(None, None), size=(ring_size, ring_size),
            pos_hint={"center_x": 0.5, "center_y": 0.58},
        )
        root.add_widget(self.ring)

        # Timer
        self.timer_label = Label(
            text=FocusTimer.format_time(duration_seconds),
            font_size=dp(54), bold=True, color=T("text"),
            size_hint=(None, None), size=(ring_size, dp(70)),
            pos_hint={"center_x": 0.5, "center_y": 0.60},
        )
        root.add_widget(self.timer_label)

        # Focusing tag
        root.add_widget(Label(
            text=S("focusing_tag"),
            font_size=dp(13), color=(*T("accent")[:3], 0.8),
            size_hint=(None, None), size=(dp(240), dp(28)),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        ))

        # Fact
        self.fact_label = Label(
            text="", font_size=dp(15),
            color=(*T("text2")[:3], 0),
            halign="center", valign="middle",
            text_size=(Window.width * 0.82, None),
            size_hint=(None, None),
            size=(Window.width * 0.82, dp(90)),
            pos_hint={"center_x": 0.5, "center_y": 0.27},
        )
        root.add_widget(self.fact_label)

        # ── Tasks button — top-right ──────────────────────────────────────
        tasks_btn = Button(
            text="[=]",
            font_size=dp(15), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent"),
            size_hint=(None, None), size=(dp(44), dp(44)),
            pos_hint={"right": 0.96, "top": 0.96},
        )
        with tasks_btn.canvas.before:
            Color(*T("bg2"))
            tb_bg = RoundedRectangle(
                size=tasks_btn.size, pos=tasks_btn.pos, radius=[dp(10)]
            )
        tasks_btn.bind(
            size=lambda w, v: setattr(tb_bg, 'size', v),
            pos=lambda w, v: setattr(tb_bg, 'pos', v),
        )
        tasks_btn.bind(on_press=self._show_tasks)
        root.add_widget(tasks_btn)

        # End session
        abandon_btn = Button(
            text=S("end_session"), font_size=dp(15),
            background_color=(0, 0, 0, 0),
            color=T("danger"),
            size_hint=(None, None), size=(dp(160), dp(44)),
            pos_hint={"center_x": 0.5, "center_y": 0.08},
        )
        with abandon_btn.canvas.before:
            Color(*T("danger")[:3], 0.18)
            abd_bg = RoundedRectangle(
                size=abandon_btn.size, pos=abandon_btn.pos, radius=[dp(10)]
            )
        abandon_btn.bind(
            size=lambda w, v: setattr(abd_bg, 'size', v),
            pos=lambda w, v: setattr(abd_bg, 'pos', v),
        )
        abandon_btn.bind(on_press=self._abandon_session)
        root.add_widget(abandon_btn)

        self.add_widget(root)

    # ── Tasks panel ───────────────────────────────────────────────────────

    def _show_tasks(self, *args):
        if self._tasks_panel is not None:
            return
        self._tasks_panel = TasksPanel(
            on_close=self._hide_tasks,
            size_hint=(1, 1),
        )
        self._tasks_panel.opacity = 0
        self._root.add_widget(self._tasks_panel)
        Animation(opacity=1, duration=0.18).start(self._tasks_panel)

    def _hide_tasks(self, *args):
        if self._tasks_panel is None:
            return
        panel = self._tasks_panel
        self._tasks_panel = None
        anim = Animation(opacity=0, duration=0.15)
        anim.bind(on_complete=lambda *a: self._root.remove_widget(panel))
        anim.start(panel)

    # ── Timer callbacks ───────────────────────────────────────────────────

    def _on_tick(self, elapsed, remaining):
        self.timer_label.text = FocusTimer.format_time(remaining)
        self.ring.update_progress(elapsed / self.timer.total_duration)

    def _rotate_fact(self):
        self._fact_index = (self._fact_index + 1) % len(self._facts)
        new_fact = self._facts[self._fact_index]
        r, g, b = T("text2")[:3]
        fade = Animation(color=(r, g, b, 0), duration=0.4)
        fade.bind(on_complete=lambda *a: self._show_fact(new_fact))
        fade.start(self.fact_label)

    def _show_fact(self, fact_text):
        r, g, b = T("text2")[:3]
        self.fact_label.text = S("fact_prefix") + fact_text
        Animation(color=(r, g, b, 1), duration=0.6).start(self.fact_label)

    def _on_complete(self):
        save_session(self.timer.total_duration, success=True)
        self._go_to_result(success=True)

    def _abandon_session(self, *args):
        if self.timer:
            self.timer.stop()
        save_session(self.timer.total_duration, success=False)
        self._go_to_result(success=False)

    def _go_to_result(self, success):
        self._hide_tasks()
        rs = self.manager.get_screen("result")
        rs.show_result(
            success=success,
            duration=self.timer.total_duration,
            elapsed=self.timer.elapsed,
        )
        self.manager.transition.direction = "left"
        self.manager.current = "result"

    def on_leave(self):
        self._hide_tasks()
        if self.timer and self.timer.running:
            self.timer.stop()
            if not self.timer.completed:
                save_session(self.timer.total_duration, success=False)