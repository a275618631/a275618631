# Che-Yu Wu

**製造業 × AI 系統整合與 Agent 架構 · Multi-Agent Systems · 企業營運與可驗證工程**

我專注於把模糊、複雜的實際需求，轉換成可維護、可測試、可驗證的 AI 輔助系統與 Agentic Systems（Agent 型系統）。

目前主要關注：

- AI Agent 架構與 Multi-Agent Systems（多 Agent 系統）
- Agent Runtime（Agent 執行環境）、Tool、Skill 與 MCP 整合
- 跨平台系統整合與自動化
- Human-in-the-loop（人工介入）與安全邊界
- Requirements → Architecture → Implementation → Validation
- Local / Cloud（本地／雲端）任務與隱私分流
- Verification-driven Engineering（驗證導向工程）

我的設計原則是：**優先使用平台原生能力，避免沒有必要的 Framework 與基礎設施；架構複雜度必須由實際需求證明。**

→ **[Codex × Antigravity 協作架構網站（繁體中文）](https://a275618631.github.io/codex-antigravity-collaboration/)**

---

## 主要能力方向

### AI Agent Architecture
設計 Agent Runtime、角色分工、跨 Runtime 委派、工具與權限邊界，以及不同 AI 平台之間的協作方式。

### Multi-Agent Systems
不是單純增加更多 Agent，而是處理：

- 誰負責什麼工作
- 哪些工作可以平行
- 哪些寫入不能互相衝突
- Agent 之間如何交接 Context（上下文）
- 如何限制遞迴委派
- 如何驗證彼此的結果

### System Integration
將 AI 能力整合進既有程式庫、工具、工作流程、瀏覽器、Google 生態與本地環境，而不是建立彼此孤立的 Demo。

### Safety & Verification
關注：

- 權限與 Approval（核准）邊界
- Secret / PII（敏感資訊）保護
- Human-in-the-loop
- Regression Tests（回歸測試）
- Evidence-based Validation（證據導向驗證）
- 明確區分「已實作、部分完成、規劃中、探索中」

---

# Featured Projects｜主要作品

## ★ [公開技術能力作品集 (Engineering Capabilities Showcase)](showcase/)

Manufacturing AI · Grounded RAG · Agent Policy · Enterprise Platform · Multi-Agent Runtime

具備製造業現場經驗，專注將現場製程文件、設備手冊知識與營運工單流程，落地為高可靠、具備安全防護與可驗證的 AI Agent 與企業系統：

### 四大核心專案
1. **[工廠設備知識庫與地端診斷 RAG](showcase/factory-knowledge-grounded-rag/)**：離線混合檢索 (Qdrant+BM25)、手冊 Citation 與「查無證據即拒答 (ABSTAIN)」5 道檢查閘門（25 題基準測試 100% 安全合規）。
2. **[製程文件版本審核與 AI 工作流](showcase/manufacturing-document-workflow/)**：受限推理環境 (Claude Free) 之結構化 Skill 約束，實測成功阻絕跨客戶越權存取（T1 格式通過；T2 原版完整性不足，修正後重測通過；T3 依賴查核通過）。
3. **[企業營運平台垂直切片](showcase/enterprise-operations-platform/)**：ASP.NET Core 10 (.NET 10) 後端架構，RBAC 權限狀態機與工單冪等防護（22/22 項測試 PASS）。
4. **[Agent 工具策略引擎](showcase/agent-tool-policy-engine/)**：純 Python 零依賴，決定論工具調用風險預檢與 Fail-Closed 防護（24/24 項測試 PASS）。

### 延伸實作與架構
- **[Codex × Antigravity 協作架構](showcase/codex-antigravity-collaboration/)**：異質 Agent 跨 Runtime 協議與 Local Bridge 檔案鎖。
- **[LINE Portable Core 通訊核心](showcase/line-portable-core/)**：HMAC-SHA256 簽名驗證、Webhook 冪等去重與 LIFF 狀態容錯（16 項測試 PASS）。
- **[Paperclip AI Chief 部署設計與本機驗證](showcase/paperclip-ai-chief/)**：以 NT 增額月費為目標之任務閉環、Codex Heartbeat 巡查與 ARM64 部署規格。
- **[可攜式 AI Agent 環境](https://github.com/a275618631/portable-ai-agent-environment)**｜**[製造業智慧排班設計](https://github.com/a275618631/workforce-scheduling-system)**｜**[html2slides](https://github.com/a275618631/html2slides)**｜**[Codex Agent Skills](https://github.com/a275618631/codex-agent-skills)**

→ **[瀏覽作品集展示與驗證索引 (showcase/README.md)](showcase/)**

---

## 其他獨立開源專案 (Related Repositories)

- **[Codex × Antigravity 協作架構](https://github.com/a275618631/codex-antigravity-collaboration)**：以 Codex 與 Antigravity 為實際案例的 AI Agent 跨 Runtime 邊界協作參考架構。
- **[可攜式 AI Agent 環境](https://github.com/a275618631/portable-ai-agent-environment)**：私有版在 Windows／macOS 使用；公開版提供 Bash 暫存檔敏感資料掃描器與回歸測試。
- **[製造業智慧排班系統設計](https://github.com/a275618631/workforce-scheduling-system)**：私有版累積 56 項約束求解器自動化測試；公開版提供輪班規格設計與法規約束模型案例研究。
- **[html2slides 投影片轉換工具](https://github.com/a275618631/html2slides)**：將 HTML 投影片轉換為可編輯 PowerPoint (.pptx) 與 Google Slides 的轉換工具。
- **[Codex Agent Skills 技能庫](https://github.com/a275618631/codex-agent-skills)**：雙語、Safety-first 的 Agent Skill 定義規範與格式防護驗證腳本。

---

# Selected Engineering Work｜其他工程實作

## Authenticated Desktop Media Workflow *(private implementation)*

`Tauri · Rust · TypeScript · FFmpeg · Integration`

macOS 桌面端媒體處理 Workflow，主要研究：

- 安全保存登入 Session
- macOS Keychain
- yt-dlp 整合
- HLS / fMP4 解析
- FFmpeg 處理
- Atomic File Move（原子式檔案搬移）
- Authentication → Extraction → Download 的 End-to-End（端到端）驗證

這項實作主要展示：

> **桌面應用、第三方工具整合、登入狀態管理與可靠性設計。**

僅設計用於使用者有權存取的媒體流程。

→ [Case Study](projects/authenticated-desktop-media-workflow.md)

---

# Prototype / Exploration｜原型與研究

## Privacy-Aware Meeting Intelligence Workflow
*Prototype / Partially Validated MVP*

`AI Workflow · Privacy · Human-in-the-loop · Evidence`

隱私導向的會議資訊處理 Pipeline：

`逐字稿 → PII 遮蔽 → LLM 摘要 → 決策／行動項目 → 證據追蹤 → 人工 Review`

目前已實作並在本地驗證：

- Transcript processing（逐字稿處理）
- PII masking（敏感資訊遮蔽）
- Structured output（結構化輸出）
- Evidence validation（證據驗證）

尚未完整驗證：

`真實 MP4 → STT → Speaker Diarization → External LLM`

完整 End-to-End Pipeline 目前仍屬於設計階段，因此不宣稱已完成正式驗證。

---

# Reusable Components｜可重複使用元件

- **[codex-agent-skills](https://github.com/a275618631/codex-agent-skills)**  
  雙語、Safety-first（安全優先）的 Agent Skill Library，涵蓋交付、自動化、驗證與 Review Workflow。
