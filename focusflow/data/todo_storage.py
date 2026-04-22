"""
data/todo_storage.py
--------------------
Full todo list persistence.

Each todo item:
{
    "id":        str  (unique id),
    "text":      str,
    "done":      bool,
    "priority":  "high" | "normal" | "low",
    "created_at": ISO timestamp,
    "done_at":    ISO timestamp or None
}
"""

import json
import os
import uuid
from datetime import datetime

TODO_FILE = os.path.join(os.path.dirname(__file__), "todos.json")


def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)


def add_todo(text, priority="normal"):
    """Add a new todo. Returns the new item."""
    todos = load_todos()
    item = {
        "id":         str(uuid.uuid4())[:8],
        "text":       text.strip(),
        "done":       False,
        "priority":   priority,
        "created_at": datetime.now().isoformat(),
        "done_at":    None,
    }
    todos.append(item)
    _save(todos)
    return item


def toggle_todo(todo_id):
    """Toggle done/undone. Returns updated item or None."""
    todos = load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = not t["done"]
            t["done_at"] = datetime.now().isoformat() if t["done"] else None
            _save(todos)
            return t
    return None


def delete_todo(todo_id):
    """Delete a todo by id."""
    todos = load_todos()
    todos = [t for t in todos if t["id"] != todo_id]
    _save(todos)


def edit_todo(todo_id, new_text=None, new_priority=None):
    """Edit text and/or priority of a todo."""
    todos = load_todos()
    for t in todos:
        if t["id"] == todo_id:
            if new_text is not None:
                t["text"] = new_text.strip()
            if new_priority is not None:
                t["priority"] = new_priority
            _save(todos)
            return t
    return None


def clear_done():
    """Remove all completed todos."""
    todos = [t for t in load_todos() if not t["done"]]
    _save(todos)
    return todos


def reorder_todos(ordered_ids):
    """Reorder todos to match the given list of ids."""
    todos = load_todos()
    id_map = {t["id"]: t for t in todos}
    reordered = [id_map[i] for i in ordered_ids if i in id_map]
    # Append any that weren't in ordered_ids (safety)
    seen = set(ordered_ids)
    for t in todos:
        if t["id"] not in seen:
            reordered.append(t)
    _save(reordered)
    return reordered


def get_stats():
    """Return (total, done, pending) counts."""
    todos = load_todos()
    done = sum(1 for t in todos if t["done"])
    return len(todos), done, len(todos) - done
