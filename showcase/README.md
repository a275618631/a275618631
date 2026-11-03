# 工程作品集｜製造系統、AI 與工作流程

這裡整理四個與製造現場、企業系統及 AI 工具相關的公開作品。閱讀方式很簡單：先了解**遇到什麼問題**，再看**如何設計與驗證**；想深入時，才往下查看原始碼。

## 精選作品

### [工廠設備知識庫與地端診斷助手](factory-knowledge-grounded-rag/)

設備發出警報時，找到相似的手冊文字還不夠，必須核對設備型號、文件版本及引用來源。這個作品將精確搜尋與語意檢索結合，並檢查證據是否足以支持回答。

**主要內容：** Python、混合檢索、來源驗證、證據不足時停止回答。

### [企業營運平台](enterprise-operations-platform/)

以設備和維修工單為例，展示後端系統如何管理角色權限、工單狀態及錯誤回應。重點不是畫面，而是同一個 API 在不同身分與操作條件下，是否仍能維持一致規則。

**主要內容：** C#／ASP.NET Core、REST API、JWT 權限、自動化測試。

### [製程文件改版審查流程](manufacturing-document-workflow/)

文件改版涉及來源、版本、存取範圍與人工審核。這個案例整理出一套受控的工作流程，並觀察 AI Skill 在正常改版、跨權限請求及資訊不足時的回應。

**主要內容：** 文件治理、Claude Skill、人工核准、合成情境驗證。

### [Agent 工具策略引擎](agent-tool-policy-engine/)

AI Agent 能讀寫檔案與呼叫工具，但執行前仍需要清楚的規則。這個 Python 原型根據操作類型、路徑與風險，決定允許、限縮、等待核准或拒絕。

**主要內容：** Python、TOML 規則、操作前檢查、測試案例。

## 其他作品

| 專案 | 內容 |
| --- | --- |
| [LINE Portable Core](line-portable-core/) | Webhook 驗證、重複事件處理及 LIFF 整合 |
| [Paperclip AI Chief](paperclip-ai-chief/) | 多 Agent 分工與任務回報 |
| [Codex × Antigravity](codex-antigravity-collaboration/) | 開發工具之間的任務交接與 Git 協作 |
| [Codex Agent Skills](codex-agent-skills/) | 可重用的工程流程與指令 |

更多公開專案：[可攜式 AI Agent 開發環境](https://github.com/a275618631/portable-ai-agent-environment)、[規則式排班系統](https://github.com/a275618631/workforce-scheduling-system)、[AI 資料夾治理](https://github.com/a275618631/ai-folder-governance)、[html2slides](https://github.com/a275618631/html2slides)。

## 展示範圍

所有製造情境使用合成資料或可公開的工程片段，不包含任職公司的內部資料。各專案有不同的完成程度：**可執行原型、程式切片、流程設計**並不等於已上線的企業產品。程式、測試及限制會在各專案頁面分別註明。