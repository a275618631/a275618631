# 手機真機驗收指引 (Manual E2E Verification Checklist)

本文件說明如何以零洩漏、安全受控方式完成 LINE Bot 與 Mini App 的真機驗收。

---

## 1. 人機分工邊界
- **Agent 完成**：核心代碼開發、領域分層、16 項自動化單元測試、Local Smoke 驗證與 Mini App 靜態打包。
- **使用者完成**：LINE Developers Console 填寫 Endpoint、設定本機私密環境變數、真機操作驗收。

---

## 2. 真機驗收 4 項指標 (4 E2E Targets)

- [ ] **E2E-1 Mini App Open**：手機 LINE 內開啟 Mini App，LIFF 初始化成功，無 Endpoint 不符或網域白名單報錯。
- [ ] **E2E-2 shareTargetPicker**：點擊分享卡片，彈出 LINE 好友/群組選擇器，成功轉發 Demo Flex Message，接收端呈現完整卡片排版。
- [ ] **E2E-3 `/ping` Webhook Reply**：於 LINE 聊天室向測試官方帳號傳送 `/ping`，透過 HMAC 驗證並收到一次 `pong` 回覆（確認使用 Reply API，無重複發送）。
- [ ] **E2E-4 Calendar / ICS**：點擊加入行事曆按鈕，正確帶入 Google Calendar 標題、時間與地點；ICS 檔案可正常下載匯入。

---

## 3. 安全守則 (SECRET_BLACK_BOX)
1. 嚴禁將 `LINE_CHANNEL_SECRET` 與 `LINE_CHANNEL_ACCESS_TOKEN` 提交至 Git 倉庫、聊天室或公開日誌。
2. 僅於本機未納管之 `.env` 檔案中填寫變數。
3. 驗證完成後回報結果僅需列出各項 `PASS` 或 `FAIL` 及具體錯誤現象。
