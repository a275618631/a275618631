# WORKFLOW.md｜協作與任務流轉規範

本文件定義 Chief、Research、Reviewer 與 Gemini 之間的協作標準作業流程（SOP）。

```mermaid
sequenceDiagram
    autonumber
    actor User as 使用者 (Board)
    participant Chief as Chief (CEO)
    participant Research as Research (資料查證)
    participant Reviewer as Reviewer (QA 驗收)
    
    User->>Chief: 提出業務需求 / 指派目標
    Chief->>Chief: 拆解需求為子任務 (Issues)
    Chief->>Research: 委派調查任務 (PAP-2)
    Research->>Research: 檢索公開資訊 / 執行查證
    Research-->>Chief: 提交研究報告與證據留痕
    Chief->>Reviewer: 發起成果驗收審核
    Reviewer->>Reviewer: 依據 Checklist 審查事實與格式
    alt 驗收未通過
        Reviewer-->>Chief: 駁回並列出具體缺失
        Chief->>Research: 補充修正指示
    else 驗收通過
        Reviewer-->>Chief: 判定 PASS 並簽核交付物
        Chief-->>User: 結案彙整回報 (PAP-1 關閉)
    end
```

## 階段說明
1. **需求拆解 (Decomposition)**：Chief 接收輸入後，建立主 Issue (`PAP-1`)，明確界定完成判準（Definition of Done）。
2. **研究查證 (Investigation)**：由 Research 依子 Issue (`PAP-2`) 進行針對性檢索，標註資料來源、日期與信心水準。
3. **品質審核 (Review & QA)**：Reviewer 檢視交付物是否具備可驗證事實、是否含未授權敏感資訊、結構是否符合規範。
4. **結案歸檔 (Completion)**：經 Reviewer 核可後，Chief 更新主 Issue 狀態為 Completed，留痕於系統活動日誌。
