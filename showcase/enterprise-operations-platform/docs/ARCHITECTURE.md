# 企業營運平台垂直切片架構設計 (Enterprise Operations Platform Architecture)

## 1. 系統概述

本專案為製造業現場設備與工單營運管理之垂直切片 (Vertical Slice)，以 ASP.NET Core 10 (.NET 10) 為基礎打造。專注於提供安全的角色存取控制 (RBAC)、設備與工單狀態流轉防護，以及確定性的異常攔截。

## 2. 核心技術棧

- **執行環境**：.NET 10 (ASP.NET Core Web API)
- **資料存取**：Entity Framework Core 10，搭配 PostgreSQL 與 In-Memory 資料庫 Fallback
- **身分鑑權**：JWT Bearer Token 驗證，搭配基於 Claim 的 RBAC Policy
- **測試框架**：xUnit、Microsoft.AspNetCore.Mvc.Testing

## 3. 領域模型與狀態機

### 3.1 角色職權劃分 (RBAC)

系統定義三種明確角色邊界：
- **Viewer (檢視者)**：僅具備唯讀權限，可查詢設備列表與工單狀態。嘗試建立或修改資源時，中介軟體立即攔截並回傳 `403 Forbidden`。
- **Operator (作業員)**：具備現場作業權限，可新增設備資料與開立工單 (`Open`)。
- **Supervisor (主管)**：具備審核與簽核權限，負責審查並將工單標記為完工 (`Completed`)。

### 3.2 設備與工單狀態生命週期

- **設備 (Equipment)**：
  - 欄位包含識別碼 (`Id`)、名稱 (`Name`)、作業區域 (`Area`) 與運作狀態 (`Status`：Normal, Attention, Critical)。
  - **防衝突機制**：新增設備時進行全域 ID 重複檢查，若存在衝突則精確回傳 `409 Conflict`。
- **工單 (WorkOrder)**：
  - 狀態流轉：`Open` (開立中) → `Completed` (已完工)。
  - 僅授權角色方可執行完工更新，保證產線維修責任鏈完整。

## 4. 安全與隔離邊界

- **零機敏配置**：開發環境提供隔離的 DemoAuth 機制，不需外部連線字串即可進行完整 API 與單元測試。
- **純中性合成資料**：展示代碼與測試用例均採用虛擬編號與合成名稱，排除任何真實商業資訊。
