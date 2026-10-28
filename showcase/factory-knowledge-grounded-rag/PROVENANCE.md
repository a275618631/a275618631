# Provenance & Verification Boundary｜工廠設備知識庫與地端診斷助手 (RAG)

- **專案代號**：`factory-knowledge-grounded-rag`
- **原始來源**：GitHub 私有倉庫 [`a275618631/factory-knowledge-grounded-rag`](https://github.com/a275618631/factory-knowledge-grounded-rag)
- **來源分支與 Commit SHA**：`codex/docs-entry-20261019` · `2f0ba15bdf25909242fb4edfadceb183c62f82a2`（基線分支 `master`：`a02aa3db55137d7d74478bb489e3ab7b5e0b89a6`）
- **同步日期**：2026-10-28
- **同步方式**：私有倉庫 Commit-pinned 核心邏輯與合成 Benchmark 脫敏匯出

---

## 驗證證據狀態 (Evidence Status)

- **核心安全性準則**：**No unsupported actionable claim reaches the user.**（無來源支持的可執行判斷，絕不輸出）。
- **離線檢索與診斷**：**VERIFIED**（支援 Local Qdrant / BM25 離線檢索，具備來源引用 Citation 與版本衝突比對）。
- **負向防護與拒答 (Negative Safety & Abstain)**：**PASS**（在缺乏足夠證據時，系統輸出 `ABSTAINED` 並停止操作建議）。

---

## 安全邊界宣告 (Mandatory Boundaries)

1. **嚴禁散布未授權之真實 OEM PDF 原檔**：本公開展示僅使用**高保真合成設備手冊語料**（如冷軋機假想規格 DOC-Y52-*）。雖然研發階段曾於受控環境使用 8 份公開 OEM 原廠手冊進行引用驗證，但**基於原廠版權保護，本公開倉絕不提供或再散布任何 OEM 原廠 PDF 檔案**。
2. **預設唯讀與禁止自動控制 PLC**：本系統設計為純諮詢與診斷助手，**嚴禁**自動連線或寫入 PLC / SCADA 設備。
3. **Web API 狀態宣告**：Web API 程式碼僅供架構與合約展示，不代表通過跨租戶授權驗收或正式生產上線。
