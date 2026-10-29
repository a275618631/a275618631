# Codex Agent Skills｜常用工程工作流程

有些工程工作會一直重複：排查問題、規劃自動化、審查 PR、整理交付結果。每次從頭描述做法，不只浪費時間，也容易漏掉關鍵步驟。

我把這些工作整理成可重複使用的 Agent Skills。每個 Skill 都有適用時機、工作步驟和預期輸出，方便帶到不同專案使用。

## 技能一覽

| Skill | 主要用途 |
| --- | --- |
| [preventive-repair](skills/preventive-repair/SKILL.md) | 先確認問題與影響範圍，再提出修復和預防措施 |
| [portable-tool-delivery](skills/portable-tool-delivery/SKILL.md) | 整理跨電腦使用工具時的安裝、設定與交付方式 |
| [workflow-automation-agent](skills/workflow-automation-agent/SKILL.md) | 把人工流程整理成可執行步驟，處理核准、重複事件與失敗復原 |
| [pr-review-agent](skills/pr-review-agent/SKILL.md) | 審查程式變更、測試覆蓋與可能的回歸問題 |
| [output-contract](skills/output-contract/SKILL.md) | 讓完成報告包含修改內容、測試結果、風險與後續工作 |

## 怎麼使用

例如要自動處理新進文件，可以先使用 `workflow-automation-agent` 定義事件來源、輸入資料、審核節點和失敗時的處理方式。若要檢查這項自動化的程式碼，則交給 `pr-review-agent` 依照變更範圍與測試證據審查。

把需要的技能資料夾複製到 Agent 執行環境支援的 Skills 位置，再依平台規則啟用即可。目錄結構以每個資料夾的 `SKILL.md` 為入口。

## 格式驗證

提供 [PowerShell 驗證器](scripts/validate.ps1)，檢查 Skill 結構、必要欄位及常見敏感資訊模式。

```powershell
pwsh -NoProfile -File .\scripts\validate.ps1
```

完整技能庫也保留在 [codex-agent-skills 獨立專案](https://github.com/a275618631/codex-agent-skills)。可直接從上方的技能檔案閱讀每項流程。
