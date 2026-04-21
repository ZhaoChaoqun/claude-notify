# claude-notify

[English](README.md) | [中文](README_CN.md)

Claude Code plugin -- click a notification to jump back to the right terminal pane.

When Claude Code needs your attention, `claude-notify` sends a macOS notification. In iTerm2, clicking the notification takes you straight to the correct session -- no hunting through windows.

## How Notifications Work

| Terminal | Notification | Click to Focus |
|----------|-------------|----------------|
| **iTerm2** | OSC 9 (native) | Auto-focuses the correct session |
| **Other** | osascript (macOS built-in) | No auto-focus |

Terminal detection is automatic -- zero configuration needed.

## Prerequisites

- macOS
- Python 3 (ships with macOS)
- iTerm2 (recommended, for the best experience)

No third-party tools required. No `brew install` needed.

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
   +-- iTerm2? --> OSC 9 to TTY (native notification, auto-focus on click)
   |
   +-- other --> osascript display notification (macOS built-in)
```

### Terminal Detection

`notify.py` walks up the process tree from Claude's PID. If an iTerm2 process is found, it uses OSC 9 for native notifications with auto-focus. Otherwise, it falls back to `osascript display notification`.

## Project Structure

```
claude-notify/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── hooks/
│   └── hooks.json           # Hook declarations
├── notify.py                # Stop hook: detect terminal, send notification
├── question.py              # PreToolUse hook: notification for AskUserQuestion
├── README.md
├── README_CN.md
└── LICENSE
```

## Troubleshooting

**Notifications don't appear?**
- In iTerm2: check Preferences > Profiles > Terminal > "Enable notifications" is on.
- macOS may need notification permission for iTerm2. Open System Settings > Notifications and ensure iTerm2 is allowed.

**Click doesn't jump to the right pane?**
- Auto-focus only works in iTerm2 via OSC 9. Other terminals use osascript which does not support click-to-focus.
- The plugin detects terminals by walking the process tree. If Claude Code is started in an unusual way (e.g., via `ssh`), detection may fail.

## License

MIT
