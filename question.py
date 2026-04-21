#!/usr/bin/env python3
"""
claude-notify question — PreToolUse hook for AskUserQuestion.

Sends a macOS notification when Claude asks the user a question.
Parses the first question text from stdin JSON for a richer notification.
"""
import json
import os
import sys

from common import detect_terminal, get_tty, send_notification


def extract_question(stdin_data):
    """Extract the first question text from PreToolUse AskUserQuestion input."""
    try:
        data = json.loads(stdin_data)
        questions = data.get("tool_input", {}).get("questions", [])
        if questions and isinstance(questions, list):
            return questions[0].get("question", "")
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return ""


def main():
    stdin_data = ""
    try:
        stdin_data = sys.stdin.read()
    except (ValueError, IOError):
        pass

    question = extract_question(stdin_data)
    if len(question) > 80:
        question = question[:77] + "..."
    message = question or "需要你帮忙做个决定～"

    tty = get_tty()
    terminal = detect_terminal(os.getppid())
    send_notification("💬 Claude Code", message, terminal, tty)


if __name__ == "__main__":
    main()
