# claude-notify

[English](README.md) | [中文](README_CN.md)

Claude Code 插件 -- 收到通知，点击即跳转到对应的终端窗格。

当 Claude Code 需要你的关注时，`claude-notify` 会发送 macOS 原生通知。点击通知即可自动跳转到正确的终端窗口、标签页和窗格，无需手动翻找。

## 支持的终端

| 终端 | 跳转级别 | 实现方式 |
|------|---------|---------|
| **iTerm2** | Session（窗格） | AppleScript TTY 匹配 |
| **tmux** | Pane（窗格） | `tmux select-pane` + 宿主终端激活 |
| **cmux** | 原生 | `cmux notify` 内建面板跳转 |
| **Terminal.app** | 标签页 | AppleScript TTY 匹配 |

终端类型自动检测，无需任何配置。

## 前置依赖

- macOS
- Python 3（macOS 自带）
- [terminal-notifier](https://github.com/julienXX/terminal-notifier) — 用于发送通知（cmux 不需要）
- [alerter](https://github.com/vjeantet/alerter) — 可选，用于权限审批和问题交互通知

```bash
brew install terminal-notifier

# 可选：启用审批按钮和问题交互通知
brew install vjeantet/tap/alerter
```

未安装 alerter 时，基础通知功能仍然正常。Claude Code 会回退到终端内的权限确认和问题交互界面。

## 安装

### 从 Marketplace 安装（推荐）

```bash
# 1. 添加 marketplace（仅需一次）
/plugin marketplace add ZhaoChaoqun/claude-plugins

# 2. 安装插件
/plugin install claude-notify@zhaochaoqun-plugins
```

### 从本地克隆安装

```bash
git clone https://github.com/ZhaoChaoqun/claude-notify.git
claude --plugin-dir ./claude-notify
```

> **提示：** 本地克隆模式直接运行克隆目录中的文件，修改本地文件后立即生效，无需额外更新步骤。

## 更新

### Marketplace 安装方式

```bash
claude plugin update claude-notify@zhaochaoqun-plugins
```

更新后，在 Claude Code session 中运行 `/reload-plugins` 即可立即生效，或者重启 session。

### 本地克隆方式

```bash
cd /path/to/claude-notify
git pull
```

无需重启，下次 hook 触发时即使用最新代码。

### 关于自动更新

Claude Code **不会自动更新插件**。你需要手动执行上述更新命令来获取最新版本。建议定期检查更新，尤其是遇到问题时。

## 工作原理

```
Claude Code 触发 Stop hook（任务完成，等待输入）
        |
   notify.py 读取 hook 输入
        |
   检测终端类型（遍历进程树）
        |
   +-- cmux? --> cmux notify（原生通知，完成）
   |
   +-- 其他 --> terminal-notifier 发送通知
                        |
                  用户点击通知
                        |
                  focusers/{terminal}.sh 执行
                        |
                  终端窗格被激活
```

### 终端检测

`notify.py` 从 Claude 的 PID 向上遍历进程树：

1. **cmux** -- 发现 `cmux` 进程，使用 `cmux notify`
2. **tmux** -- 发现 `tmux` 进程，使用 `tmux select-pane` + 激活宿主终端
3. **iTerm2** -- 发现 `iTerm2`/`iTermServer-main`，使用 AppleScript
4. **Terminal.app** -- 发现 `Terminal`，使用 AppleScript

### tmux 双层跳转

tmux 运行在宿主终端内，`claude-notify` 同时处理两层：

1. `tmux select-window` + `tmux select-pane` -- 切换到正确的 tmux 窗格
2. 检测并激活宿主终端（iTerm2 或 Terminal.app）

## 项目结构

```
claude-notify/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据
├── hooks/
│   └── hooks.json           # Hook 声明
├── notify.py                # Stop hook：检测终端，发送通知
├── approve.py               # PermissionRequest hook：alerter 对话框 + 窗格聚焦
├── question.py              # PreToolUse hook：alerter 处理 AskUserQuestion
├── focusers/
│   ├── iterm2.sh            # iTerm2 AppleScript 聚焦
│   ├── terminal_app.sh      # Terminal.app AppleScript 聚焦
│   ├── tmux.sh              # tmux 窗格选择 + 宿主终端激活
│   └── cmux.sh              # cmux 原生通知
├── README.md
├── README_CN.md
└── LICENSE
```

## 常见问题

**通知没有出现？**
- 检查 `terminal-notifier` 是否已安装：`which terminal-notifier`
- macOS 可能需要通知权限。打开 系统设置 > 通知，确保 terminal-notifier 被允许。

**点击通知没有跳转到正确的窗格？**
- 插件通过遍历进程树来检测终端。如果 Claude Code 以非常规方式启动（如通过 `ssh`），检测可能失败。
- 使用 tmux 时，确保 `tmux` 在你的 `$PATH` 中。

**cmux 通知？**
- cmux 内建通知支持，插件直接调用 `cmux notify`，不需要 terminal-notifier。
- 确保 `cmux` 在你的 `$PATH` 中。

## License

MIT
