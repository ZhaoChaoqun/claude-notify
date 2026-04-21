#!/usr/bin/env python3
"""
claude-notify — Stop/StopFailure hook.

Sends a macOS notification when Claude completes a task or encounters an error.
Pass --failure for error notifications.
"""
import os
import sys

from common import detect_terminal, get_tty, send_notification


def main():
    try:
        sys.stdin.read()
    except (ValueError, IOError):
        pass

    failure = "--failure" in sys.argv

    if failure:
        title = "❌ Claude Code"
        message = "出错了，快来看看"
    else:
        title = "✨ Claude Code"
        message = "活干完了，来瞅瞅 👀"

    tty = get_tty()
    terminal = detect_terminal(os.getppid())
    send_notification(title, message, terminal, tty)


if __name__ == "__main__":
    main()
