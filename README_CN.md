# claude-notify

[English](README.md) | [中文](README_CN.md)

Claude Code 插件 -- 收到通知，点击即跳转到对应的终端窗格。

当 Claude Code 需要你的关注时，`claude-notify` 会发送 macOS 原生通知。在 iTerm2 中，点击通知即可自动跳转到正确的 session，无需手动翻找。

## 通知方式

| 终端 | 通知方式 | 点击跳转 |
|------|---------|---------|
| **iTerm2** | OSC 9（原生） | 自动聚焦到对应 session |
| **其他** | osascript（macOS 内建） | 无自动聚焦 |

终端类型自动检测，无需任何配置。

## 前置依赖

- macOS
- Python 3（macOS 自带）
- iTerm2（推荐，获得最佳体验）

无需安装任何第三方工具，无需 `brew install`。

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
   +-- iTerm2? --> OSC 9 写入 TTY（原生通知，点击自动聚焦）
   |
   +-- 其他 --> osascript display notification（macOS 内建）
```

### 终端检测

`notify.py` 从 Claude 的 PID 向上遍历进程树。如果发现 iTerm2 进程，使用 OSC 9 发送原生通知（点击自动聚焦）。否则回退到 `osascript display notification`。

## 项目结构

```
claude-notify/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据
├── hooks/
│   └── hooks.json           # Hook 声明
├── notify.py                # Stop hook：检测终端，发送通知
├── question.py              # PreToolUse hook：AskUserQuestion 通知
├── README.md
├── README_CN.md
└── LICENSE
```

## 常见问题

**通知没有出现？**
- 在 iTerm2 中：检查 Preferences > Profiles > Terminal > "Enable notifications" 是否开启。
- macOS 可能需要通知权限。打开 系统设置 > 通知，确保 iTerm2 被允许。

**点击通知没有跳转到正确的窗格？**
- 自动聚焦仅在 iTerm2 中通过 OSC 9 实现。其他终端使用 osascript，不支持点击跳转。
- 插件通过遍历进程树来检测终端。如果 Claude Code 以非常规方式启动（如通过 `ssh`），检测可能失败。

## License

MIT
