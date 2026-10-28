# A｜作品集導向的後續規劃｜2026-10-21

## 定位與完成定義

本文件供後續 A-scoped worker 執行。A 的既有本機垂直切片已能 Demo：Development 登入、角色授權、設備讀取、工單讀取／建立／完成、PostgreSQL 持久化、合成資料備份／還原。這是已完成的 **local MVP slice**，不是原始作品集路線全部完成。實際驗收以當次 Repo commit、測試輸出和瀏覽器操作證據為準；舊報告的 PASS 不自動代表新改動通過。

原規劃的 M1 還包含設備新增、工單指派與較完整狀態流轉、OpenAPI／契約展示、瀏覽器 E2E；作品集核心規劃另列 Fake Supplier outbound REST、inbound webhook 與基本操作追蹤。它們保留在原路線內，不因這次優化另增新模組。正式 Identity Provider、使用者治理、部署／監控與 MCP 等沿用原後續里程碑，不列為下一個本機 Demo 的前置條件。

來源：[Repo README](../README.md)、[架構契約](ARCHITECTURE_MVP_20261016.md)、[原 M0–M8 實作路線](https://docs.google.com/document/d/1TlpUBppDE-Ps1sdvFUjwBKnGlU980T3-AIoPmeK1dgU/edit)、[作品集 MVP 收斂](https://docs.google.com/document/d/1hu3RuDf2IvjLULEeCbTZeeZOH1k8nJRttoXEg5-XpsA/edit)。若 Drive 舊進度與 Repo 實作衝突，以 Repo 程式與當次測試證據判定「已完成」。

## 範圍護欄與協作

- 僅在 A Repo 的 `codex/` 安全分支工作；不碰 B／C、跨專案資源、遠端 Push、Merge 或部署。四類既有未追蹤項目保留，不執行 `git add -A`。
- 每次只有一個 active writer 修改同一 write-set。worker 領取下列單一工作包，開始前唯讀確認 Root、Branch、HEAD、dirty state，先讀 README／AGENTS／架構／本文件；回報變更檔案、測試與 rollback。其他 worker 可做獨立唯讀覆核。
- 僅用合成資料。現有 PostgreSQL 資料（目前含重複測試工單）不視為可丟棄；Demo 資料必須在獨立測試 DB 或可回復 fixture 建立，不能清空既有 DB。
- 不把 signing key、密碼或 token 寫入 Git、截圖、測試輸出或報告。前端角色提示是導引，API RBAC 才是權限邊界；外部貼入的 token 不可由前端猜角色。
- 每包完成時更新狀態為 `PASS`、`FAIL` 或 `BLOCKED`，附上 commit、驗收證據、已知限制。下方工作包均為 `PLANNED`；負責人和期限尚未指定。

## 執行順序

| 順序 | 工作包 | 範圍 | 完成門檻 | 狀態 |
|---|---|---|---|---|
| 1 | UX-01：既有旅程的介面整理 | `frontend/src/App.vue`、`frontend/src/style.css`、必要時 UX 文件 | 登入後主視覺聚焦設備與工單；Demo／進階 token 設定可收合；桌機與窄畫面可用；操作有明確結果 | PASS：PR #2 合併，320px 瀏覽器證據見 artifacts/ux-02-role-guidance-20261022 |
| 2 | UX-02：角色導引與錯誤復原 | 同一前端 write-set；須等 UX-01 完成 | Viewer／Operator／Supervisor 的可用動作與 API 政策一致；401／403、逾時、空清單與驗證錯誤有可行下一步 | PASS：PR #2 合併 |
| 3 | QA-01：可重現的 Demo 與瀏覽器驗收 | 前端測試／fixture、測試說明；不改現有 DB | 三角色主流程與 401／403 在瀏覽器重現；PostgreSQL 建立→重啟→讀回與合成資料還原有當次證據 | PASS：原基線 run `c11c4ca1…`／PR #3；M1 post-commit 回歸 run `7d7cc605a2964c13be325b51456778d1`／commit `a4c08e4`；[QA-01 report](A_QA-01_repeatable_demo_acceptance_2026-10-22.md) |
| 4 | M1-REM：原 M1 尚缺業務流程 | A 的 API／資料庫／前端，依子工作包拆開 | 設備新增、工單指派與狀態流轉符合原規劃；migration、RBAC、OpenAPI、UI、回歸測試一致 | IN PROGRESS：設備建立切片 PASS（實作 commit `be72e80`、行動版驗收 commit `a4c08e4`）；剩餘工單指派／狀態流轉與 OpenAPI／contracts |
| 5 | M2-INT：原整合示範 | A 的獨立 integration adapter 與 fake provider | outbound REST、inbound webhook 的成功／失敗／去重與基本 trace 有合成測試；停用 adapter 時核心設備／工單仍可運作 | PLANNED |
| 6 | PORT-01：作品集交付 | README、操作截圖／錄影與證據索引 | 觀看者可在數分鐘內看懂任務、角色差異、持久化和限制；每個「已驗證」宣稱有 commit／run／畫面證據 | PLANNED |

## 可直接領取的下一批工作

### UX-01｜登入後的工作台整理

**目的**：讓維修人員或主管在登入後第一眼看到設備狀態、待處理工單與下一個動作。沿用現有 Vue 頁面與 API；不新增 Dashboard、路由或業務資料欄位。

**實作邊界**：保留 Demo 登入及手貼 Bearer token 功能；登入後將設定區收合，讓目前角色、設備、工單成為主區域。用現有狀態呈現空清單、讀取中、操作成功與失敗；將 `Operational`／`Attention`、`Open`／`Completed` 等 UI 顯示文案統一為易懂中文，API 值保持不變。檢查手機寬度、鍵盤焦點、欄位標籤、狀態文字與對比。

**驗收**：未登入與登入後的桌機／窄畫面均可找到主動作；登入、查看設備、輸入工單、送出與重新整理都能操作；不把 token 顯示或存入 browser storage；`npm run build` 通過。提供截圖與操作紀錄，無障礙合規不得只憑截圖宣稱。

**2026-10-22 實作檢查點**：登入設定於成功載入後收合；工作區目前顯示設備與工單，狀態／優先級使用中文顯示，提供空／載入／操作結果訊息及欄位標籤、ARIA 狀態與焦點樣式。`npm run build` 與 `git diff --check` 通過；本機瀏覽器以合成 Operator 登入，讀取 2 台設備、28 筆既有本機測試工單，並確認重新整理成功。另以 API `/health` 確認 `persistence=in-memory` 後，在隔離的程序記憶體中用滑鼠與 Enter 各建立一筆合成工單，畫面均回報成功且更新清單；未寫入 PostgreSQL。後續 UX-02 的 [PR #2](https://github.com/a275618631/enterprise-operations-platform/pull/2) 已提供 320px 瀏覽器驗收及角色操作證據，故 UX-01／UX-02 均結案。此檢查點已提交至 A 分支。

### UX-02｜角色導引與失敗復原

**依賴**：UX-01 合併到工作分支後執行，避免同時改 `App.vue`。

**實作邊界**：Development Demo 登入已取得角色時，Viewer 不提供建立操作，Operator 不提供完成操作，Supervisor／Administrator 顯示相應動作；可用文字說明原因。外部 token 模式保持權限未知，由 API 回應判定，不能解析未驗證的 JWT 當成授權。401 提示重登，403 提示角色不足，API 不可用提示重試；成功訊息須與實際資料更新一致。

**驗收**：四種 Demo 角色的可見動作對照 README 的 RBAC 表；直接呼叫 API 仍驗證 401／403；前端 build 通過；手動或自動驗證角色切換與操作失敗後可恢復。

### QA-01｜Demo 驗收與資料隔離

**依賴**：UX-01／02 的主要互動穩定後執行；可先唯讀設計測試案例。

**實作邊界**：在獨立的合成資料環境跑瀏覽器驗收，不重設使用者現有 PostgreSQL。覆蓋 Viewer 查看但不可建立、Operator 建立但不可完成、Supervisor 完成、錯誤密碼、未登入 401、權限不足 403、重整後資料持續存在。測試工具以現有 Vue／.NET 生態中最小可維護方案選擇；避免測試只重述實作。

**驗收**：一組可重跑的命令、測試結果、失敗定位方式和當次環境／commit 記錄；PostgreSQL 與 in-memory 分支各自標示，不把兩者混稱同一持久化證據。備份／還原沿用既有 helper，在獨立 restore DB 驗證。

**資料安全決策**：既有 `enterprise_operations_restore_smoke` 的 `public` schema 含有先前資料，不視為空白或可清除。QA runner 每次建立唯一 `qa01_<run>` schema；migration、測試資料、備份及 `pg_restore --schema` 都限制在該 schema。runner 不連線到主要 `enterprise_operations` DB 作寫入，不刪除 QA schema，也不清空既有 restore DB 的其他 schema。

**2026-10-22 驗收檢查點**：QA-01 PASS，run `56026d68b2de4827a504f99effb350d3`，schema `qa01_56026d68b2de4827a504f99effb350d3`，驗收程式 commit `e2a9b9c6359100db484bd5fd24b38359bc839c66`。完整報告與畫面／摘要索引見 [A_QA-01_repeatable_demo_acceptance_2026-10-22.md](A_QA-01_repeatable_demo_acceptance_2026-10-22.md)。通過 .NET Release（17 passed、1 intentionally skipped）、Vue production build、瀏覽器 401／403 與三角色流程、320px 無水平溢位、API restart persistence、限定 schema 的 backup／restore digest 比對，以及快照內／快照後資料驗證。已確認 QA API／Vite 程序結束且測試埠釋放；僅使用 restore smoke DB 內新建的唯一 schema。

## 後續原規劃工作包的拆分條件

### 2026-10-27 M1-REM 設備建立切片驗收

- 狀態：**PASS，僅此子切片完成；M1-REM 整體仍進行中**。
- 實作：`POST /api/operations/equipment` 沿用既有 `WritePolicy`；設備代碼正規化大寫且唯一（最多 32 字元），名稱／區域各最多 200 字元，狀態限 `Operational`／`Attention`。匿名 401、Viewer 403、無效欄位 400、重複代碼 409；Operator 可新增，並可用新設備建立工單。既有資料表足夠，無 migration。
- UI：設備清單內新增設備表單與 Viewer 導引，提供提交中、成功、驗證錯誤與重複代碼回饋；窄版單欄呈現。
- commits：實作 `be72e8082dceee00b4bedcb02352c2fa9496f9be`、行動版驗收 `a4c08e4ea44746bd4d5df8761169152ed08c25e2`；分支 `codex/m1-rem-equipment-create`，堆疊在 QA-01 PR #3 之上，尚未合併。
- 驗收：.NET Release 22 passed／1 intentionally skipped；Vue production build PASS；QA-01 post-commit run `7d7cc605a2964c13be325b51456778d1`（專用 `enterprise_operations_restore_smoke` DB 的唯一 schema）。涵蓋匿名 401／Viewer 403／Operator 新增設備與工單／Supervisor 完成、Viewer 與 Operator 320px 水平溢位、API 重啟資料讀回、schema-scoped backup／restore digest 相符與 snapshot boundary。完整摘要與畫面索引見 [QA-01 report](A_QA-01_repeatable_demo_acceptance_2026-10-22.md)。
- QA runner 已允許在堆疊的 `codex/m1-rem-*` 分支執行；證據中的 commit 與受測程式版本一致。
- 下一子切片仍依 roadmap：工單指派與完整狀態轉換；先定義舊 `Open`／`Completed` 資料的相容對應，不破壞既有工單，再處理 OpenAPI／contracts。

- **M1-REM** 先拆成設備新增，再拆成工單指派／狀態。原規劃狀態為 `OPEN → IN_PROGRESS → PENDING_REVIEW → CLOSED`；目前 API 使用 `Open → Completed`。實作前先在既有資料上定義相容遷移與舊狀態對應，再由單一 worker 同步 API、migration、Vue 和測試。不可直接更名舊資料狀態或破壞現有工單。
- **M2-INT** 在 M1 核心流程穩定後才做。Fake Supplier 與 webhook 完全使用合成資料；adapter 可停用，逾時／失聯不阻斷設備查詢或工單操作。用不含敏感資訊的 trace／操作紀錄串起請求與結果。原 M2 還包含 Legacy adapter，但先以可驗證的一條 Fake Supplier 往返示範收斂，不宣稱其餘整合已完成。
- **PORT-01** 使用獨立合成 Demo 資料集與清晰的角色腳本，避免把本機 28 筆歷史測試工單當展示成品；保留現有資料。README 精確列出已完成、原規劃未完成及正式產品後續，不以「完整 CRUD」或「完整企業產品」稱呼目前切片。

## 延後但保留的原路線

正式 IdP、使用者／角色管理、token 撤銷與輪替、完整 audit 治理、CI／Secret Manager／部署與監控、MCP、RAG、進階基礎設施均屬原規劃後段或選修階段。除非新的使用者決策改變優先級，這些不佔用 UX-01 至 QA-01 的 write-set 或驗收時程。本機 Demo 完成後再評估封裝與公開展示方式。

## 目前應校正的用語

- 現況：設備 **讀取**；工單 **讀取、建立、完成**。完整設備／工單 CRUD 尚未完成。
- 前端在送出期間停用建立按鈕，可避免同一頁的連續點擊；後端尚無通用冪等鍵或重複請求去重，不宣稱完整防重提交。
- 17/17 .NET 測試、Vue build、PostgreSQL restore 是先前已記錄證據；每個新工作包須提供自己的當次驗證。
