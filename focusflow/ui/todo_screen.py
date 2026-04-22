"""
ui/todo_screen.py
-----------------
Full-featured Todo List screen.

Features:
- Add tasks with priority (High / Normal / Low)
- Check off tasks (strikethrough style)
- Delete individual tasks
- Edit task text (tap text to edit)
- Clear all completed tasks
- Filter: All / Pending / Done
- Stats bar: X done, Y pending
- Theme-aware (dark / light)
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.animation import Animation

from data.todo_storage import (
    load_todos, add_todo, toggle_todo, delete_todo,
    edit_todo, clear_done, get_stats
)
from data.theme import T

# Priority colors (accent only — readable in both themes)
PRIORITY_COLORS = {
    "high":   (0.90, 0.30, 0.30, 1),   # red
    "normal": (0.40, 0.70, 0.95, 1),   # blue
    "low":    (0.55, 0.75, 0.45, 1),   # green
}
PRIORITY_LABELS = {"high": "!", "normal": "o", "low": "-"}

# Filter states
FILTERS = ["All", "Pending", "Done"]


class TodoScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._filter = "All"
        self._selected_priority = "normal"

    def on_pre_enter(self):
        self.clear_widgets()
        self._build_ui()

    def on_enter(self):
        Window.clearcolor = T("bg")

    # ─────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        with root.canvas.before:
            Color(*T("bg"))
            self._bg = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=lambda w, v: setattr(self._bg, 'size', v))
        root.bind(pos=lambda w, v: setattr(self._bg, 'pos', v))

        root.add_widget(self._build_header())
        root.add_widget(self._build_stats_bar())
        root.add_widget(self._build_filter_bar())
        root.add_widget(self._build_list())
        root.add_widget(self._build_input_area())

        self.add_widget(root)

    def _build_header(self):
        bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(56),
            padding=(dp(16), dp(8)), spacing=dp(8)
        )
        with bar.canvas.before:
            Color(*T("bg2"))
            bg = Rectangle(size=bar.size, pos=bar.pos)
        bar.bind(size=lambda w, v: setattr(bg, 'size', v))
        bar.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        # Back button
        back = Button(
            text="< Back",
            font_size=dp(14), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent"),
            size_hint=(None, 1), width=dp(70)
        )
        back.bind(on_press=lambda *a: self._go_back())
        bar.add_widget(back)

        bar.add_widget(Label(
            text="My Tasks",
            font_size=dp(20), bold=True,
            color=T("text"),
            size_hint_x=1
        ))

        # Clear done button
        clr = Button(
            text="Clear Done",
            font_size=dp(11),
            background_color=(0, 0, 0, 0),
            color=T("text3"),
            size_hint=(None, 1), width=dp(80)
        )
        clr.bind(on_press=self._clear_done)
        bar.add_widget(clr)

        return bar

    def _build_stats_bar(self):
        total, done, pending = get_stats()

        bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(36),
            padding=(dp(16), 0), spacing=dp(20)
        )
        with bar.canvas.before:
            Color(*T("bg3"))
            bg = Rectangle(size=bar.size, pos=bar.pos)
        bar.bind(size=lambda w, v: setattr(bg, 'size', v))
        bar.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        bar.add_widget(Label(
            text=f"Total: {total}",
            font_size=dp(12), color=T("text3")
        ))
        bar.add_widget(Label(
            text=f"Done: {done}",
            font_size=dp(12), color=(0.4, 0.85, 0.5, 1)
        ))
        bar.add_widget(Label(
            text=f"Pending: {pending}",
            font_size=dp(12), color=T("text2")
        ))

        self._stats_bar = bar
        return bar

    def _build_filter_bar(self):
        bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(40),
            padding=(dp(12), dp(4)), spacing=dp(8)
        )
        with bar.canvas.before:
            Color(*T("bg"))
            bg = Rectangle(size=bar.size, pos=bar.pos)
        bar.bind(size=lambda w, v: setattr(bg, 'size', v))
        bar.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        self._filter_btns = {}
        for f in FILTERS:
            is_active = (f == self._filter)
            btn = Button(
                text=f,
                font_size=dp(12), bold=is_active,
                background_color=(0, 0, 0, 0),
                color=T("accent") if is_active else T("text3"),
                size_hint=(None, 1), width=dp(74)
            )
            if is_active:
                with btn.canvas.before:
                    Color(*T("accent")[:3], 0.15)
                    _bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(8)])
                btn.bind(
                    size=lambda w, v, b=_bg: setattr(b, 'size', v),
                    pos=lambda w, v, b=_bg: setattr(b, 'pos', v)
                )
            btn.bind(on_press=lambda _, fv=f: self._set_filter(fv))
            self._filter_btns[f] = btn
            bar.add_widget(btn)

        bar.add_widget(Widget())  # spacer
        return bar

    def _build_list(self):
        """Scrollable list of todo items."""
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)

        self._list_layout = GridLayout(
            cols=1, spacing=dp(6),
            size_hint_y=None,
            padding=(dp(12), dp(6))
        )
        self._list_layout.bind(minimum_height=self._list_layout.setter("height"))

        self._populate_list()

        scroll.add_widget(self._list_layout)
        self._scroll = scroll
        return scroll

    def _populate_list(self):
        """Clear and repopulate the todo list based on active filter."""
        self._list_layout.clear_widgets()
        todos = load_todos()

        # Apply filter
        if self._filter == "Pending":
            todos = [t for t in todos if not t["done"]]
        elif self._filter == "Done":
            todos = [t for t in todos if t["done"]]

        if not todos:
            self._list_layout.add_widget(Label(
                text="No tasks here yet." if self._filter == "All" else f"No {self._filter.lower()} tasks.",
                font_size=dp(14), color=T("text3"),
                size_hint_y=None, height=dp(60)
            ))
            return

        for todo in todos:
            self._list_layout.add_widget(self._todo_row(todo))

    def _todo_row(self, todo):
        """Build a single todo row widget."""
        is_done = todo["done"]
        priority = todo.get("priority", "normal")
        p_color = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["normal"])
        p_label = PRIORITY_LABELS.get(priority, "o")

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(54),
            spacing=dp(6),
            padding=(dp(8), dp(6))
        )

        # Row background
        bg_alpha = 0.4 if is_done else 1.0
        with row.canvas.before:
            Color(*T("bg2")[:3], bg_alpha)
            row_bg = RoundedRectangle(size=row.size, pos=row.pos, radius=[dp(10)])
        row.bind(
            size=lambda w, v: setattr(row_bg, 'size', v),
            pos=lambda w, v: setattr(row_bg, 'pos', v)
        )

        # Priority dot
        dot = Label(
            text=p_label,
            font_size=dp(16), bold=True,
            color=(*p_color[:3], 0.5 if is_done else 1.0),
            size_hint=(None, 1), width=dp(22)
        )
        row.add_widget(dot)

        # Checkbox button
        check_text = "[x]" if is_done else "[ ]"
        check = Button(
            text=check_text,
            font_size=dp(14),
            background_color=(0, 0, 0, 0),
            color=(0.4, 0.85, 0.5, 1) if is_done else T("text3"),
            size_hint=(None, 1), width=dp(38)
        )
        check.bind(on_press=lambda _, tid=todo["id"]: self._toggle(tid))
        row.add_widget(check)

        # Task text — tap to edit
        display_text = todo["text"]
        txt_color = T("text3") if is_done else T("text")

        task_btn = Button(
            text=display_text,
            font_size=dp(14),
            background_color=(0, 0, 0, 0),
            color=txt_color,
            halign="left", valign="middle",
            text_size=(dp(210), None),
            size_hint=(1, 1),
            strikethrough=is_done
        )
        task_btn.bind(on_press=lambda _, t=todo: self._open_edit_popup(t))
        row.add_widget(task_btn)

        # Delete button
        del_btn = Button(
            text="X",
            font_size=dp(13), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("danger"),
            size_hint=(None, 1), width=dp(34)
        )
        del_btn.bind(on_press=lambda _, tid=todo["id"]: self._delete(tid))
        row.add_widget(del_btn)

        return row

    def _build_input_area(self):
        """Bottom input bar: text field + priority selector + add button."""
        area = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(110),
            padding=(dp(12), dp(8)), spacing=dp(6)
        )
        with area.canvas.before:
            Color(*T("bg2"))
            bg = Rectangle(size=area.size, pos=area.pos)
        area.bind(size=lambda w, v: setattr(bg, 'size', v))
        area.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        # ── Text input + Add button row ───────────────────────────────────
        input_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(44),
            spacing=dp(8)
        )

        self._text_input = TextInput(
            hint_text="Add a new task...",
            font_size=dp(14),
            multiline=False,
            size_hint=(1, 1),
            background_color=T("bg3"),
            foreground_color=T("text"),
            hint_text_color=T("text3"),
            cursor_color=T("accent"),
            padding=(dp(10), dp(10))
        )
        self._text_input.bind(on_text_validate=self._add_task)
        input_row.add_widget(self._text_input)

        add_btn = Button(
            text="Add",
            font_size=dp(15), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text"),
            size_hint=(None, 1), width=dp(60)
        )
        with add_btn.canvas.before:
            Color(*T("accent"))
            add_bg = RoundedRectangle(size=add_btn.size, pos=add_btn.pos, radius=[dp(10)])
        add_btn.bind(
            size=lambda w, v: setattr(add_bg, 'size', v),
            pos=lambda w, v: setattr(add_bg, 'pos', v)
        )
        add_btn.bind(on_press=self._add_task)
        input_row.add_widget(add_btn)
        area.add_widget(input_row)

        # ── Priority selector row ─────────────────────────────────────────
        pri_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(32),
            spacing=dp(8)
        )
        pri_row.add_widget(Label(
            text="Priority:",
            font_size=dp(12), color=T("text3"),
            size_hint=(None, 1), width=dp(58)
        ))

        self._pri_btns = {}
        for pri in ["high", "normal", "low"]:
            is_sel = (pri == self._selected_priority)
            p_col = PRIORITY_COLORS[pri]
            pbtn = Button(
                text=pri.capitalize(),
                font_size=dp(12), bold=is_sel,
                background_color=(0, 0, 0, 0),
                color=p_col if is_sel else T("text3"),
                size_hint=(None, 1), width=dp(68)
            )
            if is_sel:
                with pbtn.canvas.before:
                    Color(*p_col[:3], 0.2)
                    pbg = RoundedRectangle(size=pbtn.size, pos=pbtn.pos, radius=[dp(6)])
                pbtn.bind(
                    size=lambda w, v, b=pbg: setattr(b, 'size', v),
                    pos=lambda w, v, b=pbg: setattr(b, 'pos', v)
                )
            pbtn.bind(on_press=lambda _, p=pri: self._set_priority(p))
            self._pri_btns[pri] = pbtn
            pri_row.add_widget(pbtn)

        pri_row.add_widget(Widget())
        area.add_widget(pri_row)

        return area

    # ─────────────────────────────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────────────────────────────

    def _add_task(self, *args):
        text = self._text_input.text.strip()
        if not text:
            return
        add_todo(text, priority=self._selected_priority)
        self._text_input.text = ""
        self._refresh()

    def _toggle(self, todo_id):
        toggle_todo(todo_id)
        self._refresh()

    def _delete(self, todo_id):
        delete_todo(todo_id)
        self._refresh()

    def _clear_done(self, *args):
        clear_done()
        self._refresh()

    def _set_filter(self, f):
        self._filter = f
        self._refresh()

    def _set_priority(self, priority):
        self._selected_priority = priority
        # Rebuild input area by refreshing full UI
        self._refresh()

    def _open_edit_popup(self, todo):
        """Show a popup to edit the task text and priority."""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        with content.canvas.before:
            Color(*T("bg2"))
            bg = Rectangle(size=content.size, pos=content.pos)
        content.bind(size=lambda w, v: setattr(bg, 'size', v))
        content.bind(pos=lambda w, v: setattr(bg, 'pos', v))

        content.add_widget(Label(
            text="Edit Task",
            font_size=dp(16), bold=True,
            color=T("text"),
            size_hint_y=None, height=dp(32)
        ))

        txt = TextInput(
            text=todo["text"],
            font_size=dp(14),
            multiline=False,
            size_hint_y=None, height=dp(44),
            background_color=T("bg3"),
            foreground_color=T("text"),
            cursor_color=T("accent"),
            padding=(dp(10), dp(10))
        )
        content.add_widget(txt)

        # Priority row in popup
        pri_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        pri_row.add_widget(Label(
            text="Priority:", font_size=dp(12), color=T("text3"),
            size_hint=(None, 1), width=dp(58)
        ))
        current_pri = [todo.get("priority", "normal")]
        pri_btns_popup = {}

        def _refresh_popup_pri():
            for p, b in pri_btns_popup.items():
                b.color = PRIORITY_COLORS[p] if p == current_pri[0] else T("text3")
                b.bold = (p == current_pri[0])

        for pri in ["high", "normal", "low"]:
            pb = Button(
                text=pri.capitalize(),
                font_size=dp(12),
                background_color=(0, 0, 0, 0),
                color=PRIORITY_COLORS[pri] if pri == current_pri[0] else T("text3"),
                bold=(pri == current_pri[0]),
                size_hint=(None, 1), width=dp(68)
            )
            def _set(_, p=pri):
                current_pri[0] = p
                _refresh_popup_pri()
            pb.bind(on_press=_set)
            pri_btns_popup[pri] = pb
            pri_row.add_widget(pb)
        pri_row.add_widget(Widget())
        content.add_widget(pri_row)

        # Save / Cancel
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))

        popup = Popup(
            title="",
            title_size=0,
            content=content,
            size_hint=(0.88, None),
            height=dp(240),
            background_color=T("bg2"),
            separator_height=0
        )

        cancel_btn = Button(
            text="Cancel", font_size=dp(14),
            background_color=(0, 0, 0, 0),
            color=T("text3")
        )
        cancel_btn.bind(on_press=popup.dismiss)

        save_btn = Button(
            text="Save", font_size=dp(14), bold=True,
            background_color=(0, 0, 0, 0),
            color=T("accent_text")
        )
        with save_btn.canvas.before:
            Color(*T("accent"))
            sbg = RoundedRectangle(size=save_btn.size, pos=save_btn.pos, radius=[dp(8)])
        save_btn.bind(
            size=lambda w, v: setattr(sbg, 'size', v),
            pos=lambda w, v: setattr(sbg, 'pos', v)
        )

        def _save(*a):
            new_text = txt.text.strip()
            if new_text:
                edit_todo(todo["id"], new_text=new_text, new_priority=current_pri[0])
                popup.dismiss()
                self._refresh()

        save_btn.bind(on_press=_save)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        content.add_widget(btn_row)

        popup.open()

    def _refresh(self):
        """Rebuild the full screen to reflect latest data."""
        self.clear_widgets()
        self._build_ui()

    def _go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
