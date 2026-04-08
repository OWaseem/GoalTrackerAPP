# Goal Tracker

A personal goal tracking desktop app for macOS — card-based UI built with tkinter and SQLite.

---

## Requirements

- Python 3.11+
- [Homebrew](https://brew.sh)
- `terminal-notifier` (for clickable notifications)

```bash
pip3 install typer rich
brew install terminal-notifier
```

---

## Setup

**1. Add the shell alias**

Add to `~/.zshrc`:

```zsh
alias goals="python3 /Users/omarwaseem/projects/python_projects/GoalTrackerAPP/main.py"
```

```bash
source ~/.zshrc
```

**2. Register the daily reminder (run once)**

```bash
cp com.trackgoals.reminder.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.trackgoals.reminder.plist
```

Fires every morning at **9am** automatically — no terminal needs to be open.

---

## Launch

```bash
goals
```

Or directly:

```bash
python main.py
```

---

## Using the App

### Adding a Goal

Click **+ Add Goal**. Fields:

| Field | Required | Notes |
|---|---|---|
| Title | Yes | Keep it action-oriented |
| Description | No | Optional detail |
| Category | No | Defaults to `general` |
| Due Date | No | Required for notifications to fire |

### Goal colours

| Colour | Meaning |
|---|---|
| White | Upcoming |
| Yellow | Due today |
| Red | Overdue and still pending |
| Green | Completed |

### Actions

Each card has inline buttons:

- **Done / Pending** — toggle goal status
- **Edit** — update any field
- **Remove** — delete with confirmation

### Filtering

Use the two dropdowns to filter by **Status** and **Category**. Filters can be combined.

---

## Project Structure

```
GoalTrackerAPP/
├── main.py                        # Desktop GUI (tkinter)
├── db.py                          # SQLite queries
├── models.py                      # Goal dataclass
├── notifier.py                    # macOS notifications
├── reminder.py                    # Daily check → macOS notifications
├── goals.db                       # SQLite database
└── com.trackgoals.reminder.plist  # launchd config for 9am reminders
```

---

## Optimal Workflow

1. **Sunday planning** — add everything you want to accomplish that week with due dates and categories.
2. **Morning check-in** — the 9am notification surfaces anything urgent.
3. **Keep categories consistent** — pick 3–5 and stick to them (`work`, `fitness`, `learning`, `personal`).
4. **Always set due dates** — goals without a due date are never included in notifications.
5. **Never delete completed goals** — mark them done instead and review periodically with the `done` filter.
