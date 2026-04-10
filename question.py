#!/usr/bin/env python3
"""
claude-notify question — Notification hook for AskUserQuestion.

When Claude asks the user a question, this hook sends a macOS notification
to alert the user. The question is displayed normally in the terminal —
this hook does NOT intercept or block it.

Clicking the notification focuses the correct terminal pane so the user
can answer the question there.
"""
import json
import os
import shutil
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))
FOCUSERS_DIR = os.path.join(PLUGIN_ROOT, "focusers")


def find_alerter():
    """Find alerter binary."""
    path = shutil.which("alerter")
    if path:
        return path
    for p in ("/opt/homebrew/bin/alerter", "/usr/local/bin/alerter"):
        if os.path.isfile(p):
            return p
    return None


def find_notifier():
    """Find terminal-notifier binary."""
    path = shutil.which("terminal-notifier")
    if path:
        return path
    for p in ("/opt/homebrew/bin/terminal-notifier", "/usr/local/bin/terminal-notifier"):
        if os.path.isfile(p):
            return p
    return None


def get_tty():
    """Get the TTY by walking up the process tree until we find one."""
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,tty="],
            capture_output=True, text=True, timeout=2,
        )
        pids = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                try:
                    pids[int(parts[0])] = (int(parts[1]), parts[2])
                except ValueError:
                    pass
        current = os.getpid()
        for _ in range(30):
            info = pids.get(current)
            if info is None:
                break
            ppid, tty = info
            if tty and tty not in ("??", "-"):
                return tty if tty.startswith("/dev/") else f"/dev/{tty}"
            current = ppid
    except Exception:
        pass
    return None


def detect_terminal(pid=None):
    """Detect terminal type by walking the process tree."""
    if pid is None:
        pid = os.getppid()
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,comm="],
            capture_output=True, text=True, timeout=3,
        )
        tree = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 3:
                try:
                    tree[int(parts[0])] = (int(parts[1]), parts[2])
                except ValueError:
                    pass
    except Exception:
        return "unknown"

    current = pid
    for _ in range(30):
        info = tree.get(current)
        if info is None:
            break
        ppid, comm = info
        name = os.path.basename(comm).lower()
        if "cmux" in name:
            return "cmux"
        if name.startswith("tmux"):
            return "tmux"
        if name in ("iterm2", "iterm", "itermserver-main"):
            return "iterm2"
        if name in ("terminal", "terminal.app"):
            return "terminal_app"
        current = ppid

    return "unknown"


def focus_terminal(terminal, tty, pid):
    """Focus the correct terminal pane/tab by running the focuser script."""
    focus_script = os.path.join(FOCUSERS_DIR, f"{terminal}.sh")
    if not os.path.isfile(focus_script) or not tty:
        return
    subprocess.Popen(
        ["bash", focus_script, tty, str(pid or "")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def send_notification(message, terminal, tty, pid):
    """Send a notification and focus the terminal."""

    alerter = find_alerter()
    notifier = find_notifier()

    if alerter:
        subprocess.Popen(
            [
                alerter,
                "--title", "Claude Code — 提问",
                "--message", message,
                "--sound", "Glass",
                "--timeout", "10",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    elif notifier:
        subprocess.Popen(
            [notifier, "-title", "Claude Code — 提问", "-message", message, "-sound", "Glass"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    else:
        subprocess.Popen(
            [
                "osascript", "-e",
                f'display notification "{message}" '
                'with title "Claude Code — 提问" sound name "Glass"',
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    focus_terminal(terminal, tty, pid)


def main():
    try:
        stdin_data = sys.stdin.read()
        data = json.loads(stdin_data) if stdin_data.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return

    tty = get_tty()
    pid = os.getppid()
    terminal = detect_terminal(pid)

    send_notification("Claude 有问题想问你", terminal, tty, pid)


if __name__ == "__main__":
    main()
