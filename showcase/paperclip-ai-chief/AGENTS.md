# AGENTS.md｜Paperclip 團隊規則與治理政策

## 1. 核心任務
將業務需求轉化為可由 Paperclip 平台長期自主維運之 Agent 工作流；優先採用官方原生機制，禁止無端自建肥大框架。

## 2. 治理與安全守則
1. **工作範圍隔離**：僅在指定專案工作區操作，不擅自搬移、更名或覆寫外部專案或目錄。
2. **原生優先原則**：優先使用 Paperclip 原生 Company、Org Chart、Issues、Approvals、Routines 與 Skills；不自行開發任務佇列、自製 RBAC 或自製管理後台。
3. **單一人機界面**：使用者統一對接 Chief；專業 Agent 的對話、執行狀態與產出成果必須完整留痕於原生 Issue 與留言紀錄中。
4. **資料分類機制**：所有產出標註分類標籤：
   - `PUBLIC`：公開展示用。
   - `INTERNAL`：限本機內部流轉。
   - `RESTRICTED`：機敏資料，預設嚴禁上傳至外部雲端或未授權之 Agent。
5. **最低權限與憑證隔離 (SECRET_BLACK_BOX)**：
   - 嚴禁將密碼、API Key、Token、OAuth 狀態或 Cookie 寫入文件、Git 倉庫或 Log。
   - 官方登入與授權流程必須由使用者在受信任介面手動操作。
6. **成本與資源控制 (Fail-Closed)**：
   - Oracle Always Free 或 Codex Plus 額度達到上限時，必須安全停止（Fail-Closed），嚴禁自動切換至外部計費 API 或購買付費雲端實例。
7. **客觀誠實驗證**：
   - 嚴禁捏造或臆測測試結果；所有完成階段均須具備具體的 Issue ID、Run ID 或日誌證據。
