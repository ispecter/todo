# todo

A simple command-line to-do list. Tasks persist to `~/.todo.json` between sessions.

## Features

- Add tasks with due dates and categories
- List with filters: overdue, by category, by date, done/pending
- Edit or delete tasks by ID
- Partial ID matching — type just enough to be unique
- No dependencies — standard library only

## Installation

```bash
# Make executable and symlink to somewhere on your PATH
chmod +x todo.py
ln -sf "$(pwd)/todo.py" ~/.local/bin/todo
```

## Usage

```
todo <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `todo add "text" [--due DATE] [-c CAT]` | Add a task |
| `todo list [filters]` | List tasks |
| `todo done ID [ID ...]` | Mark task(s) complete |
| `todo edit ID [--text] [--due] [-c]` | Edit a task |
| `todo delete ID [ID ...] [-y]` | Delete task(s) |
| `todo categories` | Show categories with counts |

### Examples

```bash
todo add "Write report" --due tomorrow --category work
todo add "Buy groceries" --due friday

todo list
todo list --category work
todo list --overdue
todo list --due-before friday --sort-by due
todo list --all

todo done 36c8
todo edit 36c8 --due 2026-03-01 --category personal
todo delete 36c8 --yes
```

### Date formats

`YYYY-MM-DD` · `today` · `tomorrow` · `mon`, `tuesday`, `fri`, … · `none` (to clear)

### List filters

| Flag | Description |
|------|-------------|
| `--all` / `-a` | Show completed and pending |
| `--done` | Show only completed |
| `--category CAT` / `-c` | Filter by category |
| `--overdue` | Show only overdue tasks |
| `--due-before DATE` | Tasks due on or before DATE |
| `--sort-by FIELD` | Sort by `due`, `created`, or `category` |

## Data file

Tasks are stored in `~/.todo.json`. Override with the `TODO_FILE` environment variable:

```bash
TODO_FILE=~/work/tasks.json todo list
```
