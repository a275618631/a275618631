# Che-Yu Wu

**製造系統整合｜AI 工作流程｜資料與權限治理**

我從製造現場的系統需求、介面整合與上線維運出發，延伸研究 AI 在文件處理、設備知識檢索與日常工作流程中的實際用法。

在工廠，系統能不能運作只是第一關。文件版本是否正確、資料能否追溯、誰有權修改、異常時如何回復，以及現場人員能否接手，往往更影響一個方案能不能長期使用。我把這些問題也帶進個人技術作品。

這裡有可直接查看的公開專案，也有從私人開發專案整理出的**部分公開程式碼與合成測試快照**。兩者會標明，不將設計或本機測試說成企業正式上線。

## 先看這幾個作品

### [製程文件改版審查與 Claude Skill](https://github.com/a275618631/manufacturing-document-workflow)

製造、品保、文管與資訊單位共用文件時，最麻煩的不是產生摘要，而是版本、責任與權限不清楚。

我用虛構工廠案例設計審查流程，製作兩版 Claude Skill，並在 Claude Free 實際操作合成情境。原版跨客戶案例能拒絕越權，但替代方案不夠完整；修正版單次重測補足了文件 Owner 授權、最小權限、再次檢查 ACL 與人工核准。模型與提示也有差異，因此不把結果歸因為 Skill 修改的單一效果。**這不是已連接 SharePoint 的系統。**

[看 Skill、測試與證據](https://github.com/a275618631/manufacturing-document-workflow/blob/main/docs/validation.md)

### [工廠設備知識庫與地端檢索](showcase/factory-knowledge-grounded-rag/)

設備手冊不只要能搜尋，答案還得對應正確的設備、版本與頁碼；查不到依據時，應清楚說明缺什麼，而不是補上一個看似合理的操作建議。

公開作品集提供部分 Python 程式碼、合成語料與測試快照，展示全文／向量檢索、來源引用及拒答機制。私人開發分支另有較新的本機 Web、文件匯入與回饋流程；**公開快照不等於最新完整產品，也未完成企業多使用者上線驗收**。

[看公開原始碼與版本邊界](showcase/factory-knowledge-grounded-rag/PROVENANCE.md)

### [AI 資料夾治理](https://github.com/a275618631/ai-folder-governance)

同一個專案的文件可能散落在本機、雲端和 Git。不能因為檔名像「最新版」，就自動刪除或覆寫其他文件。

這套公開 Skill／Prompt 規則要求先盤點、辨認來源、提出變更預覽，再由人員核准並驗證結果。它是**治理方法與可重用規則**，不是已部署的企業檔案管理平台。

### [企業營運平台：角色權限與工單流程](showcase/enterprise-operations-platform/)

用合成設備與工單資料，練習將需求轉成 API、角色權限、操作流程與測試。公開目錄包含部分 .NET 程式碼、測試及版本說明；私人專案仍是本機 MVP，不是企業產品驗收。

## 其他公開專案

- [Codex Agent Skills](https://github.com/a275618631/codex-agent-skills)：可重用的診斷、審查、交付與人工核准流程。
- [Codex × Antigravity Collaboration](https://github.com/a275618631/codex-antigravity-collaboration)：跨 Agent 執行環境協作的參考架構、本機 Bridge 與尚未排除的限制。
- [Portable AI Agent Environment](https://github.com/a275618631/portable-ai-agent-environment)：跨電腦移轉時的設定分類、敏感資料排除與本機驗證。
- [Workforce Scheduling System](https://github.com/a275618631/workforce-scheduling-system)：輪班規則、限制條件與例外狀態的系統設計案例；完整實作為私人版本。
- [html2slides](https://github.com/a275618631/html2slides)：將 HTML 簡報轉換成可編輯 PowerPoint／Google Slides 的工具。

[完整作品與公開證據索引](showcase/README.md)

## 我如何判斷方案是否做好

我習慣先確認實際使用者要解決什麼問題，再決定資料來源、權限、介面與驗證方式。除了正常流程，也會檢查來源不足、版本衝突、權限不足、外部服務中斷以及失敗後的回復方法。

公開文件會區分**已實作、已測試、私人環境驗證、設計中**；測試案例與數字只適用於其標明的範圍。工作中的製造系統與私人資料不放到公開倉庫。
