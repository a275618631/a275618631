# Codex Agent Skills

Reusable, safety-first skills for reliable agent work.

可重複使用、以安全為優先的 Agent Skills，協助代理人穩定完成分析、交付、自動化與審查工作。

[![Validate](https://github.com/a275618631/codex-agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/a275618631/codex-agent-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why this collection? / 為什麼是這套？

These skills turn common agent habits into explicit, reusable operating contracts:

- diagnose before repairing;
- keep risky actions behind approval gates;
- separate development context from target-user context;
- make outputs, evidence, and follow-up work explicit;
- stop safely when assumptions or validation fail.

這套技能把常見的 Agent 工作習慣整理成可重複使用的執行契約：先診斷再修復、敏感操作需要核准、開發環境與目標環境分離、交付必須帶證據，驗證失敗時安全停止。

## Skills / 技能目錄

| Skill | Best for / 適用情境 |
| --- | --- |
| [`preventive-repair`](skills/preventive-repair/SKILL.md) | Resilience, failure prevention, recovery boundaries / 預防性防護、失效隔離與復原邊界 |
| [`portable-tool-delivery`](skills/portable-tool-delivery/SKILL.md) | Cross-machine tools and non-engineer handoff / 跨電腦工具與非工程使用者交付 |
| [`workflow-automation-agent`](skills/workflow-automation-agent/SKILL.md) | Safe automation with approvals and auditability / 具核准與稽核能力的自動化 |
| [`pr-review-agent`](skills/pr-review-agent/SKILL.md) | Code review, regression, test and security findings / 程式碼、回歸、測試與安全審查 |
| [`output-contract`](skills/output-contract/SKILL.md) | Consistent completion reports and handoffs / 一致的完成報告與交接 |

## Quick start / 快速開始

Copy one skill directory into the skills directory supported by your agent runtime. Keep the directory name unchanged and review the skill's trigger description before enabling it.

將任一技能資料夾複製到你的 Agent 執行環境支援的 skills 目錄。請保留資料夾名稱，並在啟用前先閱讀該技能的觸發條件。

```text
skills/
└── preventive-repair/
    └── SKILL.md
```

No secrets, personal settings, credentials, or machine-specific backups belong in this repository.

本倉庫不應放入秘密、個人設定、憑證或特定電腦的備份。

## Validation / 驗證

The repository includes a dependency-free PowerShell validator:

```powershell
pwsh -NoProfile -File .\scripts\validate.ps1
```

它會檢查技能目錄名稱、`SKILL.md` front matter、必要標題，以及常見個人資料與秘密檔案模式。

## Contributing / 參與貢獻

Please read [CONTRIBUTING.md](CONTRIBUTING.md). New skills should be self-contained, bilingual where practical, explicit about safety boundaries, and testable without private infrastructure.

請先閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。新增技能應自包含、盡可能提供中英文說明、明確定義安全邊界，並能在不依賴私人基礎設施的情況下驗證。

## Security / 安全性

Please report suspected vulnerabilities privately according to [SECURITY.md](SECURITY.md). Never open an issue containing credentials, tokens, cookies, or private configuration.

若發現疑似安全問題，請依 [SECURITY.md](SECURITY.md) 私下回報。不要在 Issue 放入憑證、Token、Cookie 或私人設定。

## License / 授權

MIT © 2026 a275618631
