# 企業營運平台｜設備與維修工單管理

企業系統除了能建立資料，也必須回答幾個日常問題：**誰有權修改、工單能否進入下一個狀態，以及資料衝突時應如何回應？**

這個作品以設備和維修工單為例，展示後端 API 如何處理這些規則。

## 主要設計

- **設備資料檢查**：同一筆設備識別碼不能重複建立，衝突會回傳明確結果。
- **工單狀態管理**：建立、處理與完成遵循既定的狀態變化。
- **依角色授權**：Viewer 可閱讀、Operator 可新增、Supervisor 可執行完成操作；由後端檢查權限。
- **一致的錯誤回應**：未登入、權限不足和資料衝突使用不同的 HTTP 狀態，方便前端辨識。

## 架構與程式

公開版本採用 **C#／ASP.NET Core 10**，示範 REST API、JWT 驗證與角色權限檢查。測試涵蓋一般操作及不允許的情境。

可從 [API 入口](src/EnterpriseOperationsPlatform.Api/Program.cs)、[架構設計](docs/ARCHITECTURE.md) 與 [測試說明](docs/QA_ACCEPTANCE.md) 閱讀；使用 .NET 10 SDK 可執行：

```bash
dotnet test EnterpriseOperationsPlatform.slnx
```

## 作品範圍

這是**可公開的後端工程切片**，使用合成設備與維修資料。完整私人開發版本另有 Vue 畫面、PostgreSQL 和更多流程；上述內容並不包含在本公開切片中。README 所述測試依既有紀錄整理，未代表所有環境都已重新驗證。