# Che-Yu Wu｜技術作品集

**製造業系統整合 · AI Agent · 全端開發 · 自動化工具**

我喜歡把現場遇到的問題整理成可以操作、維護與測試的系統。工作重點包括製造業資訊整合、系統可靠度，以及讓 AI 工具在既有流程裡真正發揮作用。

這個 GitHub 收錄我的工程專案。每個作品都能看到我處理的問題、採用的技術、架構設計和實作結果。

## 精選作品

### [技術能力作品集｜六個工程專案](showcase/)

從工廠設備知識檢索、企業營運平台，到 Agent 工具政策與跨平台協作，整理成可以逐一閱讀的專案：

| 專案 | 可以看到什麼 |
| --- | --- |
| [製程文件改版審查流程](showcase/manufacturing-document-workflow/) | 文件版本、審核流程、Claude Skill 與實際測試 |
| [工廠設備知識庫與地端診斷助手](showcase/factory-knowledge-grounded-rag/) | Qdrant／FTS5 混合檢索、故障資訊引用、資料不足時的處理 |
| [企業營運平台](showcase/enterprise-operations-platform/) | ASP.NET Core、Vue、JWT 角色權限、設備與工單流程 |
| [Agent 工具策略引擎](showcase/agent-tool-policy-engine/) | 工具操作風險分類、權限範圍、核准與測試 |
| [Codex × Antigravity 協作架構](showcase/codex-antigravity-collaboration/) | 跨 AI 開發環境交接、任務契約、本地橋接 |
| [Codex Agent Skills 技能庫](showcase/codex-agent-skills/) | 可重複使用的工程 Skills 與格式驗證 |

**[進入完整作品集](showcase/)**

## 其他工程作品

### [Codex × Antigravity Collaboration](https://github.com/a275618631/codex-antigravity-collaboration)

研究兩套 AI 開發環境如何分工、交接任務並維持一致的修改範圍。採用 Task/Result 契約、本地 MCP Bridge、有限次外部委派與 Git worktree。可從[繁體中文架構說明](https://github.com/a275618631/codex-antigravity-collaboration/blob/main/README.zh-TW.md)或[架構網站](https://a275618631.github.io/codex-antigravity-collaboration/)開始閱讀。

### [Portable AI Agent Engineering Environment](https://github.com/a275618631/portable-ai-agent-environment)

處理 AI 開發環境跨電腦移轉時，設定檔、登入狀態與機器識別資訊混在一起的問題。公開內容包含可攜與本機專屬設定的分類、敏感資訊掃描方式及跨平台驗證案例。

### [Constraint-Based Workforce Scheduling System](https://github.com/a275618631/workforce-scheduling-system)

把輪班現場的資格、休息時間、覆蓋需求與人工指定班次整理成規則模型，實作排班、違規提醒、月曆檢視及匯出。原始實作累積 56 項自動化測試；公開版本使用合成案例介紹設計。

### [AI Folder Governance](https://github.com/a275618631/ai-folder-governance)

讓 Agent 先理解檔案內容、用途與版本關係，再決定怎麼整理。提供可直接使用的 Skill、提示範本與文件治理流程。

### [html2slides](https://github.com/a275618631/html2slides)

將 HTML 簡報轉成可編輯的 PowerPoint 或 Google Slides 物件，保留文字、圖形及圖片的獨立編輯能力，並提供轉換測試與報告。

## 其他實作記錄

- [登入式桌面媒體處理流程](projects/authenticated-desktop-media-workflow.md)：Tauri／Rust、macOS Keychain、yt-dlp 與 FFmpeg 整合，以及完整檔案交付流程。
- **會議資訊整理流程**：逐字稿、個資遮蔽、結構化摘要與來源驗證的實驗性工作流。

## 技術方向

我主要使用 Python、C#／.NET、TypeScript 與 GitHub 工具鏈，結合 REST API、資料庫、檢索系統、Skills 和 MCP。設計時優先沿用成熟工具，再針對真正需要控制的資料、權限與可靠度問題補上必要的程式。
