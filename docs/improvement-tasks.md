# claude-notify 优化任务追踪

基于 [Claude Code Hooks 官方文档](https://code.claude.com/docs/en/hooks) 对比分析得出的改进项。

---

## 任务列表

### 1. 提取公共模块，消除代码重复
- **优先级**：🔴 高
- **状态**：✅ 已完成
- **说明**：`notify.py`、`question.py`、`notification.py` 中 `get_tty()`、`detect_terminal()`、`send_notification()` 逻辑完全相同。提取到 `common.py`，三个脚本只保留各自的 `main()` 逻辑。
- **影响**：可维护性，后续新增 hook 脚本时不再复制粘贴

### 2. 使用 `async: true` 避免阻塞 Claude
- **优先级**：🔴 高
- **状态**：✅ 已完成
- **说明**：发通知不需要返回结果给 Claude，在 `hooks.json` 中为所有 hook 添加 `"async": true`，让通知脚本异步执行，不阻塞 Claude 的响应流程。
- **影响**：性能，避免 `ps` 命令或通知发送拖慢 Claude

### 3. 解析 stdin 展示问题摘要
- **优先级**：🔴 高
- **状态**：✅ 已完成
- **说明**：`question.py` 的 PreToolUse hook 收到的 stdin JSON 包含 `tool_input`，里面有 Claude 要问用户的具体问题。当前通知只显示通用文本"需要你帮忙做个决定"，应解析 stdin 将问题摘要放入通知，让用户在通知中就能预览问题内容。
- **影响**：用户体验，通知信息量更大

### 4. Hook `Notification` 事件
- **优先级**：🟡 中
- **状态**：✅ 已完成
- **说明**：官方提供了专门的 `Notification` 事件，覆盖 `permission_prompt`（权限请求）、`idle_prompt`（空闲等待）、`elicitation_dialog`（MCP 对话框）、`auth_success`（认证成功）等场景。该事件 input 直接包含 `message` 和 `title`，是为通知插件量身设计的。
- **影响**：功能完整性，覆盖更多需要用户关注的场景

### 5. Hook `PermissionRequest` 事件
- **优先级**：🟡 中
- **状态**：❌ 已取消
- **说明**：当 Claude 请求执行需要权限的工具时触发。经评估，`Notification` 事件的 `permission_prompt` 类型已覆盖此场景——当 Claude 等待权限审批时会触发 Notification，`notification.py` 已能发送通知。PermissionRequest 的设计目的是拦截/自动审批权限，非通知用途，hook 它只会产生重复通知。
- **影响**：用户体验，减少用户错过权限请求的情况

### 6. 清理 `plugin.json` keywords
- **优先级**：🟢 低
- **状态**：✅ 已完成
- **说明**：`plugin.json` 的 keywords 中仍包含 `"tmux"`、`"cmux"`，但相关功能已在之前的简化中移除，应删除这些过时的关键词。
- **影响**：元数据准确性

---

## 状态说明

| 标记 | 含义 |
|------|------|
| ⬜ 待开始 | 尚未开始 |
| 🔄 进行中 | 正在实施 |
| ✅ 已完成 | 已完成并验证 |
| ❌ 已取消 | 评估后决定不做 |

## 更新日志

- **2026-04-21**：创建任务列表，共 6 项优化任务
- **2026-04-21**：完成任务 4 — 新增 `notification.py`，hook `Notification` 事件
- **2026-04-21**：完成任务 1 — 提取 `common.py` 公共模块，三个脚本从 ~130 行精简到 ~30 行
- **2026-04-21**：完成任务 3 — `question.py` 解析 stdin 中的问题文本，通知展示问题摘要
- **2026-04-21**：完成任务 2 — 所有 hook 添加 `async: true`，避免阻塞 Claude
- **2026-04-21**：完成任务 6 — 清理 `plugin.json` keywords，移除 tmux/cmux
- **2026-04-21**：取消任务 5 — PermissionRequest 与 Notification(permission_prompt) 功能重复
