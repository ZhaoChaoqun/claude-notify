# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

claude-notify is a Claude Code plugin for macOS that sends native notifications when Claude completes tasks and auto-focuses the correct terminal pane when clicked. Supports iTerm2, Terminal.app, tmux, and cmux.

## Architecture

Three hook entry points, each reading JSON from stdin and writing JSON to stdout:

- **notify.py** (Stop hook) — Detects terminal type by walking the process tree, sends a macOS notification, then runs the matching focuser script to jump to the correct pane
- **approve.py** (PermissionRequest hook) — Shows a macOS `alerter` dialog with Approve/Deny buttons for permission requests; falls back silently if alerter is not installed
- **question.py** (PreToolUse hook, AskUserQuestion only) — Shows `alerter` dialog with up to 3 option buttons; falls back to terminal for complex questions

**focusers/** — Shell scripts that activate the correct terminal pane via AppleScript or CLI:
- `iterm2.sh` — Searches iTerm2 sessions by TTY, selects tab+session
- `terminal_app.sh` — Searches Terminal.app tabs by TTY
- `tmux.sh` — Two-layer: selects tmux pane by TTY/PID, then activates the host terminal (iTerm2 or Terminal.app)
- `cmux.sh` — Delegates to `cmux notify` CLI

**hooks/hooks.json** — Declares hook bindings (Stop, PermissionRequest, PreToolUse) that Claude Code uses to invoke the Python scripts.

## Key Patterns

- **Process tree walking**: All detection logic walks parent PIDs via `ps -axo pid=,ppid=,tty=` to find terminal type and TTY
- **Graceful degradation**: Falls back to simpler notification methods when tools (terminal-notifier, alerter) are unavailable; hooks exit silently on failure
- **Detached processes**: Notifications dispatched via `subprocess.Popen(start_new_session=True)` to avoid blocking Claude Code
- **No external Python dependencies**: Uses only stdlib (subprocess, json, sys, os)
- **macOS only**: Relies on AppleScript, osascript, OSC escape sequences

## Notification Dispatch Order (notify.py)

1. cmux detected → `cmux notify`
2. tmux detected → `terminal-notifier` + tmux pane select + host terminal focus
3. iTerm2 detected → OSC 9 escape sequence to TTY (native, auto-focuses)
4. Terminal.app detected → `terminal-notifier` + AppleScript focus
5. Unknown → `osascript` fallback

## Prerequisites

- macOS with Python 3
- `terminal-notifier` (`brew install terminal-notifier`) — for notifications
- `alerter` (`brew install vjeantet/tap/alerter`) — for permission/question dialogs

## Testing

No automated test suite. Manual testing by running Claude Code in different terminal configurations (bare terminal, tmux, nested tmux+iTerm2, cmux).

## Development

Plugin is installed via `claude plugin add --plugin-dir /path/to/claude-notify`. Hook commands use `${CLAUDE_PLUGIN_ROOT}` to resolve script paths. All scripts are invoked as `python3 ${CLAUDE_PLUGIN_ROOT}/{script}.py` with JSON on stdin.
