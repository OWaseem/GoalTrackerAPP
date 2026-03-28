import subprocess
import shutil
import sys
from pathlib import Path

MAIN_PY = Path(__file__).parent / "main.py"


def send_notification(title: str, message: str, sound: bool = True):
    if shutil.which("terminal-notifier"):
        cmd = [
            "terminal-notifier",
            "-title",   title,
            "-message", message,
            "-execute", f"{sys.executable} {MAIN_PY}",
        ]
        if sound:
            cmd += ["-sound", "default"]
        subprocess.run(cmd, check=True)
    else:
        # Fallback to osascript if terminal-notifier is not installed
        sound_part = ' sound name "Default"' if sound else ""
        script = f'display notification "{message}" with title "{title}"{sound_part}'
        subprocess.run(["osascript", "-e", script], check=True)
