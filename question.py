#!/usr/bin/env python3
"""
claude-notify question — Notification hook for AskUserQuestion.

When Claude asks the user a question, this hook sends a macOS notification
to alert the user. The question is displayed normally in the terminal —
this hook does NOT intercept or block it.

For iTerm2: uses OSC 9 which auto-focuses the correct session on click.
For others: falls back to osascript.
"""
import json
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# TTY detection
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Terminal detection
# ---------------------------------------------------------------------------

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
        if name in ("iterm2", "iterm", "itermserver-main"):
            return "iterm2"
        current = ppid

    return "unknown"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

def send_notification(message, terminal, tty):
    """Send a notification via iTerm2 OSC 9 or osascript fallback."""

    if terminal == "iterm2" and tty:
        try:
            with open(tty, "w") as f:
                f.write(f"\033]9;💬 {message}\007")
            return
        except OSError:
            pass

    subprocess.Popen(
        [
            "osascript", "-e",
            f'display notification "{message}" '
            'with title "💬 Claude Code" sound name "Glass"',
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Consume stdin (hook sends JSON via pipe) to avoid broken pipe
    try:
        sys.stdin.read()
    except (ValueError, IOError):
        pass

    tty = get_tty()
    pid = os.getppid()
    terminal = detect_terminal(pid)

    send_notification("需要你帮忙做个决定～", terminal, tty)


if __name__ == "__main__":
    main()
