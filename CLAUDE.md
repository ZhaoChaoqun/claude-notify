# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

claude-notify is a Claude Code plugin for macOS that sends native notifications when Claude completes tasks or needs user input. Currently supports iTerm2 (via OSC 9 with auto-focus) with osascript as fallback for other terminals.

## Architecture

Two hook entry points, each reading JSON from stdin:

- **notify.py** (Stop hook) — Detects terminal type by walking the process tree, sends notification via iTerm2 OSC 9 (auto-focuses on click) or osascript fallback
- **question.py** (PreToolUse hook, AskUserQuestion only) — Same notification mechanism, alerts user when Claude asks a question

**hooks/hooks.json** — Declares hook bindings (Stop, StopFailure, PreToolUse) that Claude Code uses to invoke the Python scripts.

## Key Patterns

- **Process tree walking**: All detection logic walks parent PIDs via `ps -axo pid=,ppid=,tty=` to find terminal type and TTY
- **iTerm2 OSC 9**: Writes `\033]9;message\007` to TTY — triggers native macOS notification that auto-focuses the correct iTerm2 session on click
- **Graceful degradation**: Falls back to `osascript display notification` when not in iTerm2
- **No external dependencies**: Uses only Python stdlib and macOS built-in tools
- **macOS only**: Relies on osascript and OSC escape sequences

## Notification Dispatch Order

1. iTerm2 detected → OSC 9 escape sequence to TTY (native notification, auto-focuses on click)
2. Other/unknown → `osascript display notification` fallback

## Prerequisites

- macOS with Python 3
- iTerm2 (recommended, for best experience with auto-focus)

## Testing

No automated test suite. Manual testing by running Claude Code in iTerm2.

## Development

Plugin is installed via `claude plugin add --plugin-dir /path/to/claude-notify`. Hook commands use `${CLAUDE_PLUGIN_ROOT}` to resolve script paths. All scripts are invoked as `python3 ${CLAUDE_PLUGIN_ROOT}/{script}.py` with JSON on stdin.
