# todo — Help

A command-line to-do list. Tasks are saved to `~/.todo.json` between sessions.

## Installation

The `todo` command is installed and available system-wide via a symlink at `~/.local/bin/todo`. Run it from any directory:

```
todo <command> [options]
```

To reinstall or move the script, recreate the symlink:

```bash
ln -sf /Users/harborcapital/claude-projects/todo/todo.py ~/.local/bin/todo
```

## Usage

```
todo <command> [options]
```

---

## Commands

### add
Add a new task.

```
todo add "Task description" [--due DATE] [--category CAT]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--due DATE` | | Due date (see Date Formats below) |
| `--category CAT` | `-c` | Category or tag label |

Examples:
```
todo add "Write report"
todo add "Submit invoice" --due tomorrow
todo add "Fix login bug" --due 2026-03-01 --category work
```

---

### list
List tasks. By default shows only incomplete tasks.

```
todo list [options]
todo ls  [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--all` | `-a` | Show all tasks, including completed |
| `--done` | | Show only completed tasks |
| `--category CAT` | `-c` | Filter by category |
| `--overdue` | | Show only overdue tasks |
| `--due-before DATE` | | Show tasks due on or before DATE |
| `--sort-by FIELD` | | Sort by `due`, `created`, or `category` (default: `created`) |

Examples:
```
todo list
todo list --all
todo list --category work
todo list --overdue
todo list --due-before friday --sort-by due
todo list --done
```

Overdue tasks are flagged with ` !` at the end of the line.

---

### done
Mark one or more tasks as complete.

```
todo done ID [ID ...]
```

Examples:
```
todo done 36c83c9e
todo done 36c83c9e 4bdebcb8
```

---

### edit
Edit a task's text, due date, or category. Only the fields you specify are changed.

```
todo edit ID [--text TEXT] [--due DATE] [--category CAT]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--text TEXT` | | Replace the task description |
| `--due DATE` | | Set a new due date; use `none` to remove it |
| `--category CAT` | `-c` | Set a new category; use `none` to remove it |

Examples:
```
todo edit 36c83c9e --text "Updated description"
todo edit 36c83c9e --due 2026-03-15
todo edit 36c83c9e --due none --category personal
```

---

### delete
Delete one or more tasks. Prompts for confirmation unless `--yes` is passed.

```
todo delete ID [ID ...]  [--yes]
todo rm      ID [ID ...]  [--yes]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--yes` | `-y` | Skip the confirmation prompt |

Examples:
```
todo delete 36c83c9e
todo delete 36c83c9e 4bdebcb8 --yes
```

---

### categories
List all categories that have at least one incomplete task, with task counts.

```
todo categories
todo cats
```

---

## Task IDs

Every task is assigned a unique ID (UUID). You only need to type enough characters to uniquely identify a task — usually 4–8 characters works fine.

```
todo done 36c8        # matches task starting with "36c8"
todo done 36c83c9e    # full 8-char short ID also works
```

If the prefix is ambiguous (matches more than one task), an error is shown listing the matches.

---

## Date Formats

Accepted wherever a date is expected (`--due`, `--due-before`):

| Input | Meaning |
|-------|---------|
| `YYYY-MM-DD` | Exact date, e.g. `2026-03-15` |
| `today` | Today's date |
| `tomorrow` | Tomorrow's date |
| `mon`, `monday` | Next Monday |
| `tue`, `wednesday`, `fri`, etc. | Next occurrence of that weekday |
| `none` or `clear` | Remove the date (edit command only) |

---

## Data File

Tasks are stored in `~/.todo.json`. To use a different file, set the `TODO_FILE` environment variable:

```
TODO_FILE=~/work/tasks.json todo list
```

You can make this permanent with a shell alias:
```bash
alias todo='TODO_FILE=~/work/tasks.json python3 ~/todo.py'
```
