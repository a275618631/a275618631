# Portfolio One-Command Demo Execution Flow

本文件記錄 `scripts/demo.ps1` 與 `app/demo.py` 的標準展示流程與技術亮點說明。

> 文件狀態：歷史／選用展示流程（需 Docker Qdrant 與 Ollama）。C 專案目前的預設開發入口是 Qdrant Local Mode；本文件不得取代 Local Mode，也不應為了執行本文件而啟動或操作受保護的 Docker Volume。

日常開發與最小驗證請依根目錄 `README.md` 的 Local Mode 指令執行；只有在已獲得相應環境核准且需要重現舊展示時，才使用下列 Docker／Ollama 流程。

---

## 1. 執行方式

在專案根目錄下直接執行：

```powershell
.\scripts\demo.ps1
```

或使用 Python 指令：

```powershell
python app/demo.py --profile portfolio
```

---

## 2. 展示步驟與防護行為

```text
[Preflight Check]
  ├─ 檢查 Qdrant Docker 容器 (http://127.0.0.1:6333/healthz)
  └─ 檢查 Ollama 地端服務與 qwen3:8b 模型 (http://127.0.0.1:11434/api/tags)
       │
       ▼
[展示案例 1：精確工廠代碼與警報檢索 (Exact Code Lookup)]
  ├─ 題目：ALM-3025 光纖通訊中斷排除步驟
  ├─ 行為：SQLite FTS5 + RRF 融合精確命中手冊章節
  └─ 成果：驗證通過 (PASS)，完整引註 EV-001，下發安全重置程序
       │
       ▼
[展示案例 2：口語化設備故障語意對齊 (Semantic Paraphrase)]
  ├─ 題目：馬達運轉溫度過高排查
  ├─ 行為：Dense 向量召回 + BGE-Reranker (分數 > 0.05) 聚焦馬達冷卻章節
  └─ 成果：輸出結構化主張，數值比對吻合，核可標準量測步驟
       │
       ▼
[展示案例 3：超出工廠手冊範圍主動棄權 (Out-of-scope Abstention)]
  ├─ 題目：台積電 2 奈米廠 EUV 機台冷卻規格
  ├─ 行為：BGE-Reranker 分數過濾後，Evidence 集合為空
  └─ 成果：系統自動標記 ABSTAINED，絕不下發未授權操作，守住工業安全底線
```
