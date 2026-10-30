# 企業營運平台垂直切片 (Enterprise Operations Platform Slice)

> **專案定位**：以 ASP.NET Core 10 (.NET 10) 打造的產線設備與工單管理垂直切片，展示企業級 RBAC 權限狀態機、工單冪等防重試與資料回滾驗證。  
> **核心技術**：.NET 10、ASP.NET Core Web API、Entity Framework Core、JWT Bearer、xUnit。  
> **驗證狀態**：22 項單元與整合測試全數通過 (1 Skip)，包含 401/403 攔截與資料回滾驗證。

---

## 1. 核心痛點與架構目標

在製造業產線管理系統中，常見兩大可靠性與資安痛點：
1. **工單重複提交與狀態錯亂**：現場網路瞬態波動時，作業員重複點擊容易造成重複派工或異常工單。
2. **權限越位與鑑權缺失**：一般開發容易將管理者權限與作業員權限混淆，缺乏嚴格的角色存取控制 (RBAC)。

### 本切片之設計方案
- **嚴格的 RBAC 狀態機**：針對「設備建立」、「工單指派」與「工單完工」實作不同層級的 JWT Policy，明確區隔 Operator (作業員)、Engineer (工程師) 與 Supervisor (主管) 職責。
- **工單冪等與資料防護**：工單建立與狀態轉移具備防重送檢查，並支援離線記憶體資料庫 fallback 模式。
- **安全的 Demo 驗證機制**：內建安全隔離之開發環境 DemoAuth，不需本機安裝資料庫或設定機敏連線字串，即可獨立重現與執行測試。

---

## 2. 模組架構

```
enterprise-operations-platform/
├── src/
│   ├── EnterpriseOperationsPlatform.Api/         # Web API 核心：Controllers、JWT 驗證、中介軟體
│   ├── EnterpriseOperationsPlatform.Core/        # 領域模型：設備、工單、RBAC 政策定義
│   └── EnterpriseOperationsPlatform.Infrastructure/ # 資料存取層：EF Core DbContext、Repository
├── tests/
│   ├── EnterpriseOperationsPlatform.Api.Tests/   # API 整合測試：401/403 攔截、DemoAuth 流程
│   └── EnterpriseOperationsPlatform.Core.Tests/  # 領域單元測試：狀態轉移、工單邏輯
├── appsettings.Development.json                  # 安全開發配置 (啟用 DemoAuth，排除機敏字串)
└── EnterpriseOperationsPlatform.slnx             # 方案檔 (.NET 10)
```

---

## 3. 本地重現與測試驗證

本切片具備 100% 可重現之自動化測試套件，完全不需要安裝外部資料庫：

```bash
# 執行全量測試 (22 項通過，1 項略過)
dotnet test EnterpriseOperationsPlatform.slnx
```

### 測試覆蓋重點
- **RBAC 權限攔截**：未認證請求精確回傳 `401 Unauthorized`；作業員嘗試完工主管工單精確回傳 `403 Forbidden`。
- **Demo 登入流程**：驗證開發模式下各虛擬角色 JWT Token 之簽發與有效期限。
- **工單生命週期**：驗證 Draft → InProgress → Completed 之狀態轉移合法性與資料一致性。

---

## 4. 安全與邊界說明
- 本公開展示切片採用合成設備與工單資料，不含真實產線設備型號或員工個資。
- 排除所有生產環境資料庫連線字串與 JWT 實體簽署密鑰。
