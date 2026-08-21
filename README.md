# Che-Yu Wu
**AI Agent 架構 · Multi-Agent Systems（多 Agent 系統）· 系統整合 · 自動化**
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

## 1. [Codex × Antigravity Collaboration](https://github.com/a275618631/codex-antigravity-collaboration)

`Agent Architecture · Multi-Agent · MCP · Skills · Privacy · Verification`

一套以 **Codex 與 Antigravity 為實際案例**的 AI Agent 協作參考架構。

核心問題不是「如何再做一套 Agent Framework」，而是：

> **既然 Codex、Antigravity 本身已經具備 Agent Runtime 與 Multi-Agent 能力，要如何用最少額外基礎設施，讓不同 Runtime 分工、互相委派、共享能力並維持安全邊界？**

目前架構涵蓋：

- **Native Multi-Agent Runtime**  
  優先使用 Codex、Antigravity 原生的 Agent / Subagent 能力，不重新製作 Agent Scheduler（排程器）。

- **Cross-runtime Delegation（跨 Runtime 委派）**  
  Codex 與 Antigravity 可以交換任務與結果，同時限制跨平台遞迴轉交。

- **Capability-aware Routing（依能力分工）**  
  根據工具、Runtime、資料敏感度與任務類型分配工作，而不是讓所有 Agent 重複做同一件事。

- **Shared Skills（共用技能）**  
  採用單一能力來源與薄平台 Adapter（轉接層），降低跨平台重複維護。

- **Git-based Write Ownership（Git 寫入所有權）**  
  使用 branch / worktree（分支／獨立工作區）、optimistic concurrency（樂觀式併發控制）與 PR / Review / Merge 管理平行修改，而不是自行建立分散式鎖服務。

- **Privacy-aware Routing（隱私感知分流）**  
  規劃本地模型、敏感資料分類、最小化與可逆假名化，讓不同資料依信任等級選擇 Local / Cloud 執行環境。

- **Verification & Status Boundaries（驗證與狀態邊界）**  
  清楚區分 Implemented、Partial、Planned、Exploratory，不把 Roadmap 當成已完成功能。

這個專案主要展示的是：

> **AI Agent 系統的架構取捨、Runtime 邊界、協作方式、安全設計與可維護性，而不是單純串接更多 AI 工具。**

→ **[架構網站（繁體中文）](https://a275618631.github.io/codex-antigravity-collaboration/)**  
→ [GitHub Repository](https://github.com/a275618631/codex-antigravity-collaboration)

---

## 2. [Portable AI Agent Engineering Environment](https://github.com/a275618631/portable-ai-agent-environment)

`AI Agents · System Architecture · Security · Cross-platform`

解決「AI Agent 開發環境如何安全地跨電腦移轉」的問題。

直接複製整個 Agent 環境，可能同時複製：

- Session state（登入狀態）
- Credentials（憑證）
- Machine identity（機器識別資訊）
- 私人設定與不應移轉的資料

此專案建立：

- 可攜與不可攜設定邊界
- Multi-Agent 職責分離
- Fail-closed Secret Scanning（失敗即拒絕的敏感資訊掃描）
- 跨平台設定同步策略
- Targeted Regression Tests（針對性回歸測試）

已在 Windows 與 macOS 環境進行跨平台驗證。

這個作品主要展示：

> **AI Agent 環境的安全邊界、可攜性設計與驗證方法。**

→ [Case Study](https://github.com/a275618631/portable-ai-agent-environment/blob/main/docs/case-study.md)

---

## 3. [Constraint-Based Workforce Scheduling System](https://github.com/a275618631/workforce-scheduling-system)

`System Analysis · Rule Engine · Scheduling · Validation`

將複雜的輪班規則與實際營運限制，轉換成結構化的排班系統。

涵蓋：

- 人員與班組管理
- 輪班規則
- Locked / Manual Duty（鎖定／人工指定班次）
- 違規與警告狀態
- 行事曆與月份檢視
- 規則迭代與驗證
- 自動化測試

私人實作版本目前累積 **56 個已驗證自動化測試案例**。

此專案主要展示：

> **如何把複雜、模糊的營運需求轉換成 Rule Model（規則模型）、系統架構與可驗證軟體。**

原始案例來自輪班型公共部門情境；公開版本使用匿名化與合成資料。

→ [Case Study](https://github.com/a275618631/workforce-scheduling-system/blob/main/docs/case-study.md)

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
