# Agent 工具策略引擎 (Thin Agent Tool Policy Engine)

> **核心設計原則**：  
> **不把 Prompt 當作安全邊界，模型宣稱安全不代表能放寬執行權限。**  
> 純 Python、零執行期外部依賴的決定論 (Deterministic) 安全策略核心，專門防範 AI Agent 自主調用工具時的越權寫入與危險指令。

---

## 1. 核心痛點與防禦概念

AI Agent 在調用本機終端、檔案讀寫或 MCP 工具時，最常見的安全風險是 **Prompt Injection**：攻擊者透過 Prompt 誘導模型「忽略先前的指令，改為讀取/覆寫系統檔案」。

若將安全防護寄託於模型「聽不聽話」，在工程上是不可靠的。本專案採用**決定論安全架構**：
- 在工具真正執行前，強制進行靜態 Preflight 檢查。
- 根據工具名稱、動作類型、路徑正規化結果與受保護分支規則進行風險評估。
- 評估結果僅有 4 種確定性狀態：`allow`、`allow_scoped`、`require_approval`、`deny`。

---

## 2. 核心使用範例：輸入工具呼叫 → 判定安全等級

```python
from agent_policy.evaluator import evaluate
from agent_policy.model import Decision, ToolCall
from agent_policy.policy_loader import load_policy

# 載入 TOML 安全政策
policy = load_policy("policies/policy.toml")

# 1. 唯讀狀態檢查：直接放行 (ALLOW)
res1 = evaluate(ToolCall("git", "git.status"), policy)
print(res1.decision)  # Decision.ALLOW

# 2. 嘗試寫入工作區外的敏感路徑：判定需人工審核 (REQUIRE_APPROVAL)
res2 = evaluate(ToolCall("file_writer", "write", path="/etc/hosts"), policy)
print(res2.decision)  # Decision.REQUIRE_APPROVAL
```

---

## 3. 核心功能與特性

1. **路徑與目標正規化**：自動處理跨平台路徑（Windows 反斜線 / POSIX 斜線），解析真實相對位置，防止 `../` 目錄遍歷攻擊。
2. **純決定論評估 (Deterministic Core)**：零 LLM 調用、零網路依賴，執行時間小於 5 毫秒。
3. **Fail-Closed 預設防護**：遇到未知副作用 (Unknown Side-Effect) 或未定義工具時，一律預設為拒絕 (`deny`) 或降級為需審查 (`require_approval`)。
4. **脫敏稽核日誌 (Audit Log)**：輸出 JSONL 結構化稽核事件，對機敏參數進行雜湊指紋化，絕不留存明文金鑰。

---

## 4. 本地重現與跨平台 CI 驗證

```bash
# 執行 24 項單元測試 (零外部套件，標準庫即可跑)
PYTHONPATH=src python -m unittest discover -s tests -v
```

### 跨平台矩陣驗證 (6/6 全數 PASS)
- **Ubuntu** (Python 3.11 / 3.12)：PASS
- **macOS** (Python 3.11 / 3.12)：PASS
- **Windows** (Python 3.11 / 3.12)：PASS

---

## 5. 展示邊界說明
- 本專案定位為「工具調用前置決策核心 (Preflight Policy Engine)」，非全域攔截的作業系統沙盒 (Sandbox) 或獨立 Gateway 服務。
