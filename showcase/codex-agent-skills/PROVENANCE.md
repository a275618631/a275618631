# Provenance & Verification Boundary｜Codex Agent Skills

- **專案代號**：`codex-agent-skills`
- **原始來源**：GitHub 公開倉庫 [`a275618631/codex-agent-skills`](https://github.com/a275618631/codex-agent-skills)
- **來源 Commit SHA**：`2fa26a5bc05ef1331478e3329fd1a93b1972d691`
- **同步日期**：2026-10-28
- **同步方式**：公開倉庫 Commit-pinned 快照鏡像（排除 `.git` 歷史）

---

## 驗證證據狀態 (Evidence Status)

- **Skill 格式驗證器 (`scripts/validate.ps1`)**：**PASS**
  - 驗證包含 YAML frontmatter、結構化命名、必要標籤與安全宣告。
- **標準技能庫 (Standard Skills)**：
  - `output-contract`：任務交付物格式標準化與清單合約。
  - `portable-tool-delivery`：跨平台與受限 IT 環境工具可攜性設計。
  - `pr-review-agent`：資安優先、缺陷導向之 PR 審查規格。
  - `preventive-repair`：系統預防性修復與回歸保護。
  - `workflow-automation-agent`：通用工作流程自動化與審核規範。

---

## 與文件工作流的規範整合

本子專案作為**共用技能庫與驗證標準**，與 `showcase/manufacturing-document-workflow/` 共享相同的技能設計原則：
1. **單一規範源 (Single Normative Source)**：所有 Skill 均遵循 `SKILL.md` 規範與 `validate.ps1` 自動檢驗。
2. **安全邊界先決**：每個技能均包含明確的「停止條件」與「未驗證邊界」，禁止在缺乏環境授權時進行越權推論。
