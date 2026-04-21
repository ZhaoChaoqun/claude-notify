#!/usr/bin/env python3
"""
claude-notify — Stop hook.

Sends a macOS notification when Claude completes a task.
Extracts the last assistant message from the transcript for a richer notification.
"""
import json
import os
import sys

from common import detect_terminal, get_tty, send_notification


def extract_last_message(stdin_data):
    """Extract the last assistant text from the session transcript."""
    try:
        data = json.loads(stdin_data)
        transcript_path = data.get("transcript_path", "")
        if not transcript_path or not os.path.isfile(transcript_path):
            return ""

        last_text = ""
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                # content can be a string or a list of blocks
                content = msg.get("content", "")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, str):
                            parts.append(block)
                        elif isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                    text = "".join(parts)
                else:
                    continue
                if text.strip():
                    last_text = text.strip()
        return last_text
    except Exception:
        return ""


def main():
    stdin_data = ""
    try:
        stdin_data = sys.stdin.read()
    except (ValueError, IOError):
        pass

    title = "✨ Claude Code"
    last_msg = extract_last_message(stdin_data)
    if last_msg:
        summary = last_msg.rsplit("\n", 1)[-1].strip()
        if len(summary) > 80:
            summary = summary[:77] + "..."
        message = summary or "活干完了，来瞅瞅 👀"
    else:
        message = "活干完了，来瞅瞅 👀"

    tty = get_tty()
    terminal = detect_terminal(os.getppid())
    send_notification(title, message, terminal, tty)


if __name__ == "__main__":
    main()
