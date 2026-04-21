#!/usr/bin/env python3
"""
claude-notify question — PreToolUse hook for AskUserQuestion.

Sends a macOS notification when Claude asks the user a question.
"""
import os
import sys

from common import detect_terminal, get_tty, send_notification


def main():
    try:
        sys.stdin.read()
    except (ValueError, IOError):
        pass

    tty = get_tty()
    terminal = detect_terminal(os.getppid())
    send_notification("💬 Claude Code", "需要你帮忙做个决定～", terminal, tty)


if __name__ == "__main__":
    main()
