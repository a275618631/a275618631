# 工廠設備知識庫與地端診斷助手 (Factory Knowledge Grounded RAG)

> **核心安全性準則**：  
> **No unsupported actionable claim reaches the user.**  
> （沒有來源支持的可執行工程判斷／操作建議，不得輸出給使用者。）

本專案是一個 **工具無關 (Tool-Agnostic)、Local-First、完全可離線執行** 的工廠設備知識庫與診斷助手系統。系統預設唯讀，嚴禁自動控制 PLC/SCADA；AI 產出之新知識與影像辨識一律預設為 `candidate`，必須經由專家審查方可生效。

## 唯一開發入口

正確 Repo Root：`.`

先讀本 README，再讀 `docs/architecture_v3.md`、`docs/demo_flow.md`、`reports/CURRENT_STATUS.md`，最後依 `tests/` 與 `reports/sprint-*` 的證據工作。這個 checkout 的預設開發路徑是 Qdrant Local；Docker Server 與 Ollama 展示是選用／歷史路徑，不是 Local Mode 的啟動前提。

使用者操作以 CLI／展示流程為主：執行本地測試或 Local Mode query，查看來源 citation；若證據不足，系統必須回傳 `ABSTAINED` 且不得產生可執行處方。系統不寫入 PLC／SCADA。

## 版本、來源與證據對照

| 版本／名稱 | 本機可驗證狀態 | 來源與證據 |
|---|---|---|
| `master` | `Current`；本 checkout 以 `master` 為基線，文件修正位於安全分支 | Git branch、`README.md`、`reports/CURRENT_STATUS.md` |
| `public-real-document-pilot-v1` | `Reference`；唯讀 `git ls-remote` 已確認遠端 ref，Commit `775a81e2b6e7e0af3e7374bfa8ce8a02de158374`；本機未驗證內容 | 不在本機 checkout、未 Checkout／Merge；仍需人工核對遠端與 Drive provenance |
| 2026-10-15 Pre-Pilot | `Reference`／`UNKNOWN`；未複製 Drive 文件至 Repo | Drive 專案資料夾 `1s34Z2_KDwzDOdkM5OJzwhRlkthbZM7CY`；本機只採既有報告證據 |
| 2026-10-16 Public Pilot | `Reference`／`UNKNOWN`；未複製 Drive 文件至 Repo | Drive／外部交接文件需人工核對；本機不宣稱已取得 |
| 2026-10-19 Local evidence | `Current evidence` | Qdrant Local synthetic query／reopen、引用與 `ABSTAINED` 測試；未啟動 Docker |

不同名稱不代表重複版本；合併或歸檔前必須取得 provenance、commit／文件日期與內容差異證據。

---

## 證據等級與系統邊界 (Evidence Level & System Boundaries)

### 證據等級：`V3 — Technical PoC on Synthetic Benchmark Corpus`（歷史基線）

> [!IMPORTANT]
> **本節保留 2026-10 審計的 V3 技術 PoC 歷史基線**。
> 其中 Docker Server／Ollama 的端到端描述與指標是歷史證據，不代表本輪 Local Mode 已重新執行；本輪可驗證證據以文件上方的 2026-10-19 Local evidence 與下方 14 項測試為準。
>
> **強制系統邊界宣告 (Mandatory Boundary Disclaimers)**：
> - **NOT real factory data validation**：測試語料為高保真合成／開源假想冷軋設備手冊，尚未取得或驗證廠內真實機密資料。
> - **NOT production acceptance**：本階段為技術 PoC 驗證，不代表已通過廠區生產驗收。
> - **NOT live OT validation**：系統未實體連線真實產線 PLC / SCADA / OPC UA 即時資料流（預留為架構擴展介面）。

---

## 系統現況與誠實邊界揭露 (V3 Truth Matrix)

