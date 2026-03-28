import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notifier import send_notification

send_notification("Test", "Notifications are working!")
