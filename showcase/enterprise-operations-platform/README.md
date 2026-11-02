# 企業營運平台｜設備與維修工單的權限管理

一套工廠營運系統要能建立設備、處理工單，更要能正確限制不同角色的操作。重複設備編號、未登入請求、一般操作員誤用主管功能，都是需要在 API 層處理的問題。

我以合成設備與工單資料，實作 **ASP.NET Core 10、JWT 角色權限、資料模型與工單流程**，並用自動化測試確認正常和錯誤情境。

## 實作功能

- **設備資料與識別碼檢查**：避免重複建立設備，重複 ID 回傳 `409 Conflict`。
- **工單生命週期**：從建立到完成的受控狀態變化。
- **JWT／RBAC**：Viewer 只能閱讀；Operator 可新增；Supervisor 可完成工單。權限由後端端點判斷。
- **清楚的 HTTP 回應**：未登入 `401`、權限不足 `403`、資料衝突 `409`，讓介面能提供正確提示。
- **本地測試切片**：保留 API、部分資料存取與自動化測試，使用合成資料檢查操作行為。

## 從程式開始閱讀

- [ASP.NET Core API 入口](src/EnterpriseOperationsPlatform.Api/Program.cs)
- [方案檔](EnterpriseOperationsPlatform.slnx)
- [架構設計](docs/ARCHITECTURE.md)
- [測試驗收摘要](docs/QA_ACCEPTANCE.md)

## 測試與使用

公開切片的既有驗收紀錄為 **22 項測試通過、1 項略過**，包含角色權限、工單處理與資料衝突情境。已安裝 .NET 10 SDK 後，可在這個目錄執行：

```bash
dotnet test EnterpriseOperationsPlatform.slnx
```

此指令會依目前套件與環境安裝狀況決定測試結果；本次 README 修改沒有重新執行測試。

完整私人開發專案另有 Vue 介面、PostgreSQL 和進一步的工作流程。這份公開副本聚焦 API 與可公開測試，不包含私人環境連線設定，也不需要用真實員工或設備資料才能閱讀。
