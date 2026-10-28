# A 專案｜QA-01 可重現 Demo 驗收紀錄｜2026-10-22

## 結果

**PASS**。QA-01 基線驗收與 M1 設備新增後回歸皆通過，驗證的是不同分支／程式切片，證據分開保留。PR #3 的 runner 修正後，最新基線 run 為 `5656043c…`（受測 commit `6f5e8f7`）；PR #3 整合至 M1 分支後，最新完整回歸 run 為 `e638b556…`（受測 merge commit `5f05189`）。更新日期：2026-10-27。

- QA-01 基線分支：`codex/qa-01-repeatable-browser-acceptance-20261022`；[PR #3](https://github.com/a275618631/enterprise-operations-platform/pull/3)（open；尚未合併）
- 最新基線 run：`5656043ce90e40f1abd87ae9b82fa30e`，commit `6f5e8f7885b6bb5b1ae7a79693e5f6062a5f1cb9`（API `5080`、Web `5173`）
- 基線 PostgreSQL：`enterprise_operations_restore_smoke` / `qa01_5656043ce90e40f1abd87ae9b82fa30e`
- M1 功能分支：`codex/m1-rem-equipment-create`；[PR #4](https://github.com/a275618631/enterprise-operations-platform/pull/4)（open；尚未合併）
- M1 最新整合回歸 run：`e638b556868547f6a48f4f01984e62dd`，受測 merge commit `5f05189af87ead2371bd6c3698aa17dbf8eb4b84`
- M1 PostgreSQL：`enterprise_operations_restore_smoke` / `qa01_e638b556868547f6a48f4f01984e62dd`
- 前次 M1 run：`7d7cc605a2964c13be325b51456778d1`，commit `a4c08e4ea44746bd4d5df8761169152ed08c25e2`（保留作歷史證據）
- 最新基線摘要：[`qa-01-summary.json`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/qa-01-summary.json)；[Drive copy](https://drive.google.com/file/d/1Z96IF03E0xLp8gULzxZwHXz7mGowSH1S/view?usp=drivesdk)
- M1 最新整合回歸摘要：[`qa-01-summary.json`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/qa-01-summary.json)；[Drive copy](https://drive.google.com/file/d/1XMp6lvIjoC5RichY1Mojy52UkvtOO0bK/view?usp=drivesdk)
- 前次 M1 回歸摘要：[`qa-01-summary.json`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/qa-01-summary.json)；[Drive copy](https://drive.google.com/file/d/1XP_NQCM_gAv9jNapCcTrDT1CYXz4PnoP/view?usp=drivesdk)
- 單一命令重跑：`pwsh -ExecutionPolicy Bypass -File .\scripts\qa-01.ps1`
- 初次成功摘要：[`qa-01-summary.json`](../artifacts/qa-01-56026d68b2de4827a504f99effb350d3/qa-01-summary.json)

## ADHD 速讀

1. **登入／權限**：未登入 API 得到 401；Viewer 新增設備／建立工單得到 403；Operator 可新增設備並以該設備建立工單；Supervisor 可完成工單。
2. **手機寬度**：Viewer 與 Operator 設備表單的 320px 版面均無水平溢位；三角色主要流程均通過。
3. **資料真的有保存**：建立並完成的合成工單，在 API 停止再啟動後仍讀得到。
4. **還原有驗證**：備份後再新增一筆合成工單；還原後原快照工單仍在、快照後新增項目消失，資料摘要相同。
5. **安全邊界**：只在 restore smoke DB 的唯一 `qa01_...` schema 操作；不以主要 `enterprise_operations` DB 作目標，不清除既有 `public` schema。測試結束後 API／Vite 已停止，5080／5173 埠已釋放。

## 驗收證據

| 證據 | 用途 |
|---|---|
| [`qa-01-summary.json`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/qa-01-summary.json) · [Drive](https://drive.google.com/file/d/1Z96IF03E0xLp8gULzxZwHXz7mGowSH1S/view?usp=drivesdk) | PR #3 最新基線 PASS、commit、branch、schema、8 個通過階段 |
| [`database-digest-5656043ce90e40f1abd87ae9b82fa30e.json`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/database-digest-5656043ce90e40f1abd87ae9b82fa30e.json) · [Drive](https://drive.google.com/file/d/14aOSbAYQ2AQ0v0_XaDt0ckHphEQYBBd_/view?usp=drivesdk) | 基線備份／還原 digest |
| [`viewer-320px.png`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/viewer-320px.png) · [Drive](https://drive.google.com/file/d/1suJwuyd2UWLfRqfuriiNCipQe1ngLzyB/view?usp=drivesdk) | 基線窄版 Viewer 畫面 |
| [`operator-work-order.png`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/operator-work-order.png) · [Drive](https://drive.google.com/file/d/12OkiiLHESaDxn_2iJsVScLzmrwsSnDcW/view?usp=drivesdk) | 基線 Operator 建立工單畫面 |
| [`supervisor-completed.png`](../artifacts/qa-01-5656043ce90e40f1abd87ae9b82fa30e/supervisor-completed.png) · [Drive](https://drive.google.com/file/d/1doGrICabLnMBuPnMYuxPaZvcP7HGn_PV/view?usp=drivesdk) | 基線 Supervisor 完成工單畫面 |
| [`qa-01-summary.json`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/qa-01-summary.json) · [Drive](https://drive.google.com/file/d/1XMp6lvIjoC5RichY1Mojy52UkvtOO0bK/view?usp=drivesdk) | PR #3 整合至 M1 分支後的最新完整回歸 PASS；受測 commit `5f05189` |
| [`database-digest-e638b556868547f6a48f4f01984e62dd.json`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/database-digest-e638b556868547f6a48f4f01984e62dd.json) · [Drive](https://drive.google.com/file/d/18ejQbHRUrzttymx_7LhoF7uu6UBu7jR4/view?usp=drivesdk) | 最新 M1 整合回歸備份／還原 digest |
| [`viewer-320px.png`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/viewer-320px.png) · [Drive](https://drive.google.com/file/d/1KxJgrjWXHpYAjOc63_NPGjx1ypP8_UOr/view?usp=drivesdk) | 最新 Viewer 窄版驗收畫面 |
| [`operator-equipment-320px.png`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/operator-equipment-320px.png) · [Drive](https://drive.google.com/file/d/1vCojF7IvMVje7V2oOKWdT6a880UPxy5M/view?usp=drivesdk) | Operator 設備新增表單 320px 畫面 |
| [`operator-work-order.png`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/operator-work-order.png) · [Drive](https://drive.google.com/file/d/1V0Z4F3KfUHoj46frosIujYoD2GCinOCu/view?usp=drivesdk) | Operator 建立工單畫面 |
| [`supervisor-completed.png`](../artifacts/qa-01-e638b556868547f6a48f4f01984e62dd/supervisor-completed.png) · [Drive](https://drive.google.com/file/d/1V2ybka8reN7n04mxBkk7ZFM-ABWpM-Vt/view?usp=drivesdk) | Supervisor 完成工單畫面 |
| [`qa-01-summary.json`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/qa-01-summary.json) · [Drive](https://drive.google.com/file/d/1XP_NQCM_gAv9jNapCcTrDT1CYXz4PnoP/view?usp=drivesdk) | 前次 M1 受測 commit `a4c08e4` 的回歸 PASS，保留歷史紀錄 |
| [`database-digest-7d7cc605a2964c13be325b51456778d1.json`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/database-digest-7d7cc605a2964c13be325b51456778d1.json) · [Drive](https://drive.google.com/file/d/1LXvXNmqsch7tMXMcMeJLy60EV9M7ofJm/view?usp=drivesdk) | M1 測試快照 digest |
| [`viewer-320px.png`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/viewer-320px.png) · [Drive](https://drive.google.com/file/d/1-yTQdZ5c_emVsIO8LcezTUoSr7g_Rjz9/view?usp=drivesdk) | M1 回歸窄版 Viewer 畫面 |
| [`operator-equipment-320px.png`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/operator-equipment-320px.png) · [Drive](https://drive.google.com/file/d/1Ng4Wopu0GXE6VQN6p3XD252Ns_HKTidN/view?usp=drivesdk) | Operator 新設備表單的 320px 驗收畫面 |
| [`operator-work-order.png`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/operator-work-order.png) · [Drive](https://drive.google.com/file/d/1X9YS2eoFlMiz-uWk3RyKiaUY5HsYt-Kk/view?usp=drivesdk) | Operator 新增設備並建立工單畫面 |
| [`supervisor-completed.png`](../artifacts/qa-01-7d7cc605a2964c13be325b51456778d1/supervisor-completed.png) · [Drive](https://drive.google.com/file/d/1A_nwEGqqz_S6l8nV_fI85jCsnFDDnpQn/view?usp=drivesdk) | M1 回歸 Supervisor 完成工單畫面 |

PR 審查指出 QA runner 以分號切割連線字串會破壞引號內含分號的密碼，且備份／還原未沿用已設定的 PostgreSQL Host／Port。commit `6f5e8f7` 改用 .NET `DbConnectionStringBuilder` 解析、改寫 Database/Search Path，並將 Host／Port／Username 傳入兩個 helper；合成案例確認 `Password="qa01;parser-probe"` round-trip 正確且 Port `55432` 可讀。修正後的完整 run `5656043c…` 再次通過 8 個階段。此前自訂 URL 的非預設 loopback 埠 `5180`／`5174` 完整重跑證據仍保留於 run `c11c4ca1…`；API 預設 CORS 來源仍維持既有設定，可由設定覆寫。

備份 `.dump` 為本機合成測試產物，不納入版本控制；截圖與 JSON 不含密碼、token 或連線字串。

原始 Playwright trace 僅保留於本機驗收目錄，未提交／上傳；公開索引使用經挑選的摘要、digest 與畫面證據。

## 驗證摘要

- 最新整合回歸 `.NET Release`：22 passed、1 skipped（QA 專用 PostgreSQL bootstrap 測試在未帶明確 QA flag 的一般測試中刻意略過）。
- Vue production build：通過。
- 瀏覽器角色／狀態流程：通過；Playwright 每一個階段只執行該階段測試，其餘 3 個階段測試會依設計 skip。
- PostgreSQL migration、API restart read-back、schema-scoped backup／restore、digest 等值、快照內外資料確認：通過。
- `git diff --check`：通過；QA-01 run `e638b5…` 的摘要記錄 M1 最新整合受測 commit `5f05189`。前次 M1 run `7d7cc6…` 仍留作歷史證據。

## 尚未完成

QA-01 已結案。M1-REM 的設備建立切片已完成；M1 剩下工單指派／完整狀態流轉與契約展示。其後仍是 M2-INT（Fake Supplier／webhook 示範）及 PORT-01（作品集整理與正式展示）。不包含正式 IdP、部署或監控等範圍擴張。
