# Codex × Antigravity｜跨 AI 開發環境協作

當 Codex 和 Antigravity 同時參與一個專案，最大的難題未必是讓兩邊互相傳訊息，而是**誰負責做事、交接時要帶什麼資訊，以及如何避免兩邊修改同一批檔案**。

我以兩套 AI 開發環境為例，整理共同的任務與結果格式，搭配本地 MCP Bridge、Git 分支與 worktree，讓協作過程能分工、回報並保留可檢查的結果。

[繁體中文完整架構說明](README.zh-TW.md) · [專案架構網站](https://a275618631.github.io/codex-antigravity-collaboration/)

## 設計重點

- **依能力分工**：Codex 偏向程式修改與測試，Antigravity 可負責需要其他整合工具的工作；實際分工依工具可用性調整。
- **任務與結果格式**：把目標、修改範圍、驗證方式、結果與剩餘事項寫進共同契約，減少交接資訊遺漏。
- **限制跨平台委派次數**：避免兩套 Runtime 無限互相轉派。
- **降低檔案衝突**：使用 Git branch、worktree 和 PR 管理可追蹤的修改。
- **本地橋接**：用 MCP 工具與 JSONL mailbox 傳送、讀取訊息，搭配跨平台檔案鎖處理併發存取。
- **共用 Skills**：把可攜的工作方式留在共同規範，平台差異交由薄 Adapter 處理。

## 一個協作任務

```text
提出需求
   ↓
整理任務與可修改範圍
   ↓
指定適合的 Runtime 執行
   ↓
工作分支中修改與測試
   ↓
回傳結果、證據和剩餘工作
   ↓
人工審閱並決定是否合併
```

這個方式適合研究多 Agent 怎麼共用既有 GitHub 工作流，而不是另外建一套龐大的任務排程器。

## 已完成的部分

專案包含 Task/Result 契約、有限次委派規則、本地 MCP Bridge 與相關自動化測試。Windows 本地橋接曾通過雙程序測試，跨 Runtime 也有受限的唯讀測試紀錄。

桌面端完整即時雙向協作及無人值守寫入，目前仍不是已驗收的使用方式。想了解具體進度，可看[繁體中文狀態與設計](README.zh-TW.md)及原始[獨立專案倉庫](https://github.com/a275618631/codex-antigravity-collaboration)。

## 程式與文件

- [本地 MCP Bridge 使用說明](https://github.com/a275618631/codex-antigravity-collaboration/blob/main/local_bridge/README.md)
- [本地交接工具技術入口](https://github.com/a275618631/codex-antigravity-collaboration/blob/main/github_handoff/README_GITHUB_HANDOFF_20260929.md)
- [架構與協作設計](docs/ARCHITECTURE.md)
