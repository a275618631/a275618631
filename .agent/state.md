[SUMMARY]
- 主導：Codex；registry contract 與既有作品去名由兩位 Luna workers 各自獨立 write-set 執行。
- 工單：PORT-LOCAL-20261111；P00–P08 實作中，最終驗收與交付準備階段。
- 最後完成：Playwright Chromium 實際驗收通過；29 項單元測試通過（另補 A07／A14 覆蓋後待最終重跑）；全 repo 私有出版審計通過。
- 目前停在：已完成 registry／CLI／build／UI／server／publication／文件；接受紀錄已更新，分支仍在 `codex/portfolio-local-hub-20261111`。
- 卡點／下一步：此 checkout 的 ignored `.local/dist` 有不可讀且未辨識的既有輸出，禁止覆蓋；改在乾淨 staging checkout 驗證預設 build，之後提交並推 PR／更新既有 Issue #2。

[ACTIVE_TICKET_SPEC]
- Target：`a275618631/a275618631`，remote `https://github.com/a275618631/a275618631.git`；只改 hub repo，不改來源專案 runtime。
- Base：`308063538eaec8df533416b3972039551f04677d`；PR #12 docs-only／open，新增首頁程式不等待其合併。
- Branch：`codex/portfolio-local-hub-20261111`；primary writer Codex；worker write-set 見工作交辦。
- Public SSOT：`portfolio/projects.json`；local-only overlay `.local/projects.local.json`，public mode 永不載入。
- Fixed CLI：`python portfolio/hub.py`；Python stdlib runtime；Playwright 1.64.1 僅供 dev/browser test。
- 固定九個公開 ID：八個 showcase + `ai-folder-governance`；不含 NPI；禁止求職／指定雇主語境。
- 四種 link：revision-pinned HTTPS repo、allowlisted static_bundle、loopback-only local_http overlay、HTTPS external。
- 不啟動／代理來源 app；不共享 DB／secret；不部署／開 tunnel；外部 Demo 可選且故障不影響首頁。
- Public/local outputs：`.local/dist/public/` 與 `.local/dist/local/`；path 僅接受受控輸出目錄，失敗保留前版。
- Static public output：相對路徑、hash routes、資料驅動、JS 關閉時仍有可讀內容、無 CDN／tracking。
- Local server：只綁 `127.0.0.1`；預設 8765，依序 fallback；只提供產物，拒絕 traversal／symlink／dotfile。
- CLI needs doctor、validate、build、upsert、import-bundle、audit、serve、verify-links；錯誤碼依工單 §6。
- New project/function/link must be data-only; stable slug; planned/partial/implemented visible; exact examples and dry-run.
- Static bundle import only `.local/imports/<id>/<revision>/` allowlist; <=500 files and <=50 MiB; checksums and no symlinks.
- Company rules real/private in ignored `.local/company-rules.json`; committed fixture uses synthetic sentinels only.
- Required security: escaped text, safe URLs, strict local/public projection, deterministic manifest, atomic writes, preserve unknown output.
- Browser E2E covers 390px/1440px, keyboard, unknown route, reload, no-JS, no external network, root/subpath.
- Required final commands follow formal work order §10; each run records actual exit status, no historical CI substituted.
- DoD: P00–P08 and A01–A20 evidence, clean staging public build, Windows live URL/browser evidence, audit and byte asset ledger.
- No `LOCAL_COMPLETE` unless every hard gate is PASS; browser restriction means `BLOCKED_E2E`, otherwise incomplete is `PARTIAL`.
- Stage precise files only; do not add `.local`, raw company dictionary, venv, logs, screenshots with private paths, or unrelated files.
- Complete local commit on authorized branch; remote PR may be prepared under existing explicit push authorization; never auto-merge/deploy.
