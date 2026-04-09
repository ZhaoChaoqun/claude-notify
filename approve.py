#!/usr/bin/env python3
"""
claude-notify approve — PermissionRequest hook for Claude Code.

Reads the PermissionRequest event from stdin, shows a macOS alert via
`alerter` with Approve/Deny buttons, and returns the user's decision
as JSON on stdout so Claude Code can proceed without terminal interaction.

Requires: alerter (brew install alerter)
If alerter is not installed, exits silently to let Claude Code fall back
to its normal terminal-based permission prompt.
"""
import json
import os
import shutil
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))
FOCUSERS_DIR = os.path.join(PLUGIN_ROOT, "focusers")
ALERTER_TIMEOUT = 120  # seconds before auto-fallback


def find_alerter():
    """Find alerter binary."""
    path = shutil.which("alerter")
    if path:
        return path
    for p in ("/opt/homebrew/bin/alerter", "/usr/local/bin/alerter"):
        if os.path.isfile(p):
            return p
    return None


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
        if "cmux" in name:
            return "cmux"
        if name.startswith("tmux"):
            return "tmux"
        if name in ("iterm2", "iterm", "itermserver-main"):
            return "iterm2"
        if name in ("terminal", "terminal.app"):
            return "terminal_app"
        current = ppid

    return "unknown"


def focus_terminal(terminal, tty, pid):
    """Focus the correct terminal pane/tab by running the focuser script."""
    focus_script = os.path.join(FOCUSERS_DIR, f"{terminal}.sh")
    if not os.path.isfile(focus_script) or not tty:
        return
    subprocess.Popen(
        ["bash", focus_script, tty, str(pid or "")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def summarize_tool_input(tool_name, tool_input):
    """Build a human-readable summary of the tool call."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if len(cmd) > 200:
            cmd = cmd[:200] + "..."
        return cmd
    if tool_name in ("Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "Read":
        return tool_input.get("file_path", "")
    if tool_name in ("Glob", "Grep"):
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", "")
        return f"{pattern} in {path}" if path else pattern
    if tool_name == "WebFetch":
        return tool_input.get("url", "")
    if tool_name == "WebSearch":
        return tool_input.get("query", "")
    if tool_name == "Agent":
        return tool_input.get("prompt", "")[:200]
    if tool_name == "ExitPlanMode":
        prompts = tool_input.get("allowedPrompts", [])
        if not prompts:
            return "计划已就绪，等待审批"
        items = [p.get("prompt", "") for p in prompts if p.get("prompt")]
        if items:
            return "计划已就绪: " + ", ".join(items)
        return "计划已就绪，等待审批"
    # MCP tools or unknown
    return json.dumps(tool_input, ensure_ascii=False)[:200]


def main():
    try:
        stdin_data = sys.stdin.read()
        data = json.loads(stdin_data) if stdin_data.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return

    if data.get("hook_event_name") != "PermissionRequest":
        return

    alerter = find_alerter()
    if not alerter:
        return  # No alerter — fall back to terminal prompt

    tool_name = data.get("tool_name", "Unknown Tool")
    tool_input = data.get("tool_input", {})
    summary = summarize_tool_input(tool_name, tool_input)

    # Collect TTY and terminal info before blocking on alerter
    tty = get_tty()
    pid = os.getppid()
    terminal = detect_terminal(pid)

    try:
        result = subprocess.run(
            [
                alerter,
                "--title", f"Claude Code — {tool_name}",
                "--message", summary,
                "--close-label", "Deny",
                "--actions", "Approve",
                "--timeout", str(ALERTER_TIMEOUT),
                "--sound", "default",
            ],
            capture_output=True, text=True, timeout=ALERTER_TIMEOUT + 5,
        )
        answer = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return  # Timeout or error — fall back to terminal prompt

    if answer == "Approve":
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        }
        focus_terminal(terminal, tty, pid)
    elif answer in ("Deny", "@CLOSED"):
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": "User denied via notification",
                },
            }
        }
        focus_terminal(terminal, tty, pid)
    else:
        # @TIMEOUT or unexpected — fall back to terminal prompt
        return

    json.dump(decision, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
