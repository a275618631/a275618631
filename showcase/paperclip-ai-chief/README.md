# Paperclip AI Chief｜用現成工具組成可分工的 AI 團隊

單一 AI Agent 很容易變成「所有事情都自己做」。我想解決的是：有一個固定入口接收需求，能分派研究與審查工作，並讓人隨時看見進度、結果與需要核准的事項。

我選擇組合 **Paperclip、Codex CLI 與既有任務流程**，建立 Chief、Research、Reviewer 的分工，再規劃把執行環境移到 Oracle Cloud Always Free，讓個人電腦關機時仍能處理例行任務。

## 分工方式

```text
使用者
   ↓
Chief：接需求、拆工作、掌握進度
   ├─ Research：蒐集與查證資料
   ├─ Reviewer：檢查成果與驗收
   └─ Gemini Adapter：技術工作輔助
          ↓
Chief 彙整結果與需要核准的事項
```

## 已做出的成果

- **本地任務閉環**：Chief 接收任務、Research 交付、Reviewer 驗收，再由 Chief 結案。
- **Codex CLI Heartbeat**：已在本機成功執行一次真實 Codex Heartbeat。
- **角色與核准設定**：採用 Paperclip 原生組織分工、任務、留言和人工核准能力。
- **雲端部署規劃**：準備 Oracle ARM64 Compose、Tailscale 私網與備份流程，避免自行重造任務管理平台。

[查看 Oracle ARM64 部署範本](deploy/oracle-always-free/docker-compose.oracle-arm64.yml)

## 目前可用範圍

上述任務閉環與 Heartbeat 為本機驗證成果。Oracle 東京免費 VM 因容量不足尚未完成部署，因此不把全天候雲端運行當成已完成能力，也不保證所有情境都能維持零額外費用。

這個作品展示的是**如何整合成熟 Agent 平台，建立能分工、核准與回報的工作流程**；範例與設定已排除個人帳號及私人憑證。