| 組件／模組 | 實體實作機制 | 驗證狀態 | 備註說明 |
|---|---|---|---|
| **文件解析 (Docling)** | `adapters/parsers/docling_adapter.py` | **REAL EXECUTION** | 支援多格式轉結構化 Markdown，附輕量解析備援 |
| **密集向量嵌入 (FastEmbed)** | `adapters/embedding/fastembed_embedder.py` | **REAL EXECUTION** | `paraphrase-multilingual-MiniLM-L12-v2` (ONNX CPU, 384 維度) |
| **向量資料庫 (Local)** | `adapters/vector/qdrant_store.py` | **REAL EXECUTION** | Qdrant Local／本地儲存模式；目前開發預設 |
| **向量資料庫 (Docker Server)** | Qdrant Docker (`factory-qdrant`, v1.19.1) | **HISTORICAL / OPTIONAL** | 舊版 Server／具名 Volume 證據保留；本輪不啟動、不接觸 Volume |
| **全文檢索 (SQLite FTS5)** | `adapters/retrieval/sqlite_fts.py` | **REAL EXECUTION** | 支援代號、Alarm、Tag 精確比對，CJK n-gram 分詞 |
| **混合檢索融合 (RRF)** | `adapters/retrieval/hybrid_retriever.py` | **REAL EXECUTION** | Reciprocal Rank Fusion (k=60)，整合全文與語意檢索 |
| **神經重排序 (BGE Reranker)** | `adapters/rerank/bge_v2_m3_reranker.py` | **REAL EXECUTION** | `BAAI/bge-reranker-v2-m3` (560M 參數)，科學化校準最佳門檻值 `0.05` |
| **本機 LLM 生成 (Ollama)** | `adapters/llm/ollama_adapter.py` | **HISTORICAL / OPTIONAL** | 舊版本機 `qwen3:8b` 證據保留；Local Mode 核心測試不以 Ollama 為前提 |
| **確定性防幻覺閘門** | `core/verifier.py` (`DeterministicVerifier`) | **REAL EXECUTION** | 5 大安全閘門（數值精確比對、引用存在性、衝突阻擋、歷史隔離、無佐證棄權） |
| **評測測試語料 (Corpus)** | `data/source/` (12 份合成標準手冊) | **SYNTHETIC / LICENSE-SAFE** | 高保真假想冷軋設備手冊，安全無機密洩漏風險 |
| **現場 OT 網路連線 (Factory OT)** | N/A (未連線真實產線) | **NOT VALIDATED** | 嚴格隔離，預設唯讀 |

---

## 系統架構：Thin Core + 可替換 Adapters

```text
使用者問題 / 故障現象
       │
       ▼
Query / Terminology Resolver (三態解析: EXACT / CANDIDATE / AMBIGUOUS)
       │
       ▼
Hybrid Retrieval Pipeline (多路融合檢索)
  ├─ SQLite FTS5 全文索引 (代號、警報、規格)
  └─ Qdrant Local 向量資料庫 (FastEmbed 384-dim；Docker Server 為選用路徑)
       │
       ▼
Reciprocal Rank Fusion (RRF k=60)
       │
       ▼
BGE Multilingual Cross-Encoder Reranker (校準門檻值 0.05 過濾)
       │
       ▼
Evidence Package Builder (封裝合格佐證與完整 Provenance EV-xxx)
       │
       ▼
Local LLM Generation (Ollama qwen3:8b, Pydantic JSON Schema, temp=0)
       │
       ▼
Deterministic Verifier Gate (防幻覺確定性檢驗閘門)
  ├─ [PASS]  輸出結構化診斷結果 + 完整引用佐證
  ├─ [ABSTAIN] 查無足夠資料時主動棄權，列出現場手動確認項目
  └─ [BLOCK] 攔截未經核可操作、攔截造假數值、標記跨版本衝突
```

---

## 驗證指標與成果

### 1. 單元與整合測試
- **2026-10-19 Local Mode smoke**：**14 / 14 PASSED**（Qdrant Local、引用、ABSTAIN、結構化輸出與負向安全測試；本輪實測證據）
- **歷史全量基線**：57 / 57 與 Legacy Golden 30 / 30 保留作為舊版審計證據，未在本輪重新執行。

### 2. 端到端評測（2026-10 審計定錨）
- **功能狀態吻合率 (Functional Status Match)**：**76.0% (19/25)**（包含因保守安全防護所採取的棄權）
- **安全合規率 (Safety Compliance Rate)**：**100.0% (25/25)**（零未授權處方、零數值幻覺、零跨版本衝突流出）
- **重排序超範圍拒答準確率 (No-Answer Accuracy)**：**100.0%**（誤接受率 0.0%）

---

## 快速啟動 (Local Mode 預設)

### 本機需求

- Python 3.12
- C 專用 `.venv`（若尚未建立，依專案環境政策建立於 Repo 根目錄；`.gitignore` 已排除）
- 不需要 Docker、Qdrant Server 或 Ollama 即可執行 Local Mode 核心測試

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_sprint2_qdrant.py tests/test_mvp1_retrieval.py tests/test_mvp2_structured_llm.py tests/test_sprint3_negative_safety.py
```

### Docker／Ollama（歷史或選用）

`docker-compose.yml`、`scripts/demo.ps1` 與 `app/demo.py --profile portfolio` 是舊版 Server／展示流程。它們需要 Docker Qdrant `:6333` 與／或 Ollama；除非另有核准，不得將其當成 Local Mode 預設啟動流程，也不得操作受保護的 `factory-qdrant-data`。

## 文件去向

| Class | C evidence / location | Status |
|---|---|---|
| Current | This README, `docs/`, `reports/CURRENT_STATUS.md`, `tests/`, `adapters/`, `core/`, `app/` | Local source of truth for current code/tests |
| Reference | Drive folder `1s34Z2_KDwzDOdkM5OJzwhRlkthbZM7CY` | External planning/reference; not copied into Repo |
| Archive | `reports/sprint-0` through `reports/sprint-4`, `reports/audit-2026-10` | Historical evidence; retain, do not delete or rename |
| Duplicate candidate | Overlapping dated reports and Drive exports | Not classified by filename; requires provenance and content comparison |
