# Che-Yu Wu｜製造系統整合與 AI 工程作品集

**製造業系統整合｜C#／.NET｜Python｜AI 工程與自動化**

做製造系統時，我最在意的是資料能不能追溯、權限是否清楚，以及異常發生後能不能找到原因並恢復運作。這些考量也延伸到我整理的個人工程作品。

這裡收錄企業系統、設備文件檢索和 AI 工具治理等專案。每個作品都說明要處理的問題、採用的做法，以及目前開放的程式或驗證內容。

## 精選作品

| 專案 | 想解決的問題 |
| --- | --- |
| [工廠設備知識庫與地端診斷助手](showcase/factory-knowledge-grounded-rag/) | 從設備文件找到可追溯的警報資訊；版本或證據不足時，不勉強提供操作建議 |
| [企業營運平台](showcase/enterprise-operations-platform/) | 以設備與維修工單為例，實作 API、角色權限、狀態檢查與錯誤處理 |
| [製程文件改版審查流程](showcase/manufacturing-document-workflow/) | 把文件版本、存取權限與人工核准放進可追查的審查流程 |
| [Agent 工具策略引擎](showcase/agent-tool-policy-engine/) | 在 AI Agent 使用工具前，依操作範圍與風險決定是否放行 |

**[查看完整工程作品集](showcase/)**

## AI 開發與協作工具

- [Codex × Antigravity 協作架構](https://github.com/a275618631/codex-antigravity-collaboration)：研究兩套開發工具如何交接任務、共用結果格式並管理 Git 修改。
- [Codex Agent Skills](https://github.com/a275618631/codex-agent-skills)：整理可重用的排錯、審查與交付方法，減少跨專案重複設定。
- [可攜式 AI Agent 開發環境](https://github.com/a275618631/portable-ai-agent-environment)：區分能跨電腦同步的設定，與必須留在本機的登入、憑證及執行狀態。

## 其他工程作品

- [LINE Portable Core](showcase/line-portable-core/)：Webhook 驗證、重複事件處理及 LIFF 前端整合。
- [Paperclip AI Chief](showcase/paperclip-ai-chief/)：多 Agent 任務分工與結果回報的工程探索。
- [規則式人力排班系統](https://github.com/a275618631/workforce-scheduling-system)：以排班資格、休息間隔與人力需求建立可檢查的規則。
- [html2slides](https://github.com/a275618631/html2slides)：將 HTML 版面轉成可編輯的 PowerPoint 元件。
- [AI Folder Governance](https://github.com/a275618631/ai-folder-governance)：根據來源、用途與版本關係整理檔案。
- [登入式桌面媒體處理流程](projects/authenticated-desktop-media-workflow.md)：桌面工具與本機媒體處理流程的整合。

## 關於作品範圍

這些作品是個人公開工程練習與研究，使用合成資料或可公開的程式片段，不代表任職公司的正式系統或部署成果。部分作品已有可執行程式與測試，部分以流程設計或原型為主；各專案頁面會分別說明。