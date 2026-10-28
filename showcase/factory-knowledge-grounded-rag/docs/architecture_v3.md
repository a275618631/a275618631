# Factory Knowledge Grounded RAG — V3 System Architecture

> 文件狀態：歷史／參考；目前開發預設為 Qdrant Local Mode。此文件保留舊版 Docker Server 證據；Qdrant Docker／具名 Volume 是選用或歷史路徑，不是 Local Mode 的啟動前提，不得因閱讀本文件而啟動或操作受保護 Volume。

> **核心安全性準則 (Core Safety Principle)**：  
> **No unsupported actionable claim reaches the user.**  
> （沒有來源支持的可執行工程判斷／操作建議，絕不下發給現場人員。）

---

## 1. 端到端資料流與核心架構圖 (End-to-End Dataflow)

```mermaid
flowchart TD
    subgraph SOT["【Source of Truth (唯讀權威來源)】"]
        RAW["工廠設備手冊 / SOP / 警報表 (PDF / Markdown)"]
        REV["版本生命週期表 (Rev.A / Rev.B)"]
    end

    subgraph INTAKE["【結構化解析與正規化切片】"]
        DOCLING["Docling 結構化解析器 (保留標題、表格 Row/Cell、段落)"]
        CHUNK["Structure-aware Chunker (語意原子塊 + 表格保留)"]
        UUID["確定性 Chunk ID 生成 (SHA-256 Hash 跨行程一致)"]
    end

    subgraph INDEX["【衍生索引層 (Derived Indices)】"]
        FTS["SQLite FTS5 全文索引 (代號、警報、標籤、規格)"]
        EMBED["FastEmbed (ONNX CPU, 384-dim Dense Vector)"]
        QDRANT["Qdrant Local Mode（目前預設）；Docker Server 為選用／歷史路徑"]
    end

    subgraph RETRIEVAL["【多路融合與神經重排序】"]
        Q_IN["使用者現場工程問題 / 設備代碼"]
        TERM["W3C SKOS 三態術語解析器 (EXACT / CANDIDATE / AMBIGUOUS)"]
        RRF["Reciprocal Rank Fusion (RRF k=60 排名融合)"]
        BGE["BAAI/bge-reranker-v2-m3 (Cross-Encoder, 校準門檻值 0.05)"]
        EV_PKG["Evidence Package Builder (封裝 Provenance EV-001 ~ EV-xxx)"]
    end

    subgraph GEN_SAFE["【地端推理與確定性防幻覺安全互鎖】"]
        OLLAMA["Ollama 本地 LLM (qwen3:8b, 100% GPU offload, temp=0)"]
        SCHEMA["Pydantic JSON Schema 強制輸出結構"]
        VERIFIER{"DeterministicVerifier 安全互鎖閘門"}
        V_PASS["[PASS] 輸出核可處方步驟與完整引用"]
        V_ABSTAIN["[ABSTAIN] 依據不足或超範圍主動棄權"]
        V_BLOCK["[BLOCK] 攔截造假數值、標記跨版本衝突、歷史真因隔離"]
    end

    subgraph ISOLATION["【嚴格實體隔離邊界 (OT Boundary)】"]
        PLC["❌ 實體 PLC / SCADA / OT 網路 (完全隔離，嚴禁直寫)"]
    end

    RAW --> DOCLING --> CHUNK --> UUID
    UUID --> FTS
    UUID --> EMBED --> QDRANT

    Q_IN --> TERM
    TERM --> FTS
    TERM --> EMBED
    FTS --> RRF
    QDRANT --> RRF
    RRF --> BGE
    BGE --> EV_PKG
    EV_PKG --> OLLAMA
    REV --> VERIFIER
    OLLAMA --> SCHEMA --> VERIFIER

    VERIFIER -->|校驗通過| V_PASS
    VERIFIER -->|證據不足| V_ABSTAIN
    VERIFIER -->|安全違規| V_BLOCK

    V_PASS -.->|唯讀輔助人員| PLC
    V_BLOCK -.->|完全阻擋| PLC
```

---

## 2. 系統信任與安全邊界 (Trust & Security Boundaries)

### 2.1 權威來源 (Source of Truth) vs 衍生索引 (Derived Index)
- **原始手冊 (Source of Truth)**：永遠以受控版本之 PDF / Markdown 手冊為唯一準則。
- **向量資料庫與全文檢索 (Derived Indices)**：Qdrant 與 SQLite 僅為加速檢索之輔助衍生索引，不可作為獨立於手冊之外的事實來源。

### 2.2 人工審查邊界 (Human Review Boundary)
- 所有未經驗證之影像辨識、新設備知識均歸類為 `candidate`，嚴禁自動晉級為正式權威手冊。
- 歷史維修紀錄僅作為經驗參考，嚴格隔離，禁止 AI 自動升格為當前設備事故之唯一真因。

### 2.3 OT / 產線控制實體隔離 (OT Air-Gap)
- 本診斷系統純屬 **地端唯讀輔助分析工具**。
- 嚴禁透過任何自動化腳本直接對產線 PLC、SCADA 或工業機器人發出寫入或啟動指令。
- 診斷報告必須經由現場持證機電工程師人工確認後，手動於操作面板執行。
