# Goal Tracker

A personal goal tracking app for macOS with a GUI built in tkinter and native desktop notifications. Track your goals, set due dates, organise by category, and get reminded every morning automatically.

---

## Requirements

- Python 3.11+
- [Homebrew](https://brew.sh)
- `terminal-notifier` (for clickable notifications)

### Install dependencies

```bash
pip3 install typer rich
brew install terminal-notifier
```

---

## Setup

### 1. Add the shell alias

Add this to your `~/.zshrc`:

```zsh
alias goals="python3 /Users/omarwaseem/projects/python_projects/GoalTrackerAPP/main.py"
```

Then reload your shell:

```bash
source ~/.zshrc
```

### 2. Register the daily reminder (run once)

```bash
cp com.trackgoals.reminder.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.trackgoals.reminder.plist
```

This registers a background job that fires every morning at **9am** automatically — no terminal needs to be open.

---

## Launching the App

```bash
goals
```

---

## Using the App

### Adding a Goal

Click **+ Add Goal** in the top-right corner. A dialog will appear with the following fields:

| Field | Required | Notes |
|---|---|---|
| Title | Yes | Keep it action-oriented, e.g. "Finish project report" |
| Description | No | Optional extra detail |
| Category | No | Defaults to `general`. Use consistent labels like `work`, `fitness`, `learning`, `personal` |
| Due Date | No | Format: `MM-DD-YYYY`. Required for notifications to fire. Defaults to today. |

Press **Enter** or click **Add Goal** to save.

---

### Reading the Table

Goals are sorted by due date (soonest first). Goals with no due date appear at the bottom. Row colour tells you the urgency at a glance:

| Colour | Meaning |
|---|---|
| White | Upcoming — no urgency |
| Yellow | Due today |
| Red | Overdue and still pending |
| Green | Completed |

The counter in the bottom-right always shows your current `X pending · Y done` totals.

---

### Actions

- **Mark Done** — select a row, click **Mark Done**. The row turns green.
- **Edit** — select a row, click **Edit**. A pre-filled dialog opens where you can update the title, description, category, or due date.
- **Delete** — select a row, click **Delete**. A confirmation popup will appear before anything is removed.

You must select a row before any of these buttons will do anything.

---

### Filtering

Use the two dropdowns at the top of the table to narrow your view:

- **Status** — `All`, `pending`, or `done`
- **Category** — auto-populated from your existing goals

Filters can be combined. For example: `pending` + `fitness` shows only incomplete fitness goals.

---

## Notifications

Every morning at **9am**, macOS will automatically check your goals and fire a native desktop notification for:

- Any goal **due today**
- Any goal that is **overdue and still pending**

Clicking a notification **opens the app immediately**.

### Manually trigger a reminder check

```bash
python3 /Users/omarwaseem/projects/python_projects/GoalTrackerAPP/reminder.py
```

### Test that notifications appear on screen

```bash
python3 /Users/omarwaseem/projects/python_projects/GoalTrackerAPP/test_notification.py
```

This fires a one-time test notification immediately — no goals required. Use it to confirm notifications are working without waiting for 9am.

### Check notification logs

These are only useful if your 9am reminders stop working. Since `reminder.py` runs silently in the background via launchd, you can't see its output in a terminal — it gets written to these files instead.

```bash
cat /tmp/trackgoals.log   # standard output
cat /tmp/trackgoals.err   # errors
```

---

## Project Structure

```
GoalTrackerAPP/
├── main.py                        # GUI (tkinter) — entry point
├── db.py                          # All SQLite queries
├── models.py                      # Goal dataclass
├── notifier.py                    # macOS notifications via terminal-notifier
├── reminder.py                    # Checks DB for due/overdue goals → sends notifications
├── test_notification.py           # Fires a one-time test notification
├── goals.db                       # SQLite database (auto-created on first launch)
└── com.trackgoals.reminder.plist  # launchd config for daily 9am reminders
```

---

## Optimal Workflow

1. **Sunday planning** — open the app with `goals`, add everything you want to accomplish that week with due dates and categories.
2. **Morning check-in** — the 9am notification surfaces anything urgent. Click it to open the app directly.
3. **Keep categories consistent** — pick 3–5 and stick to them (`work`, `fitness`, `learning`, `personal`) so filtering stays meaningful.
4. **Always set due dates** — goals without a due date are never included in notifications. If something matters, give it a date.
5. **Never delete completed goals** — mark them done instead. Use the `done` filter periodically to review what you've accomplished.
