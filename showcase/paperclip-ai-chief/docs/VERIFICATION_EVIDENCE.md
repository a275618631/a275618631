# 驗證證據留痕 (Verification Evidence Log)

本文件收錄 Paperclip AI Chief 於本機與雲端環境之真實驗證紀錄，作為工程落地之技術依據。

---

## 1. 核心服務啟動與 API 健康檢查
- **驗證環境**：Windows 11 WSL2 / Docker Engine 27.2.0 / Node.js 22
- **服務端口**：`http://127.0.0.1:3100` (綁定本機環回介面，安全模式: `local_trusted`)
- **API 響應 (`GET /api/health`)**：
  ```json
  {
    "status": "ok",
    "version": "2026.1023.0",
    "bootstrapStatus": "ready"
  }
  ```

---

## 2. 組織架構與 Agent 建立
- **角色團隊**：
  1. **Chief** (`role: ceo`)：全域統籌與指派
  2. **Research** (`role: researcher`)：資訊檢索與查證
  3. **Reviewer** (`role: qa`)：成果驗收與把關
  4. **Gemini** (`role: engineer`)：代碼轉化與算力支援
- **組織權限鎖定**：`requireBoardApprovalForNewAgents: true`（防範未授權自我增生）

---

## 3. 端到端任務閉環流程驗證
- **任務目標**：冷軋板形異常分析知識庫初稿
- **執行流程**：
  1. **指派階段**：由使用者 (Board) 發起需求，Chief 解析目標並指派至 Research。
  2. **研究階段**：Research 角色完成標準化技術報告並標註一手資料來源。
  3. **驗收與結案**：Reviewer 執行格式與內容檢核判定通過，Chief 簽核並回報完成結案。

---

## 4. Codex CLI 心跳運行紀錄 (Heartbeat)
- **狀態**：執行成功 (`succeeded`)
- **推論適配器**：`codex_local`
- **授權模式**：本機 ChatGPT Plus 官方登入會話
- **執行結果**：Chief 於 30 秒週期內成功喚醒、解析佇列中待辦事項並回寫狀態。

---

## 5. 雲端部署現狀與限制說明
- **雲端網路架構**：
  - Oracle Cloud (Tokyo `ap-tokyo-1`) VCN: `paperclip-vcn`（已建置完成）
  - 公開子網路：`public subnet-paperclip-vcn`（已配置完成）
- **容量現狀**：
  - 現象：OCI Tokyo AD-1 區域之 Ampere A1 (ARM64) 處於高峰期，暫無免費配額。
  - 處置策略：已設定每小時自動重試輪詢腳本排隊等待釋出；絕不自動升級為計費實例，堅守 NT$0 成本邊界。
