#!/usr/bin/env python3
"""
claude-notify notification — Hook for Notification events.

Sends a macOS notification when Claude Code fires a Notification event
(permission_prompt, idle_prompt, elicitation_dialog, auth_success).
Parses title and message from stdin JSON.
"""
import json
import os
import sys

from common import detect_terminal, get_tty, send_notification


def main():
    title = "Claude Code"
    message = "需要你的关注"

    try:
        stdin_data = sys.stdin.read()
        if stdin_data:
            data = json.loads(stdin_data)
            title = data.get("title", title)
            message = data.get("message", message)
    except (ValueError, IOError, json.JSONDecodeError):
        pass

    tty = get_tty()
    terminal = detect_terminal(os.getppid())
    send_notification(title, message, terminal, tty)


if __name__ == "__main__":
    main()
