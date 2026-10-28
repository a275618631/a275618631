# Provenance & Verification Boundary｜企業營運平台垂直切片

- **專案代號**：`enterprise-operations-platform`
- **原始來源**：GitHub 私有倉庫 [`a275618631/enterprise-operations-platform`](https://github.com/a275618631/enterprise-operations-platform)
- **來源分支與 Commit SHA**：`codex/m1-rem-equipment-create` · `c381e3d48a17b1e58be01d45594966c0769ca99a`（包含已合併之 PR #2 UX-02 角色導引與失敗復原）
- **同步日期**：2026-10-28
- **同步方式**：私有倉庫 Commit-pinned 小型架構垂直切片脫敏匯出

---

## 驗證證據狀態 (Evidence Status)

- **PR #2 (UX-02)**：**MERGED**（角色導引、401/403 攔截與重試保護）。
- **架構模型與狀態機**：**VERIFIED (Unit / Mock)**（工單狀態機模型、冪等防護機制通過單元測試驗證）。
- **瀏覽器端驗收**：PR #1、#3、#4 處於評估階段，公開切片僅包含核心模型與 Mock API 規格。

---

## 安全邊界宣告 (Mandatory Boundaries)

1. **零連線字串與零生產憑證**：本公開切片排除真實資料庫連線字串（僅提供 `appsettings.example.json` 與安全預設 `appsettings.json`）。
2. **零內部工單與員工個資**：排除所有真實維修紀錄、產線機台資料與員工個人識別資訊。
3. **區分 Mock 與 Production**：明確區分本地 Mock 測試環境與正式部署，不宣稱已完成全廠 E2E 系統驗收。
