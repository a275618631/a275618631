# 技術作品集｜製造業 AI、企業系統與 Agent 工程

> [通用作品集入口](../portfolio/README.md)可從同一首頁依分類瀏覽作品與功能；來源 repo 仍各自開發，本入口不啟動來源服務。

從設備手冊查詢、工單操作，到 Agent 工具使用與跨平台協作，我把幾種實際工程問題整理成可以閱讀程式、追查設計和查看測試的專案。

這個目錄收錄可公開的程式碼與合成案例。四個主要專案展示製造業與 AI 整合，其他作品則補上 LINE 通訊、Agent 團隊協作和可重用的工程工具。

## 四個主要作品

### [工廠設備知識庫與地端診斷助手](factory-knowledge-grounded-rag/)

維修人員查詢設備警報或規格時，系統不只要找到相似文字，還要對應正確的設備、版本與來源。我使用 SQLite FTS5、Qdrant Local、檢索融合與重排序，再由確定性驗證檢查引用、數值及證據不足的情況。

**看點：** Python、Hybrid Retrieval、引用追蹤、ABSTAIN 與合成設備診斷測試。

### [製程文件改版審查流程](manufacturing-document-workflow/)

新版作業文件會影響製造、品保、文管及資訊單位。我將版本差異、文件 Owner、權限檢查與人工審核整理成 Claude Skill，並比較一般改版、跨客戶資料及資訊不足時的實際模型回覆。

**看點：** 工作流、版本治理、Claude Skill 與實測案例。

### [企業營運平台](enterprise-operations-platform/)

用設備與維修工單管理情境，實作 ASP.NET Core 10、JWT 角色權限、資料模型與狀態驗證。除了正常操作，也測試未登入、權限不足、資料重複和工單流程。

**看點：** C#／.NET、REST API、RBAC、工單狀態與自動化測試。

### [Agent 工具策略引擎](agent-tool-policy-engine/)

AI Agent 要讀寫檔案或執行工具時，先由程式規則判斷路徑、分支、動作類型和風險，再回傳允許、限縮範圍、需要核准或拒絕。

**看點：** Python、TOML 策略、決定論決策與跨平台測試。

## 其他值得看的專案

| 專案 | 主要內容 |
| --- | --- |
| [LINE Portable Core](line-portable-core/) | HMAC Webhook 驗證、事件冪等、LIFF 分享與 Calendar 介接 |
| [Paperclip AI Chief](paperclip-ai-chief/) | Chief／Research／Reviewer 本地任務閉環、Codex Heartbeat 與 Oracle 部署規劃 |
| [Codex × Antigravity](codex-antigravity-collaboration/) | Task／Result 契約、本地 MCP Bridge、跨 Agent 分工與 Git 協作 |
| [Codex Agent Skills](codex-agent-skills/) | 五個可重用工程 Skills、規格與格式驗證 |

更多獨立公開作品：[可攜式 AI Agent 開發環境](https://github.com/a275618631/portable-ai-agent-environment)、[排班系統設計](https://github.com/a275618631/workforce-scheduling-system)、[AI 資料夾治理](https://github.com/a275618631/ai-folder-governance)、[html2slides](https://github.com/a275618631/html2slides)。

## 這些能力如何搭配

以新版設備維修文件為例：先確認文件權限、版本與審核責任，再讓 RAG 在有來源的文件中查找相關設備資訊；如果需要建立工單，工具策略引擎先評估操作，營運平台再處理角色權限與資料寫入。

這是一個**跨專案應用情境示例**，用來說明各項設計如何互補，而不是已經部署的單一整合系統。

## 閱讀與操作

每個專案都有自己的 README、程式或設計文件。可以先從上方的情境進入，再查看架構、測試與操作指令。部分展示使用從私人原始專案整理出的合成資料副本；其版本與可重現範圍以該專案文件為準。
