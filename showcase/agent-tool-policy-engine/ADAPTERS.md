# Adapter Boundary

## Generic

`GenericPolicyAdapter` 將結構化 `ToolCall` 丟給 pure evaluator。它不執行工具。

## Local CLI / MCP handler

`LocalToolAdapter.preflight(argv, cwd=...)` 只解析 command 與 target，回傳決策。真正的 handler 必須在收到 `allow`／`allow_scoped` 後自行執行；其餘結果交給 host approval 或停止。

目前 enforcement status：`unsupported_preflight_only`。這個 adapter 不宣稱能攔截沒有 pre-execution hook 的 handler。

## Codex

`codex_rules.render_safe_rules()` 只輸出 preview。由於本機 Codex rules 是命令前綴規則，不是完整 side-effect schema，不能宣稱它取代 Policy Core。正式安裝前需人工 review，並使用 Codex 原生 approval/sandbox。

目前 enforcement status：`unsupported_preview_only`。

## Agents SDK

本 PoC 不依賴 SDK。可由 host 將 `Decision.REQUIRE_APPROVAL` 映射到 dynamic `needs_approval`，將 `DENY` 直接拒絕；若 host 沒有相同 hook，就只能 report-only。
