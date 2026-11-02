# Codex × Antigravity｜跨 AI 開發環境協作

當 Codex 和 Antigravity 同時參與一個專案，如何分工、交接結果，並避免互相修改同一批程式？

我以兩套 AI 開發環境做實際案例，建立共同的 Task／Result 格式、有限次跨平台委派，以及 Git 分支和 worktree 的協作方式。需要本地交換訊息時，再透過 MCP Bridge 與 JSONL mailbox 連接。

## 可以看到什麼

- **任務與結果格式**：每次交接都知道目標、可修改範圍、驗收條件和測試結果。
- **有限次委派**：不同 Agent 不會無限互相轉交工作。
- **本地橋接**：MCP Bridge 使用本地訊息檔案與檔案鎖處理通訊。
- **Git 協作**：以 branch、worktree 和 PR 管理可能衝突的修改。

## 實作與驗證

已建置本地 Bridge、協作契約與相關測試。Windows 本地 Bridge 曾通過雙程序測試，2026-10-20 亦有受限跨 Runtime 唯讀交接成功紀錄；後續重測逾時，完整即時雙向交接尚未視為穩定可用。

這份展示保留架構與部分文件，**最完整的程式與操作說明請看[獨立公開 Repo](https://github.com/a275618631/codex-antigravity-collaboration)**，也可以直接閱讀[完整繁體中文技術說明](https://github.com/a275618631/codex-antigravity-collaboration/blob/main/README.zh-TW.md)。
