"""
claude-notify common — Shared utilities for terminal detection and notification.
"""
import os
import subprocess


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
    """Detect terminal type by walking the process tree.

    Returns one of: "iterm2", "unknown".
    """
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


def _strip_control_chars(s):
    """Remove control characters (U+0000–U+001F, U+007F) from a string."""
    return "".join(c for c in s if c >= " " and c != "\x7f")


def _escape_applescript(s):
    """Escape a string for use inside AppleScript double quotes."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def send_notification(title, message, terminal, tty):
    """Send a notification via iTerm2 OSC 9 or osascript fallback.

    Args:
        title: Notification title (e.g. "✨ Claude Code").
        message: Notification body text.
        terminal: Terminal type from detect_terminal().
        tty: TTY path from get_tty().
    """
    clean_title = _strip_control_chars(title or "")
    clean_message = _strip_control_chars(message)
    osc_msg = f"{clean_title}: {clean_message}" if clean_title else clean_message

    if terminal == "iterm2" and tty:
        try:
            with open(tty, "w") as f:
                f.write(f"\033]9;{osc_msg}\007")
            return
        except OSError:
            pass

    safe_title = _escape_applescript(clean_title or "Claude Code")
    safe_message = _escape_applescript(clean_message)
    subprocess.Popen(
        [
            "osascript", "-e",
            f'display notification "{safe_message}" '
            f'with title "{safe_title}" sound name "Glass"',
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
