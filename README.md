# Che-Yu Wu｜製造業系統整合與 AI 工程作品集

**製造業資訊整合 · Python／C# .NET · AI Agent · RAG · 自動化**

我從製造現場的系統整合工作出發，習慣先釐清資料怎麼流動、哪些人需要操作系統，以及異常發生時如何繼續運作，再把需求做成可以測試、維護和交付的程式。

這裡收錄我在工廠設備知識檢索、企業營運系統、AI Agent 協作與工作流程自動化方面的作品。除了架構說明，也能找到實際的程式碼、合成案例或測試結果。

## 通用作品集入口

可用統一入口瀏覽作品、功能範圍、版本證據、程式與 Demo：[作品集入口程式與使用說明](portfolio/README.md)。入口本機執行，不會啟動或代理各作品；各專案維持自己的 repo、啟動方式與開發節奏。

需要 Python 3.12 以上。在此 repo 根目錄執行：

```powershell
python portfolio/hub.py serve --mode local --port 8765 --open
```

Windows 也可執行 `powershell -NoProfile -File .\portfolio\start.ps1`。本機入口預設只綁定 `127.0.0.1`。

## 精選工程作品

| 專案 | 實際解決的問題與實作重點 |
| --- | --- |
| [工廠設備知識庫與地端診斷助手](showcase/factory-knowledge-grounded-rag/) | 用混合檢索找到設備警報與手冊段落，檢查引用與版本，遇到證據不足時停止推測 |
| [企業營運平台](showcase/enterprise-operations-platform/) | 以 ASP.NET Core、JWT 權限和設備／工單流程，處理角色操作、錯誤狀態與資料衝突 |
| [製程文件改版審查流程](showcase/manufacturing-document-workflow/) | 將文件版本、存取範圍、審核責任與 Claude Skill 組成可檢查的流程 |
| [Agent 工具策略引擎](showcase/agent-tool-policy-engine/) | 用 Python 規則判斷工具操作是允許、限縮範圍、需要核准或應該拒絕 |
| [LINE Portable Core](showcase/line-portable-core/) | 以 TypeScript 實作 Webhook HMAC 驗證、事件冪等、LIFF Mini App 與訊息處理 |
| [Paperclip AI Chief](showcase/paperclip-ai-chief/) | 組合 Paperclip 與 Codex，讓 Chief、Research、Reviewer 分工、回報並完成本機任務閉環 |

**[進入完整技術作品集](showcase/)**

## AI Agent 開發工具與工程方法

### [Codex × Antigravity 協作架構](https://github.com/a275618631/codex-antigravity-collaboration)

研究兩套 AI 開發環境如何清楚分工、共享 Task／Result 格式、透過本地 MCP Bridge 交換資訊，並用 Git 工作區管理修改。專案包含實際橋接測試、受限的跨 Runtime 測試及可追蹤的功能狀態。

### [Codex Agent Skills](https://github.com/a275618631/codex-agent-skills)

將問題排查、流程自動化、PR 審查與交付整理成五個可攜式 Skills，讓不同專案不必每次重寫同一套工作方法。

### [可攜式 AI Agent 開發環境](https://github.com/a275618631/portable-ai-agent-environment)

處理跨電腦使用 Agent 工具時，哪些設定能共用、哪些憑證與登入狀態必須留在原電腦。公開作品包含設定分類、Git 暫存內容掃描與合成回歸測試。

## 其他工程作品

- [規則式人力排班系統](https://github.com/a275618631/workforce-scheduling-system)：將輪班資格、休息時間、人工指定及人力需求轉成可檢查的規則模型。
- [html2slides](https://github.com/a275618631/html2slides)：利用 Chromium 解析 HTML 排版，輸出文字、形狀、圖片可編輯的 PowerPoint。
- [AI Folder Governance](https://github.com/a275618631/ai-folder-governance)：先理解檔案的來源、用途與版本關係，再決定如何整理。
- [登入式桌面媒體處理流程](projects/authenticated-desktop-media-workflow.md)：Tauri、Rust、macOS Keychain、yt-dlp 與 FFmpeg 的桌面工作流整合。

## 我在意的工程問題

做系統時，我特別在意**可追溯的資料來源、合理的操作權限、異常情境與復原能力**。遇到 AI 工具，我也會先看能不能沿用現有平台，再針對確實需要控制的部分寫程式。

作品中部分是獨立公開專案，部分是從私人開發版本整理出的可公開程式與合成測試。每個頁面會標明可查看的內容和測試範圍，方便從實作本身判斷能力。
