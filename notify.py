#!/usr/bin/env python3
"""
claude-notify — Claude Code plugin for terminal-aware notifications.

Detects the current terminal emulator, sends a macOS notification,
and focuses the correct terminal pane/tab automatically.

Supported terminals: iTerm2 (via OSC 9), others (via osascript fallback).
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
        pids = {}  # pid -> (ppid, tty)
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
# Terminal detection via process tree
# ---------------------------------------------------------------------------

def get_process_tree():
    """Build pid -> (ppid, command) mapping from ps."""
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
        return tree
    except Exception:
        return {}


def walk_ancestors(pid, tree, max_depth=30):
    """Yield (pid, command) walking up the process tree."""
    current = pid
    depth = 0
    while current > 1 and depth < max_depth:
        info = tree.get(current)
        if info is None:
            break
        ppid, comm = info
        yield current, comm
        current = ppid
        depth += 1


def detect_terminal(pid=None):
    """Detect terminal type by walking the process tree.

    Returns one of: "iterm2", "unknown".
    """
    if pid is None:
        pid = os.getppid()

    tree = get_process_tree()

    for _, comm in walk_ancestors(pid, tree):
        name = os.path.basename(comm).lower()
        if name in ("iterm2", "iterm", "itermserver-main"):
            return "iterm2"

    return "unknown"


# ---------------------------------------------------------------------------
# Notification dispatch
# ---------------------------------------------------------------------------

def send_notification(terminal, tty, failure=False):
    """Send notification via iTerm2 OSC 9 or osascript fallback."""

    if failure:
        osc_msg = "❌ 出错了，快来看看"
        osascript_msg = "出错了，快来看看"
        osascript_title = "❌ Claude Code"
    else:
        osc_msg = "✨ 活干完了，来瞅瞅 👀"
        osascript_msg = "活干完了，来瞅瞅 👀"
        osascript_title = "✨ Claude Code"

    if terminal == "iterm2" and tty:
        # iTerm2 OSC 9: native notification with auto-focus on click
        try:
            with open(tty, "w") as f:
                f.write(f"\033]9;{osc_msg}\007")
            return
        except OSError:
            pass  # Fall through to osascript

    # osascript fallback — works on any Mac, no dependencies
    subprocess.Popen(
        [
            "osascript", "-e",
            f'display notification "{osascript_msg}" '
            f'with title "{osascript_title}" sound name "Glass"',
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

    failure = "--failure" in sys.argv

    tty = get_tty()
    pid = os.getppid()
    terminal = detect_terminal(pid)

    send_notification(terminal, tty, failure)


if __name__ == "__main__":
    main()
