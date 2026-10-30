# 技術作品與驗證索引

這裡集中整理我在文件流程、工廠知識檢索、系統權限和 AI Agent 協作上的作品。部分是完整公開專案，部分則是從私人開發倉庫整理出的**去識別程式碼與合成資料快照**。

我希望每個案例都能回答三個問題：**遇到什麼實際困難？做了哪些取捨？目前有什麼證據，還有哪些事沒有驗證？**

## 優先閱讀的案例

| 案例 | 解決的問題 | 目前有什麼可以檢查 |
| --- | --- | --- |
| [製程文件改版審查與 Claude Skill](manufacturing-document-workflow/) | 文件改版時，如何先確認來源與權限，再比對、審核與發布 | **完整公開來源**：兩版 Skill、合成案例、Claude Free 單次測試與回覆紀錄；未連接企業 SharePoint |
| [工廠設備知識庫與地端 RAG](factory-knowledge-grounded-rag/) | 設備手冊散落、代碼難查，答案需要明確來源與適用版本 | **公開部分 Python 快照**：檢索、引用、安全拒答與合成測試；較新的私人 Web 流程未完整同步 |
| [企業營運平台垂直切片](enterprise-operations-platform/) | 不同角色操作設備與工單時，如何限制權限並處理錯誤 | **公開部分 .NET／測試快照**：角色限制、API／資料模型；私人版本仍是本機 MVP |
| [Agent 工具策略引擎](agent-tool-policy-engine/) | 自動化工具在讀寫檔案前，如何判斷副作用與核准需求 | **公開部分 Python 快照**：規則評估和合成測試；屬 staging preflight，不是正式安全 Gateway |

## 其他公開工程作品

- [Codex Agent Skills](codex-agent-skills/)：將重複的分析、交付與驗證步驟寫成可重用的 Skill。
- [Codex × Antigravity 協作架構](codex-antigravity-collaboration/)：本機 Bridge、有限委派與人工核准；最近一次跨執行環境重測仍有逾時限制。

另外還有獨立公開倉庫：[AI 資料夾治理](https://github.com/a275618631/ai-folder-governance)、[跨電腦 AI Agent 環境](https://github.com/a275618631/portable-ai-agent-environment)、[輪班規則系統案例](https://github.com/a275618631/workforce-scheduling-system) 及 [html2slides](https://github.com/a275618631/html2slides)。

## 用一個文件改版問題理解這些作品

假設現場人員收到某設備的新版本操作文件：

1. **先確認權限與責任**：文件由誰提供、適用哪些人、是否可以放入共用知識庫？這是 [Claude Skill 案例](manufacturing-document-workflow/) 要處理的事。
2. **再確認可查詢的證據**：完成品質檢查和索引後，查詢應回到正確手冊、版次與頁碼；找不到依據就說明缺口。參考 [RAG 案例](factory-knowledge-grounded-rag/)。
3. **需要實際改動系統時**：工具動作必須受可驗證的權限與人工核准限制。參考 [工具策略](agent-tool-policy-engine/) 和 [營運平台](enterprise-operations-platform/)。

**以上是用來說明設計取捨的合成情境，不是已完成的跨 Repository 端到端整合。** Claude Skill 不會自動取得 SharePoint ACL 權限，RAG 不會寫入現場 PLC，工具策略引擎也不是生產環境的強制執行層。

## 實作、測試與公開範圍

- **已實作**：可在對應公開原始碼或 Skill 中查看的功能；實際可執行範圍仍依各專案說明。
- **已驗證**：有對應測試案例或紀錄。合成測試、本機 API 測試、模型回答觀察與真人使用者驗收是不同層級，不能互相替代。
- **私人版本**：主 Repository 可能設為 Private，但此 `showcase/` 已包含經挑選的部分原始碼。公開快照的同步日期與來源 Commit 列於各專案的 `PROVENANCE.md`。
- **尚未驗證**：不宣稱真實企業 SharePoint 租戶 ACL、生產 OT 控制、跨租戶部署、規模化正式上線或各專案間完整串接。

測試狀態可能隨來源分支推進而改變。請以各公開快照的版本說明為準；如有更新，應重新檢查可重現性與公開安全範圍。
