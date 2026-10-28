# Thin Agent Tool Policy Engine

本 staging PoC 是一個零 runtime dependency 的 deterministic policy core。它把 host 提供的結構化 tool-call 資訊收斂成四種結果：`allow`、`allow_scoped`、`require_approval`、`deny`。

## 已實作

- 跨平台 path / repo / branch / domain 正規化。
- 只看結構化訊號的 side-effect classifier；不把 prompt 或「模型說安全」當成安全邊界。
- TOML policy loader 與 scope / protected branch 比對。
- fail-safe unknown side effect、critical default deny、prompt override 不可放寬決策。
- JSONL audit event；target 只留 fingerprint，secret-like 欄位與值會 redact。
- `LocalToolAdapter`：只做 CLI/MCP handler preflight，不執行 command。
- `codex_rules`：產生可人工檢視的 Codex rules preview，不自動安裝。

## 邊界

這不是 Gateway、daemon、sandbox、approval UI，也不能攔截沒有 hook 的 first-party tool。Codex 的 sandbox、approval、rules、network policy 與 host telemetry 仍是主要 enforcement；此 core 只補跨 adapter 的一致分類與驗證。

目前是 Private GitHub staging repository：`https://github.com/a275618631/agent-tool-policy-engine`，branch `codex/staging`。本輪 staging convergence 版本為 `0.1.1-staging`；既有 `v0.1.0-staging` 保留。未寫入 `~/.codex`、未修改 shared skills、未修改 AGENTS.md、未啟用 production enforce。

## 執行測試

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 目前決策

先保留 report-only / preflight adapter；尚未接入真實高風險工具，也未啟用 enforce。24 個本機 tests 與 synthetic MCP-style gate 已 PASS；Windows automated CI 已完成，但不等同 Windows Codex runtime verified；Antigravity hard enforcement 仍是 unsupported / not yet available。

## Staging evidence

- Implementation commit：`7093053ad17421d170d18c04bfad2b9452d92a22`
- Staging convergence tag：`v0.1.1-staging`（既有 `v0.1.0-staging` 保留）
- Local tests：24 PASS；compileall PASS。
- GitHub Actions：Ubuntu/macOS/Windows × Python 3.11/3.12，6/6 PASS。
- CI run：https://github.com/a275618631/agent-tool-policy-engine/actions/runs/32715119736
- Remote branch dry-run：PASS；未建立 `chore/dry-run-policy` branch。
- Synthetic MCP-style E2E：PASS；external／critical decision 在 disposable handler 前停止。
- Disposable local bare-repo policy dry-run：PASS；未對真實 production 或重要 Repo 做 destructive test。
