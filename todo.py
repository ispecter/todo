#!/usr/bin/env python3
"""A simple CLI to-do list with due dates, categories, and JSON persistence."""

# ── Section 1: Imports & Constants ───────────────────────────────────────────

import argparse
import json
import os
import sys
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional

DEFAULT_PATH = os.path.expanduser("~/.todo.json")
DATA_FILE = os.environ.get("TODO_FILE", DEFAULT_PATH)
VERSION = 1

# ── Section 2: Data Layer ─────────────────────────────────────────────────────

def _load_raw() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"version": VERSION, "tasks": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def _save_raw(data: dict) -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)

def load_tasks() -> List["Task"]:
    return [Task.from_dict(t) for t in _load_raw()["tasks"]]

def save_tasks(tasks: List["Task"]) -> None:
    data = _load_raw()
    data["tasks"] = [t.to_dict() for t in tasks]
    _save_raw(data)

# ── Section 3: Task Dataclass ─────────────────────────────────────────────────

@dataclass
class Task:
    id: str
    text: str
    done: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    due_date: Optional[str] = None
    category: Optional[str] = None

    @classmethod
    def new(
        cls,
        text: str,
        due_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> "Task":
        return cls(id=str(uuid.uuid4()), text=text, due_date=due_date, category=category)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        valid = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_overdue(self) -> bool:
        if self.done or not self.due_date:
            return False
        return date.fromisoformat(self.due_date) < date.today()

    def due_label(self) -> str:
        if not self.due_date:
            return ""
        d = date.fromisoformat(self.due_date)
        today = date.today()
        delta = (d - today).days
        if delta < 0:
            return f"overdue {abs(delta)}d"
        elif delta == 0:
            return "due today"
        elif delta == 1:
            return "due tomorrow"
        elif delta <= 6:
            return f"due {d.strftime('%A')}"
        else:
            return f"due {d.strftime('%b %-d')}"

# ── Section 4: Date Parsing & ID Resolution ───────────────────────────────────

def parse_date(value: str) -> Optional[str]:
    """Parse flexible date strings into YYYY-MM-DD, or None for 'none'/'clear'."""
    v = value.lower().strip()
    today = date.today()
    if v in ("none", "clear", ""):
        return None
    if v == "today":
        return today.isoformat()
    if v == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    short = v[:3]
    if short in weekdays:
        target_dow = weekdays.index(short)
        days_ahead = (target_dow - today.weekday()) % 7 or 7
        return (today + timedelta(days=days_ahead)).isoformat()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD, today, tomorrow, or a weekday name."
        )

def resolve_id(tasks: List[Task], prefix: str) -> Task:
    matches = [t for t in tasks if t.id.startswith(prefix)]
    if not matches:
        sys.exit(f"Error: No task found matching ID prefix '{prefix}'")
    if len(matches) > 1:
        ids = ", ".join(t.id[:8] for t in matches)
        sys.exit(f"Error: Ambiguous ID prefix '{prefix}' matches: {ids}")
    return matches[0]

# ── Section 5: Filtering ──────────────────────────────────────────────────────

def filter_tasks(tasks: List[Task], args: argparse.Namespace) -> List[Task]:
    result = tasks

    done_only = getattr(args, "done_only", False)
    show_all = getattr(args, "all", False)

    if done_only:
        result = [t for t in result if t.done]
    elif not show_all:
        result = [t for t in result if not t.done]

    cat = getattr(args, "category", None)
    if cat:
        result = [t for t in result if t.category == cat.lower()]

    if getattr(args, "overdue", False):
        result = [t for t in result if t.is_overdue()]

    due_before = getattr(args, "due_before", None)
    if due_before:
        cutoff = date.fromisoformat(due_before)
        result = [
            t for t in result
            if t.due_date and date.fromisoformat(t.due_date) <= cutoff
        ]

    sort_by = getattr(args, "sort_by", "created")
    if sort_by == "due":
        result.sort(key=lambda t: t.due_date or "9999-99-99")
    elif sort_by == "category":
        result.sort(key=lambda t: (t.category or "", t.created_at))
    else:
        result.sort(key=lambda t: t.created_at)

    return result

# ── Section 6: Output Formatting ──────────────────────────────────────────────

def _format_line(task: Task, text_width: int) -> str:
    status = "x" if task.done else " "
    short_id = task.id[:8]
    text = task.text[:text_width].ljust(text_width)
    category = (task.category or "")[:14].ljust(14)
    due = task.due_label()
    overdue_flag = " !" if task.is_overdue() else ""
    return f"  [{short_id}] [{status}]  {text}  {category}  {due}{overdue_flag}"

