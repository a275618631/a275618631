# Local Acceptance Ledger — 2026-11-12

**Work order:** PORT-LOCAL-20261111
**Base:** `308063538eaec8df533416b3972039551f04677d`
**Branch:** `codex/portfolio-local-hub-20261111`
**Status:** IN_PROGRESS — do not label `LOCAL_COMPLETE` until every required acceptance row has runtime or browser evidence.

## Required scenario ledger

| ID | Scope | Evidence / test | Result |
|---|---|---|---|
| A01 | Nine initial projects, no source services | `test_initial_registry_has_exact_nine_stable_projects`; Chromium renders nine registry entries plus a separate synthetic extension fixture | PASS |
| A02 | Add new slug/category/tag as data only | `test_data_only_project_and_feature_changes_do_not_touch_ui_code` | PASS |
| A03 | Update feature/title/revision without changing ID | `test_data_only_project_and_feature_changes_do_not_touch_ui_code`; stable ID remains required | PASS |
| A04 | Planned state and no Demo do not imply ready | extension fixture preserves `planned`; static demo fixture is independently labeled synthetic | PASS |
| A05 | Local binding does not cause health probes; app may stop | Chromium binds a deliberate dead port and confirms no automatic request; server listener shutdown is exercised | PASS |
| A06 | Allowlisted HTML/CSS/JS bundle at root/subpath | `test_bundle_import_dry_run_real_import_idempotency_and_checksum`; Chromium opens and interacts with bundle at root and nested path | PASS |
| A07 | Expired/unavailable external link does not break offline output | `test_expired_https_link_is_inert_and_offline_build_succeeds` | PASS |
| A08 | Public output ignores corrupt/sentinel overlay byte-for-byte | `test_public_build_never_reads_or_leaks_overlay`; public validate is offline | PASS |
| A09 | HTML-like plain text is displayed as text | Chromium injects markup-shaped title and confirms literal text with no created element | PASS |
| A10 | Unsafe schemes, credentials, CRLF and sensitive queries rejected | `test_url_and_bundle_boundaries`; `test_short_sha_unknown_schema_and_control_text_rejected` | PASS |
| A11 | Encoded traversal and symlink/junction escape rejected | `test_url_and_bundle_boundaries`; `test_traversal_double_encoding_dotfiles_and_unknown_paths_are_rejected`; root symlink test; path guards include Windows junction checks | PASS |
| A12 | Unknown existing output and dangerous output paths preserved/rejected | `test_unknown_existing_file_and_root_output_are_preserved` | PASS |
| A13 | Duplicate IDs, short SHA, invalid dates and unknown schema rejected | `test_duplicate_project_capability_and_link_ids_are_rejected`; `test_short_sha_unknown_schema_and_control_text_rejected` | PASS |
| A14 | Synthetic company sentinel in text/URL/meta/filename detected | Publication scanner covers normalized path and text content; synthetic fixture audit and private all-scope audit | PASS |
| A15 | Occupied default port uses reported fallback, never kills listener | `test_occupied_port_uses_fallback_without_terminating_listener` | PASS |
| A16 | Keyboard, no-JS, 390/1440 widths, unknown route, F5 | Chromium acceptance; screenshots stored only in ignored `.local/evidence/` | PASS |
| A17 | Repeated offline build has identical digest and no absolute paths | `test_public_build_is_deterministic_and_has_static_fallback`; projection tests ensure source paths are stripped | PASS |
| A18 | Clean export builds without `.local` or source checkout imports | Fresh clean staging validation and build | PENDING |
| A19 | Local-only project is absent from all public files | `test_local_only_project_never_enters_public_output`; `test_public_projection_strips_local_http_links` | PASS |
| A20 | Pinned snapshot remains unchanged when source branches move | `test_all_initial_repo_links_pin_full_sha` checks full immutable commit references | PASS |

## Commands and evidence

Final commands are recorded after execution below with actual exit status and full local commit SHA. Do not infer pass from a test name, static inspection or historical source CI.

| Command / operation | Exit / evidence |
|---|---|
| `python portfolio/hub.py doctor --json` | PASS, exit 0; Python 3.14.10, supported, required files present |
| `python -m unittest discover -s portfolio/tests -p "test_*.py" -q` | PASS, 31 tests, 1 Windows symlink capability skip, exit 0 |
| Public/local validate and build | Validate PASS / exit 0, 9 entries each. Build retry pending in clean staging because this worktree's ignored `.local/dist` has an inaccessible unrecognized prior output. |
| Synthetic artifact audit / private all-scope audit | Private audit PASS, 322 paths scanned, no findings, nine exact path+SHA classified synthetic credential-redaction inputs; 14 baseline binary assets inventoried. Artifact audit against a populated clean build is pending with A18. |
| Browser at 1440×1000 and 390×844 | Chromium PASS, exit 0; 1440×1000, 390×844, A05/A06/A09, no-JS, reload, unknown route, no external network. |
| Clean staging public build | PENDING |
| Git diff check and staged allowlist | `git diff --check` PASS, exit 0; precise staging audit pending. |

## Security and content review

- Private company rules and local overlay are ignored under `.local/`; public fixture contains only synthetic terms.
- Public binaries are checked against the fixed base commit and current SHA-256 ledger; any changed asset requires fresh review.
- The known company mention in the synthetic RAG walkthrough is replaced with Company A. Remaining repository and external-page audit findings are recorded only with safe rule IDs and paths; no private dictionary is committed.
- PR #12 remains a separate open documentation PR. This implementation adds app functionality and a minimal README link without rewriting its descriptions.
