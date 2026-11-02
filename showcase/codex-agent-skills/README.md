# Codex Agent Skills｜可重用的工程工作方法

排錯、程式審查、流程自動化與交付，都有可以反覆使用的工作步驟。我把常見的工程方法整理成五個 Agent Skills，讓不同專案不用從零描述整套流程。

## 五個 Skill

| 技能 | 主要用途 |
| --- | --- |
| [preventive-repair](skills/preventive-repair/SKILL.md) | 先釐清問題、影響範圍和復原方式，再決定如何修復 |
| [portable-tool-delivery](skills/portable-tool-delivery/SKILL.md) | 將工具交到不同電腦或使用者手上時，檢查安裝、環境與交付 |
| [workflow-automation-agent](skills/workflow-automation-agent/SKILL.md) | 把人工流程拆成事件、檢查、核准與復原步驟 |
| [pr-review-agent](skills/pr-review-agent/SKILL.md) | 檢查變更、回歸、安全與測試缺口 |
| [output-contract](skills/output-contract/SKILL.md) | 留下可驗證的修改結果和下一步 |

## 怎麼開始

點開需要的 `SKILL.md`，讀取適用條件與工作方法，再依 Agent 平台規則安裝整個 Skill 資料夾。

本展示保留了[格式驗證器](scripts/validate.ps1)，可在 PowerShell 7 執行：

```powershell
pwsh -NoProfile -File .\scripts\validate.ps1
```

完整版本與更新紀錄見 [codex-agent-skills 獨立公開倉](https://github.com/a275618631/codex-agent-skills)。
