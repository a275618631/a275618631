---
name: portable-tool-delivery
description: Use when delivering a script, tool, or workflow across computers, operating systems, or non-engineer environments; do not use for a single-machine developer-only change.
---

# Portable Tool Delivery / 可攜式工具交付

## Purpose / 目的

Make tools usable outside the developer's machine. Separate development assumptions from target-user reality, diagnose once, repair once, and provide a bounded fallback.

讓工具在開發者以外的電腦上也能使用。分離開發環境與目標環境，一次診斷、一次修復，並提供有界線的備援方案。

## Method / 方法

1. Define the target user, operating system, architecture, permissions, paths, input format, and success signal.
2. Provide a low-dependency diagnostic package that reports stable labels, not secrets or full environment dumps.
3. Collect all known blockers in one run: executable availability, write access, encoding, line endings, network, browser, Office, and path behavior as applicable.
4. Apply one focused repair and rerun the same validation.
5. If the result still fails, stop the same route and give a different Plan B with its trade-offs.
6. Handoff exact files, commands, expected output, failure interpretation, and rollback steps.

1. 定義目標使用者、作業系統、架構、權限、路徑、輸入格式與成功訊號。
2. 提供低依賴診斷包，只回報穩定標籤，不輸出秘密或完整環境內容。
3. 一次收集可預期的阻礙：程式、寫入權限、編碼、換行、網路、瀏覽器、Office 與路徑行為。
4. 執行一次聚焦修復，再跑同一份驗證。
5. 仍失敗時停止原路線，改提供不同底層邏輯的 Plan B 與取捨。
6. 交付精確檔案、命令、預期輸出、失敗解讀與回復方法。

## Bootstrap ladder / 啟動階梯

Prefer a native shell or self-contained executable. Treat optional PowerShell, Python, package managers, GUI automation, and network downloads as progressively higher-dependency fallbacks.

優先使用原生 Shell 或自包含執行檔；PowerShell、Python、套件管理器、GUI 自動化與網路下載應視為逐步增加依賴的備援。

## Safety boundaries / 安全邊界

- Do not request passwords, tokens, cookies, or private configuration.
- Do not write outside the declared target directory without approval.
- Default to dry-run for file moves, deletes, permission changes, and uploads.
- Never claim portability from a single-machine test; state the tested environment.

## Output contract / 輸出契約

Return: target profile, diagnostic command, repair command, validation command, expected success signal, failure branches, rollback, and maintenance owner.

輸出應包含：目標環境、診斷命令、修復命令、驗證命令、成功訊號、失敗分支、回復方式與維護責任人。
