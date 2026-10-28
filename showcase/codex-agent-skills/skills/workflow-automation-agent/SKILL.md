---
name: workflow-automation-agent
description: Use when converting a repeatable process into an automation with explicit approvals, failure handling, and auditability; do not use to automate high-impact actions without a human gate.
---

# Workflow Automation Agent / 工作流程自動化 Agent

## Purpose / 目的

Turn a repeatable process into a controlled workflow. Make the trigger, inputs, tools, outputs, approvals, failure branches, audit trail, and success metrics explicit before implementation.

將可重複流程轉成受控工作流。在實作前明確定義觸發、輸入、工具、輸出、核准、失敗分支、稽核紀錄與成功指標。

## Design contract / 設計契約

Specify:

- trigger and idempotency key;
- input schema and validation rules;
- steps, dependencies, and side effects;
- human approval gates and least-privilege credentials;
- timeout, retry, compensation, and stop behavior;
- audit fields that exclude secrets;
- output schema and measurable success criteria.

必須指定：觸發與冪等鍵、輸入結構與驗證、步驟與副作用、人工核准與最小權限、逾時／重試／補償／停止行為、不含秘密的稽核欄位，以及輸出結構與可量測成功條件。

## Execution / 執行

1. Model the current manual flow and its exceptions.
2. Mark irreversible or externally visible actions.
3. Keep those actions behind explicit approval unless the user has separately authorized a safe policy.
4. Start in dry-run or sandbox mode.
5. Run representative success, duplicate, timeout, malformed-input, and permission-denied cases.
6. Publish the runbook and rollback path with the automation.

## Safety boundaries / 安全邊界

Do not bypass approval gates, conceal failures, broaden permissions, or write sensitive values to logs. If a required input or permission is missing, stop with an actionable blocker.

不得繞過核准、隱藏失敗、擴大權限或把敏感值寫入紀錄。缺少必要輸入或權限時，應明確停止並回報可行的解除阻礙方式。

## Output contract / 輸出契約

Return: workflow diagram or step list, input/output schema, approval points, failure matrix, audit plan, test evidence, and maintenance notes.

輸出應包含：工作流圖或步驟表、輸入／輸出結構、核准點、失敗矩陣、稽核計畫、測試證據與維護說明。
