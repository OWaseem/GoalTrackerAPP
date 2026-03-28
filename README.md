# Goal Tracker

A personal goal tracking app with two interfaces:

- **Desktop (macOS)** — tkinter GUI with native notifications via launchd
- **Web PWA** — Flask backend + mobile-first UI, installable on iPhone via Safari

Both interfaces share the same SQLite database (`goals.db`) when run locally.

---

## Desktop App (macOS)

### Requirements

- Python 3.11+
- [Homebrew](https://brew.sh)
- `terminal-notifier` (for clickable notifications)

```bash
pip3 install typer rich
brew install terminal-notifier
```

### Setup

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

### Launch

```bash
goals
```

---

## Web App / iPhone PWA

### Requirements

```bash
pip3 install flask gunicorn pywebpush apscheduler
```

### Run locally

```bash
python3 -m flask --app app run --debug
```

Open **http://127.0.0.1:5000** in Chrome.

> **Note:** macOS AirPlay Receiver occupies port 5000 by default. Disable it at
> System Settings → General → AirDrop & Handoff → AirPlay Receiver → Off

### Deploy to Render

**1. Generate VAPID keys (once)**

```bash
python3 generate_vapid_keys.py
```

Save the output — you'll need it in the next step.

**2. Push to GitHub**

```bash
git add .
git commit -m "Add web PWA"
git push
```

**3. Create a Render web service**

- Go to [render.com](https://render.com) → New → Web Service → connect your GitHub repo
- Render will auto-detect `render.yaml` (persistent disk + Python runtime)
- In the Render dashboard → **Environment**, add two variables:
  - `VAPID_PUBLIC_KEY` — from step 1
  - `VAPID_PRIVATE_KEY` — from step 1

**4. Add to iPhone Home Screen**

- Open your Render URL in **Safari on iPhone**
- Tap Share → **Add to Home Screen**
- Open from the Home Screen (required for push notifications)
- Accept the notification permission prompt

### iPhone push notifications

Every day at **9am UTC**, the server checks your goals and sends a push notification for:

- Any goal **due today**
- Any goal that is **overdue and still pending**

> Push notifications on iOS require iOS 16.4+, Safari, and the app added to your Home Screen.

### Test notifications manually

With the local server running and VAPID keys set, open a Python shell:

```python
from app import check_and_notify
check_and_notify()
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
├── app.py                         # Web server (Flask REST API + PWA)
├── db.py                          # All SQLite queries (shared by both)
├── models.py                      # Goal dataclass
├── notifier.py                    # macOS notifications (desktop only)
├── reminder.py                    # Daily check → macOS notifications
├── generate_vapid_keys.py         # One-time VAPID key generator
├── goals.db                       # SQLite database (shared locally)
├── requirements.txt               # Python dependencies (web app)
├── render.yaml                    # Render deployment config
├── runtime.txt                    # Python version for Render
├── com.trackgoals.reminder.plist  # launchd config for 9am macOS reminders
└── static/
    ├── index.html                 # PWA shell
    ├── style.css                  # Dark theme styles
    ├── app.js                     # Frontend logic
    ├── manifest.json              # PWA manifest
    └── sw.js                      # Service worker (caching + push)
```

---

## Optimal Workflow

1. **Sunday planning** — add everything you want to accomplish that week with due dates and categories.
2. **Morning check-in** — the 9am notification surfaces anything urgent.
3. **Keep categories consistent** — pick 3–5 and stick to them (`work`, `fitness`, `learning`, `personal`).
4. **Always set due dates** — goals without a due date are never included in notifications.
5. **Never delete completed goals** — mark them done instead and review periodically with the `done` filter.
