# Provenance & Verification Boundary｜Thin Agent Tool Policy Engine

- **專案代號**：`agent-tool-policy-engine`
- **原始來源**：GitHub 私有倉庫 [`a275618631/agent-tool-policy-engine`](https://github.com/a275618631/agent-tool-policy-engine)
- **來源分支與 Commit SHA**：`codex/staging` · `188421cb92ab772cb29e39f3e03fe6a52d91bbd3`（Staging Tag: `v0.1.1-staging`）
- **同步日期**：2026-10-28
- **同步方式**：私有倉庫 Commit-pinned 快照脫敏匯出（排除 `.git` 歷史與本地環境設定）

---

## 驗證證據狀態 (Evidence Status)

- **單元測試驗證**：**24 PASS**（執行 `PYTHONPATH=src python -m unittest discover -s tests -v`，0 外部依賴，測試耗時 < 0.1s）。
- **CI / 跨平台支援**：已通過 GitHub Actions（Ubuntu, macOS, Windows × Python 3.11/3.12，6/6 PASS）。
- **Synthetic MCP-style Gate**：**PASS**（在 disposable handler 前攔截 external 與 critical 操作）。

---

## 安全邊界與限制宣告 (Mandatory Boundaries)

1. **Staging Preflight 聲明**：本專案為 **staging preflight / report-only 決定論核心**，非已部署之生產 Gateway、Daemon 或硬性沙盒。
2. **零憑證與脫敏審計**：Audit Log 僅保留 target fingerprint 與正規化路徑，包含 Token 或 Password 欄位一律遮蔽 (Redacted)。
3. **Fail-Closed 原則**：對於未知副作用 (Unknown Side Effect) 或格式損壞之 Tool-call，策略一律採取預設拒絕 (`deny`)。
