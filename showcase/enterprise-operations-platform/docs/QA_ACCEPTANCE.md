# 測試驗收與場景覆蓋摘要 (QA Acceptance Summary)

## 1. 驗收目標

驗證企業營運平台垂直切片在身分認證、RBAC 權限管控、工單狀態流轉與異常防護之確定性行為。

## 2. 測試執行結果

- **測試套件**：`EnterpriseOperationsPlatform.Api.Tests`
- **測試框架**：xUnit + WebApplicationFactory
- **執行結果**：**22 項通過，1 項略過 (Skip)**（略過項目為本機無 PostgreSQL 時自動 Skip 之資料庫啟動整合測試）
- **總執行耗時**：約 1.2 秒

## 3. 核心測試場景覆蓋

### 3.1 認證與授權 (Authentication & Authorization)
- **未帶 Token 請求**：存取受保護端點（如 `/api/operations/equipment`）精確回傳 `401 Unauthorized`。
- **無效/過期 Token**：未經簽署或格式損毀之 Bearer Token 拒絕存取，回傳 `401 Unauthorized`。
- **Viewer 角色越權攔截**：
  - Viewer 嘗試 POST 建立工單 -> 精確攔截並回傳 `403 Forbidden`。
  - Viewer 嘗試 POST 建立設備 -> 精確攔截並回傳 `403 Forbidden`。
- **Operator 角色授權驗證**：
  - 成功建立設備與建立關聯工單 (`201 Created`)。
  - 嘗試執行非授權之完工簽核時受到適當防護。
- **Supervisor 角色簽核驗證**：
  - 成功審核並將 Open 狀態工單轉移為 Completed。

### 3.2 資料一致性與防衝突 (Data Integrity & Conflict Handling)
- **設備 ID 重複檢查**：建立已存在 ID 之設備時，系統精確回傳 `409 Conflict`，避免產線設備識別碼覆寫。
- **記憶體儲存與持久化 Fallback**：在無實體資料庫連線下，`OperationsStore` 提供強型別記憶體安全儲存，確保測試環境 100% 可重現。
