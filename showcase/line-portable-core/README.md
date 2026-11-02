# LINE Portable Core｜可移植的 Webhook 與 Mini App 核心

LINE Bot 收到訊息後，不能只做到「有回覆」。Webhook 可能重送、簽章必須正確驗證，Mini App 分享也需要區分成功、取消與失敗。

我用 TypeScript、Hono 和 LIFF 將 LINE 通訊流程拆成獨立的核心、Adapter 與 Webhook Gateway，讓業務功能不必和 LINE SDK 或特定資料庫緊密綁在一起。

## 核心功能

- **Webhook HMAC 驗證**：用原始請求內容與 HMAC-SHA256 驗證 LINE 簽章。
- **事件冪等**：以 `webhookEventId` 辨識重送，避免同一事件被重複處理；回覆失敗時保留重試機會。
- **LIFF 分享狀態**：明確區分成功、取消、不可用及錯誤，不把未回傳結果誤判成成功。
- **訊息與排程輔助**：Flex Message、Google Calendar URL 與 ICS 產生。
- **可移植架構**：核心邏輯、LINE 協議、Gateway 與儲存 Adapter 分離。

## 程式架構

```text
LINE Webhook／LIFF
       ↓
packages/line：簽章、事件與訊息格式
       ↓
packages/core：介面、配額與錯誤規則
       ↓
apps/gateway、apps/miniapp
       ↓
adapters：記憶體與其他業務系統介面
```

## 如何測試

這份展示保留 [package.json](package.json)、核心程式和合成測試，可在 Node.js 22 以上執行：

```bash
npm install
npm run check
npm run build:miniapp
```

既有自動化測試紀錄為 **16 項通過**，涵蓋簽章、重送、回覆與 LIFF 狀態等情境。手機端的四項人工 E2E 尚未完成，不能把離線測試當作正式 LINE 帳號上線驗收。

本專案不包含真實 LINE Channel Secret、Access Token 或私人使用者資料。