def cmd_list(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    filtered = filter_tasks(tasks, args)

    if not filtered:
        print("No tasks found.")
        return

    text_width = min(50, max(20, max(len(t.text) for t in filtered)))

    header_text = "Task".ljust(text_width)
    print(f"\n  {'ID':8}  {'St':3}  {header_text}  {'Category':14}  Due")
    print(f"  {'─'*8}  ───  {'─'*text_width}  {'─'*14}  {'─'*16}")

    for t in filtered:
        print(_format_line(t, text_width))

    done_count = sum(1 for t in filtered if t.done)
    pending_count = len(filtered) - done_count
    print(f"\n  {len(filtered)} task(s)", end="")
    if not getattr(args, "all", False) and not getattr(args, "done_only", False):
        total = len(load_tasks())
        hidden = total - len(filtered)
        if hidden > 0:
            print(f"  ({hidden} completed hidden, use --all to show)", end="")
    print()

# ── Section 7: Commands ───────────────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    due = parse_date(args.due) if args.due else None
    cat = args.category.lower() if args.category else None
    task = Task.new(text=args.text, due_date=due, category=cat)
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added: [{task.id[:8]}] {task.text}")

def cmd_done(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    changed = False
    for prefix in args.ids:
        task = resolve_id(tasks, prefix)
        if task.done:
            print(f"Already done: [{task.id[:8]}] {task.text}")
        else:
            task.done = True
            changed = True
            print(f"Done: [{task.id[:8]}] {task.text}")
    if changed:
        save_tasks(tasks)

def cmd_edit(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    task = resolve_id(tasks, args.id)
    if args.text is not None:
        task.text = args.text
    if args.due is not None:
        task.due_date = parse_date(args.due)
    if args.category is not None:
        if args.category.lower() in ("none", "clear"):
            task.category = None
        else:
            task.category = args.category.lower()
    save_tasks(tasks)
    print(f"Updated: [{task.id[:8]}] {task.text}")

def cmd_delete(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    to_delete = [resolve_id(tasks, p) for p in args.ids]
    if not args.yes:
        for t in to_delete:
            print(f"  [{t.id[:8]}] {t.text}")
        confirm = input(f"Delete {len(to_delete)} task(s)? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            return
    ids_to_remove = {t.id for t in to_delete}
    tasks = [t for t in tasks if t.id not in ids_to_remove]
    save_tasks(tasks)
    print(f"Deleted {len(ids_to_remove)} task(s).")

def cmd_categories(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    counts = Counter(t.category for t in tasks if t.category and not t.done)
    if not counts:
        print("No categories found.")
        return
    print()
    for cat, count in sorted(counts.items()):
        print(f"  {cat:<20}  {count} task(s)")
    print()

# ── Section 8: Argument Parser ────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple CLI to-do list.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  todo add \"Write report\" --due tomorrow --category work\n"
            "  todo list --category work\n"
            "  todo done abc123\n"
            "  todo edit abc123 --due none --category personal\n"
            "  todo delete abc123 --yes\n"
            "  todo categories\n"
            "\n"
            f"Data file: {DATA_FILE}\n"
            "Override with: TODO_FILE=/path/to/file.json todo ..."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # add
    p = sub.add_parser("add", help="Add a new task")
    p.add_argument("text", help="Task description")
    p.add_argument("--due", metavar="DATE", help="Due date (YYYY-MM-DD, today, tomorrow, weekday)")
    p.add_argument("--category", "-c", metavar="CAT", help="Category/tag")
    p.set_defaults(func=cmd_add)

    # list / ls
    p = sub.add_parser("list", aliases=["ls"], help="List tasks")
    p.add_argument("--all", "-a", action="store_true", help="Show all tasks including completed")
    p.add_argument("--done", dest="done_only", action="store_true", help="Show only completed tasks")
    p.add_argument("--category", "-c", metavar="CAT", help="Filter by category")
    p.add_argument("--due-before", metavar="DATE", dest="due_before", type=parse_date, help="Show tasks due on or before DATE")
    p.add_argument("--overdue", action="store_true", help="Show only overdue tasks")
    p.add_argument("--sort-by", dest="sort_by", choices=["due", "created", "category"], default="created", metavar="FIELD", help="Sort by: due, created, category (default: created)")
    p.set_defaults(func=cmd_list)

    # done
    p = sub.add_parser("done", help="Mark task(s) as complete")
    p.add_argument("ids", nargs="+", metavar="ID", help="Task ID prefix(es)")
    p.set_defaults(func=cmd_done)

    # edit
    p = sub.add_parser("edit", help="Edit a task")
    p.add_argument("id", metavar="ID", help="Task ID prefix")
    p.add_argument("--text", help="New task description")
    p.add_argument("--due", metavar="DATE", help="New due date, or 'none' to clear")
    p.add_argument("--category", "-c", metavar="CAT", help="New category, or 'none' to clear")
    p.set_defaults(func=cmd_edit)

    # delete / rm
    p = sub.add_parser("delete", aliases=["rm"], help="Delete task(s)")
    p.add_argument("ids", nargs="+", metavar="ID", help="Task ID prefix(es)")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p.set_defaults(func=cmd_delete)

    # categories / cats
    p = sub.add_parser("categories", aliases=["cats"], help="List all categories")
    p.set_defaults(func=cmd_categories)

    # shell
    p = sub.add_parser("shell", help="Start an interactive shell")
    p.set_defaults(func=cmd_shell)

    return parser

# ── Section 9: Interactive Shell ──────────────────────────────────────────────

def cmd_shell(args: argparse.Namespace) -> None:
    import shlex
    parser = build_parser()
    parser.prog = ""  # cleaner usage lines in shell mode
    print("todo shell  (type 'quit' or Ctrl-D to exit, 'help' for commands)")
    while True:
        try:
            line = input("todo> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            break
        try:
            tokens = shlex.split(line)
        except ValueError as e:
            print(f"Error: {e}")
            continue
        try:
            cmd_args = parser.parse_args(tokens)
            cmd_args.func(cmd_args)
        except SystemExit:
            pass  # argparse errors and resolve_id failures print their message then raise SystemExit

# ── Section 10: Entry Point ───────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
