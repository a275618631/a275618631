---
name: preventive-repair
description: Use when designing safeguards, failure handling, or recovery boundaries for a workflow or system; do not use for ordinary feature implementation without a material failure-risk question.
---

# Preventive Repair / 預防性修復

## Purpose / 目的

Design resilience before failure becomes an incident. Identify likely failure neighborhoods, choose the smallest effective guardrails, and make recovery behavior observable and bounded.

在故障變成事故前設計韌性。先找出失效鄰域，再選擇最小但有效的防護，並讓復原行為可觀測、有界線。

## Trigger / 觸發條件

Use this skill when the task involves reliability, repeated failures, partial outages, destructive operations, external dependencies, retries, timeouts, fallback behavior, or recovery planning.

當任務涉及可靠性、反覆故障、部分服務中斷、破壞性操作、外部依賴、重試、逾時、降級或復原規劃時使用。

Do not use it to add speculative complexity to a low-risk, deterministic change.

低風險且確定性的簡單修改，不應為了形式上的最佳實務套用複雜防護。

## Method / 方法

1. State the failure being prevented and the impact if it occurs.
2. Map the failure neighborhood: input, dependency, state, timing, concurrency, and operator error.
3. Select a defense: reject, normalize, validate, timeout, retry, circuit break, bulkhead, rate limit, fallback, or fail closed.
4. Define budgets: maximum retries, time, queue size, data loss, and operator effort.
5. Define telemetry: what is recorded, what is safe to record, and what should page a human.
6. Test the expected failure path and document the stop condition.

1. 說明要預防的故障，以及發生時的影響。
2. 盤點輸入、依賴、狀態、時間、並行與操作錯誤等失效鄰域。
3. 選擇防護：拒絕、正規化、驗證、逾時、重試、斷路、隔離、限流、降級或安全失敗。
4. 設定重試次數、時間、佇列、資料損失與人工處理成本上限。
5. 定義安全的遙測與需要人工介入的訊號。
6. 測試故障路徑並寫明停止條件。

## Safety boundaries / 安全邊界

- Never retry an operation that may duplicate an irreversible side effect unless idempotency is established.
- Never log secrets, credentials, cookies, or full private payloads.
- Do not silently continue after a validation failure when the result could be destructive or misleading.
- Require explicit human approval before production, deletion, credential, permission, or public-release actions.

## Output contract / 輸出契約

Return: failure statement, risk matrix, selected controls, budgets, observability plan, test evidence, and unresolved assumptions.

輸出應包含：故障描述、風險矩陣、防護選擇、各項上限、觀測計畫、測試證據與未解假設。
