# 企業營運平台垂直切片 (Enterprise Operations Platform Slice)

> **專案定位**：以 ASP.NET Core 10 (.NET 10) 打造的產線設備與工單管理垂直切片，展示企業級 RBAC 角色狀態機、設備 ID 重複防衝突 (409 Conflict) 與安全鑑權防護。  
> **核心技術**：.NET 10、ASP.NET Core Web API、Entity Framework Core、JWT Bearer、xUnit。  
> **驗證狀態**：22 項單元與整合測試全數通過 (1 Skip)，涵蓋 401/403 攔截與記憶體儲存驗證。

---

## 1. 核心痛點與架構目標

在製造業現場營運系統中，常見兩大可靠性與資安痛點：
1. **設備與工單資料衝突**：產線設備編號若重複建立或覆寫，會造成後續維修履歷斷裂與工單對應錯亂。
2. **權限越位與鑑權缺失**：一般後端若缺乏細粒度角色存取控制 (RBAC)，易使現場作業員或訪客誤觸主管簽核端點。

### 本切片之設計方案
- **嚴格的 RBAC 角色狀態機**：針對端點實作 JWT Claim-based 鑑權，明確劃分 **Viewer (檢視者)**、**Operator (作業員)** 與 **Supervisor (主管)** 三大角色職權。
- **資料防衝突機制**：新增設備時進行全域識別碼查重，若存在重複則精確回傳 `409 Conflict`。
- **工單生命週期管理**：實作 `Open` (開立中) 至 `Completed` (已完工) 之受控狀態流轉，未授權者無法變更工單狀態。
- **安全隔離之測試架構**：內建開發用 DemoAuth 與記憶體 Fallback 機制，不需安裝外部資料庫即可 100% 獨立重現測試。

---

## 2. 模組架構

```
enterprise-operations-platform/
├── src/
│   └── EnterpriseOperationsPlatform.Api/         # Web API 核心：Controllers、JWT 驗證、OperationsStore、EF Core
├── tests/
│   └── EnterpriseOperationsPlatform.Api.Tests/   # 整合與單元測試：RBAC 攔截、OperationsStore 驗證
├── docs/
│   ├── ARCHITECTURE.md                           # 系統架構與領域模型設計
│   └── QA_ACCEPTANCE.md                          # 測試驗收與場景覆蓋摘要
├── appsettings.Development.json                  # 安全開發配置 (啟用 DemoAuth，排除機敏字串)
└── EnterpriseOperationsPlatform.slnx             # 方案檔 (.NET 10)
```

---

## 3. 本地重現與測試驗證

本切片具備 100% 可重現之自動化測試套件，完全不需要外部資料庫：

```bash
# 執行全量測試 (22 項通過，1 項略過)
dotnet test EnterpriseOperationsPlatform.slnx
```

### 測試覆蓋重點
- **RBAC 權限攔截**：未認證請求回傳 `401 Unauthorized`；Viewer 嘗試建立設備或工單精確回傳 `403 Forbidden`。
- **工單狀態流轉**：驗證 `Open` → `Completed` 之合法狀態移轉與非授權操作攔截。
- **設備防衝突檢查**：驗證重複設備 ID 時正確回傳 `409 Conflict`。

詳細架構設計請參閱 [架構設計文件](docs/ARCHITECTURE.md)，完整驗收項目請參閱 [測試驗收摘要](docs/QA_ACCEPTANCE.md)。

---

## 4. 安全與邊界說明
- 本公開展示切片採用合成設備與工單資料，不含真實產線設備型號或員工個資。
- 排除所有生產環境資料庫連線字串與 JWT 實體簽署密鑰。
