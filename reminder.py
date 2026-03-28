"""
Run by launchd on a schedule to check for due/overdue goals and send notifications.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, get_due_today, get_overdue
from notifier import send_notification


def run():
    init_db()

    overdue = get_overdue()
    for goal in overdue:
        send_notification(
            "Overdue Goal",
            f'"{goal.title}" was due on {goal.due_date} and is still pending.',
        )

    due_today = get_due_today()
    for goal in due_today:
        send_notification(
            "Goal Due Today",
            f'"{goal.title}" is due today!',
        )

    if not overdue and not due_today:
        print("No goals due today or overdue.")


if __name__ == "__main__":
    run()
