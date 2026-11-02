---
name: chief-task-handoff
description: When Chief delegates work, or a specialist hands results to another Agent, use this reusable governance and evidence checklist. Does not perform external actions.
---

# Chief 任務交接 Skill（純 Markdown，可重用治理規則）

## 1. 觸發時機
- Chief 將分解後的子任務指派給專業 Agent 時。
- 專業 Agent（如 Research）完成工作，準備將成果移交 Reviewer 驗收時。
- 向 Chief 回報任務進度、提請結案或申請新資源時。

## 2. 交接檢查清單 (Handoff Checklist)
1. **識別與上下文**：確認原任務之 `task_id`、指派負責人、輸入來源與明確的驗收準則（DoD）。
2. **留痕透明化**：所有交接與成果回報必須透過 Paperclip 任務留言進行，嚴禁使用未留痕的隱密通道。
3. **資料等級標註**：
   - `PUBLIC`：可對外展示之脫敏資料。
   - `INTERNAL`：限本機內部測試與流轉之資料。
   - `RESTRICTED`：嚴禁進入外部模型或未經授權工作區之機敏資產。
4. **回報格式契約**：
   - `task_id`: 任務唯一識別碼
   - `status`: 當前狀態 (`completed` / `in_review` / `blocked`)
   - `evidence`: 具體驗證依據（測試結果、輸出檔案、日誌記錄）
   - `blockers`: 若有阻擋，列出具體技術根因與解除建議
5. **新 Agent 提案守則**：
   - 優先重用既有 Agent 角色與現成技能庫。
   - 僅在業務存在長期、專業化重複需求時，才由 Chief 走原生 `hire_agent` 申請流程，經人工核准後方可建立。
