# Provenance & Verification Boundary｜LINE Portable Core

- **專案代號**：`line-portable-core`
- **公開展示來源**：[Profile showcase snapshot](https://github.com/a275618631/a275618631/tree/308063538eaec8df533416b3972039551f04677d/showcase/line-portable-core)
- **展示 Commit SHA**：`308063538eaec8df533416b3972039551f04677d`
- **同步方式**：公開作品集中的 commit-pinned TypeScript／測試切片
- **展示範圍**：Webhook 簽章驗證、事件冪等、回覆失敗重試、LIFF 分享狀態與訊息／排程輔助

---

## 驗證證據狀態 (Evidence Status)

- **離線單元／整合測試**：**HISTORICAL**（公開 README 記錄 16 項通過，涵蓋簽章、重送、回覆與 LIFF 狀態；本入口不把歷史結果升格為本輪驗收）。
- **手機端人工 E2E**：**UNVERIFIED**（四項人工 E2E 尚未完成；不宣稱已連接正式帳號或正式上線）。

---

## 安全邊界宣告 (Mandatory Boundaries)

1. 展示不包含真實 Channel Secret、Access Token 或私人使用者資料。
2. 公開切片僅提供可重現的核心程式與合成測試；來源服務需依專案自己的 README 個別啟動。
3. 作品集入口只連結到固定展示，不自動啟動來源服務、不代理來源 API，也不共用來源的資料庫或憑證。
