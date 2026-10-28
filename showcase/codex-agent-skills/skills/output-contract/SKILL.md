---
name: output-contract
description: Use when a task must end with a verifiable handoff, report, release, or decision record; do not use to add ceremony to a trivial conversational answer.
---

# Output Contract / 交付契約

## Purpose / 目的

Make completion inspectable. A task is not complete merely because files changed; the recipient must know what changed, what was verified, what remains, and what could fail next.

讓完成狀態可檢查。任務不會因檔案改了就自動完成；接收者必須知道改了什麼、驗證了什麼、還剩什麼，以及下一步可能失敗在哪裡。

## Required sections / 必要段落

1. Status: complete, partial, blocked, or awaiting confirmation.
2. Changes: exact files, links, or external objects affected.
3. Verification: commands, tests, timestamps, and results.
4. Risks and limitations: what was not tested or cannot be guaranteed.
5. Follow-up: owner, next action, and trigger.
6. Rollback or recovery: how to undo or contain the change when relevant.

1. 狀態：完成、部分完成、受阻或等待確認。
2. 變更：受影響的精確檔案、連結或外部物件。
3. 驗證：命令、測試、時間與結果。
4. 風險與限制：未測試或無法保證的事項。
5. 後續：負責人、下一動作與觸發條件。
6. 回復或復原：必要時說明如何撤銷或隔離變更。

## Delivery rules / 交付規則

- Separate facts, inferences, recommendations, and user actions.
- Never replace missing verification with confident wording.
- Link to real artifacts and use stable names.
- Keep the summary short; put detailed evidence below it.
- If delivery is public, verify remote existence and visibility separately from content correctness.

## Output contract / 輸出格式

Use a short status-first summary followed by the six sections above. For blocked work, state the exact missing decision or permission and the safest next step.

採用先狀態、後細節的摘要，接著依序列出六個必要段落。受阻時，明確指出缺少的決策或權限，以及最安全的下一步。
