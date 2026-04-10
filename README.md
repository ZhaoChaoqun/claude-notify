# claude-notify

[English](README.md) | [中文](README_CN.md)

Claude Code plugin -- click a notification, jump back to the right terminal pane.

When Claude Code needs your attention, `claude-notify` sends a macOS notification. Click it and you're taken straight to the correct terminal window, tab, and pane -- no hunting through windows.

## Supported Terminals

| Terminal | Jump Level | How It Works |
|----------|-----------|--------------|
| **iTerm2** | Session (pane) | AppleScript TTY matching |
| **tmux** | Pane | `tmux select-pane` + host terminal activation |
| **cmux** | Native | `cmux notify` with built-in panel jump |
| **Terminal.app** | Tab | AppleScript TTY matching |

Terminal detection is automatic -- zero configuration needed.

## Prerequisites

- macOS
- Python 3 (ships with macOS)
- [terminal-notifier](https://github.com/julienXX/terminal-notifier) — for notifications (not needed for cmux)
- [alerter](https://github.com/vjeantet/alerter) — optional, for approve/deny and question notifications

```bash
brew install terminal-notifier

# Optional: enables approve/deny buttons and interactive question notifications
brew install vjeantet/tap/alerter
```

Without alerter, basic notifications still work. Claude Code will fall back to its terminal-based prompts for permission requests and questions.

## Install

### From marketplace (recommended)

```bash
# 1. Add marketplace (one-time setup)
/plugin marketplace add ZhaoChaoqun/claude-plugins

# 2. Install plugin
/plugin install claude-notify@zhaochaoqun-plugins
```

### From a local clone

```bash
git clone https://github.com/ZhaoChaoqun/claude-notify.git
claude --plugin-dir ./claude-notify
```

> **Note:** Local clone mode runs directly from the cloned directory. Changes to the local files take effect immediately without any update step.

## Update

### Marketplace install

```bash
claude plugin update claude-notify@zhaochaoqun-plugins
```

After updating, run `/reload-plugins` in your Claude Code session to activate changes immediately, or restart the session.

### Local clone

```bash
cd /path/to/claude-notify
git pull
```

No restart needed — the latest code is used on the next hook invocation.

### Auto-update

Claude Code **does not auto-update plugins**. You need to manually run the update command above to get the latest version. We recommend checking for updates occasionally, especially if you encounter any issues.

## How It Works

```
Claude Code fires Stop hook (task complete, waiting for input)
        |
   notify.py reads hook input
        |
   Detects terminal type (process tree walk)
        |
   +-- cmux? --> cmux notify (native, done)
   |
   +-- other --> terminal-notifier with -execute
                        |
                  User clicks notification
                        |
                  focusers/{terminal}.sh runs
                        |
                  Terminal pane activated
```

### Terminal Detection

`notify.py` walks up the process tree from Claude's PID:

1. **cmux** -- if a `cmux` process is found, use `cmux notify`
2. **tmux** -- if a `tmux` process is found, use `tmux select-pane` + activate host terminal
3. **iTerm2** -- if `iTerm2`/`iTermServer-main` is found, use AppleScript
4. **Terminal.app** -- if `Terminal` is found, use AppleScript

### tmux Two-Layer Jump

tmux runs inside a host terminal. `claude-notify` handles both layers:

1. `tmux select-window` + `tmux select-pane` -- switch to the correct tmux pane
2. Detect and activate the host terminal app (iTerm2 or Terminal.app)

## Project Structure

```
claude-notify/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── hooks/
│   └── hooks.json           # Hook declarations
├── notify.py                # Stop hook: detect terminal, send notification
├── approve.py               # PermissionRequest hook: alerter dialog + pane focus
├── question.py              # PreToolUse hook: alerter for AskUserQuestion
├── focusers/
│   ├── iterm2.sh            # iTerm2 AppleScript focus
│   ├── terminal_app.sh      # Terminal.app AppleScript focus
│   ├── tmux.sh              # tmux pane select + host activation
│   └── cmux.sh              # cmux native notify
├── README.md
├── README_CN.md
└── LICENSE
```

## Troubleshooting

**Notifications don't appear?**
- Check that `terminal-notifier` is installed: `which terminal-notifier`
- macOS may need notification permission for terminal-notifier. Open System Settings > Notifications and ensure terminal-notifier is allowed.

**Click doesn't jump to the right pane?**
- The plugin detects terminals by walking the process tree. If Claude Code is started in an unusual way (e.g., via `ssh`), detection may fail.
- For tmux, make sure the `tmux` binary is in your `$PATH`.

**cmux notifications?**
- cmux has built-in notification support. The plugin calls `cmux notify` directly -- no terminal-notifier needed.
- Make sure `cmux` is in your `$PATH`.

## License

MIT
