# Provenance & Verification Boundary｜Codex × Antigravity 協作架構

- **專案代號**：`codex-antigravity-collaboration`
- **原始來源**：GitHub 公開倉庫 [`a275618631/codex-antigravity-collaboration`](https://github.com/a275618631/codex-antigravity-collaboration)
- **來源 Commit SHA**：`3a04e3ff6f35489d36d3fa1ec74b59a9d267a977`
- **同步日期**：2026-10-28
- **同步方式**：公開倉庫 Commit-pinned 快照鏡像（排除 `.git` 歷史、私有 Inbox Token 與本地工作區暫存檔）

---

## 驗證證據狀態 (Evidence Status)

| 元件 / 流程 | 狀態標籤 | 驗證內容與說明 |
|---|---|---|
| **Bounded Task/Result Schema** | **VERIFIED** | 結構化 JSON Schema 驗證通過，欄位涵蓋嚴格白名單、雜湊值校驗與路徑正規化。 |
| **Local Bridge 協定規格** | **VERIFIED (Mock)** | 通過本機雙程序檔案鎖與狀態模擬測試；已驗證並行安全防護。 |
| **Windows 前景交接 (Once Mode)** | **VERIFIED (CLI)** | 於專用私有沙盒倉庫通過 Windows 前景單次觸發 E2E 測試。 |
| **全自動雙 Runtime 即時交接** | **LIVE_BLOCKED** | 目前雙平台交接受限於原生沙盒與環境隔離，**非常駐背景 Daemon**。實際交接必須經由本機受信任前景程序及人工核准 (Human Gate)。 |

---

## 安全邊界宣告 (Mandatory Boundaries)

1. **嚴格拒絕自動 Merge**：本協作架構刻意不提供自動合併 PR 之功能，所有變更一律以 Feature 分支提交，並由人工審查後合併。
2. **One-Hop 限制**：跨 Runtime 委派嚴格限制最多 1 跳，禁止遞迴回調造成循環或死鎖。
3. **One Active Writer 原則**：同一工作區或寫入範圍同一時間僅允許單一 Agent 進行寫入操作。
4. **不包含敏感金鑰**：公開展示僅包含協議規範、架構文件與 Mock 驗證程式碼，不包含任何實際私有 Inbox Repo 之存取 Token 或本機私鑰。
