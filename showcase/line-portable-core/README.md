# LINE Portable Core｜可移植 LINE Webhook & Mini App 核心

> **專案定位**：解耦、輕量且可移植的 LINE Bot & LIFF Mini App 核心架構；具備嚴格的通訊協議驗證、冪等防重放與領域分層。  
> **關鍵技術**：TypeScript、Hono、Vite、LIFF (@line/liff)、HMAC-SHA256 簽名驗證、Vitest。  
> **狀態**：16 項單元測試全數通過；手機真機 E2E 處於 0/4 待驗證狀態（待真機連線配置）。

---

## 1. 核心痛點與設計理念

在開發 LINE 企業服務或社群互動應用時，常見以下架構挑戰：
1. **強綁定特定平台或龐大框架**：許多開源範例綁定特定後端雲服務或老舊 SDK，缺乏架構分層，難以移植到微服務或邊緣運算環境。
2. **Webhook 重放與重複扣款/回覆風險**：網路瞬態波動時，LINE 伺服器會重送 Webhook 事件；若未實作基於 `webhookEventId` 的嚴格冪等機制，容易造成重複處理。
3. **缺少離線單元測試與協議校驗**：多數 LINE Bot 開發仰賴推送到雲端後用手機手動測試，缺乏本地脫機的簽名驗證與 Flex 結構自動化測試。

### 本架構之解法 (Hexagonal Architecture)
- **埠與適配器架構 (Ports & Adapters)**：核心領域邏輯 (`packages/core`) 完全獨立，不依賴任何外部資料庫或 HTTP 框架；透過介面與 `adapters/` 對接。
- **嚴謹的通訊安全防護**：
  - **HMAC-SHA256 簽名驗證**：精確比對 `x-line-signature`，阻絕未授權的偽造請求。
  - **Webhook 冪等性防護**：以 `webhookEventId` 為鍵，確保僅在回覆成功後標記已處理；若發送中斷則允許重傳重試。
- **嚴格的 Mini App 狀態判斷**：針對 `@line/liff` 的 `shareTargetPicker()` 進行嚴格校驗，只有明確回傳 `{ status: "success" }` 才判定分享成功，修正將 `undefined` 誤判為成功的常見陷阱。

---

## 2. 模組架構與目錄職責

```
line-portable-core/
├── packages/
│   ├── core/           # 核心領域：Ports 介面定義、配額策略 (Quota Policy)、領域錯誤
│   ├── line/           # LINE 專用協議：HMAC 簽名驗證、Webhook 冪等、Messaging API、Flex 校驗
│   └── calendar/       # 整合輔助：Google Calendar URL 產製與 ICS 檔案轉換
├── adapters/
│   ├── memory/         # 本地記憶體適配器 (Bounded MemoryStore，供離線測試與原型驗證)
│   ├── benefit-contract/     # 企業福利領域合約介面
│   └── production-contract/  # 生產排程領域合約介面
├── apps/
│   ├── gateway/        # 輕量 Webhook 路由伺服器 (Hono / Node.js 22+)
│   └── miniapp/        # LIFF Mini App 前端介面 (Vite + Vanilla TypeScript)
└── tests/              # 自動化單元測試與測試 Fixtures (16 Tests PASS)
```

---

## 3. 自動化驗證與測試留痕

本專案具備完整的本地脫機測試套件，使用 Vitest 驅動：

```bash
npm install
npm test
```

### 單元測試結果 (全數 16 項 PASS)
```text
 ✓ tests/unit/core.test.ts (4 tests)
   - 驗證配額扣減與超額攔截 (QuotaPolicy)
   - 驗證領域錯誤封裝與邊界條件
 ✓ tests/unit/miniapp.test.ts (2 tests)
   - 驗證 LIFF 初始化防禦
   - 驗證多語系環境相容
 ✓ tests/unit/share.test.ts (4 tests)
   - 驗證 shareTargetPicker 成功狀態判斷 ({ status: "success" })
   - 驗證使用者取消 (cancel)、功能不可用與例外的容錯處理
 ✓ tests/unit/flex-calendar.test.ts (2 tests)
   - 驗證 Flex Message 結構與樣式合法性校驗
   - 驗證 ICS 行事曆時間戳記解析
 ✓ tests/unit/line.test.ts (4 tests)
   - 驗證合法 HMAC-SHA256 簽名驗證通過
   - 驗證非法簽名即時拒絕 (HTTP 401 Unauthorized)
   - 驗證 webhookEventId 冪等性去重防止重覆處理
   - 驗證 Reply 失敗時的重送容許機制

Test Files  5 passed (5)
     Tests  16 passed (16)
```

---

## 4. 誠實工程邊界與限制

1. **手機實機 E2E 狀態 (0/4 待真機連線)**：
   - 包含四項需要連線 LINE 官方 Console 與真機環境之驗證：
     1. Mini App 打開與 LIFF 身分讀取
     2. `shareTargetPicker` 手機好友選取轉發
     3. `/ping` 訊息自動 Webhook 回覆
     4. 行事曆加入與 ICS 匯入
   - 目前維持在 `FINAL_STATE: READY_FOR_USER_ACTION`，誠實標明 **0/4 未於真機連線**，絕不將未驗證之項目宣稱為通過。
2. **儲存層限制**：
   - 本展示版本使用內建 `MemoryStore`，僅適用於離線驗證與單元測試；正式高並發環境需掛載 Redis / Postgres 實作分散式冪等鎖。
3. **資安規範 (SECRET_BLACK_BOX)**：
   - 本倉庫絕不提交任何真實 `LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN` 或真實使用者 ID。
