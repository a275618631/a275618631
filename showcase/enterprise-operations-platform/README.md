# A｜Enterprise Operations Platform

This is the development entry for project A. Work only inside:

`<LOCAL_WORKSPACE_PATH>`

The private GitHub repository [`a275618631/enterprise-operations-platform`](https://github.com/a275618631/enterprise-operations-platform) has been created. The approved development branch is `codex/docs-entry-20261019`; it is published separately and has not been merged into `main`.

## Purpose and MVP

Status as of 2026-10-27: the local MVP has a test-backed JWT authentication/RBAC slice, Development-only Demo login, one-click local startup, equipment creation, and work-order operations. It is still a local development MVP, not production acceptance.

Build a local enterprise operations platform for equipment and work-order operations.

The current MVP is a small, independently runnable vertical slice:

- ASP.NET Core 10 REST API on `127.0.0.1:5080`.
- Vue 3 + TypeScript client on the Vite development port.
- PostgreSQL 18.6 persistence owned only by A.
- Equipment listing and creation, plus work-order listing, creation, and completion.
- JWT Bearer validation with role-based read, write, and completion policies.
- Development-only Demo login that issues short-lived JWTs for synthetic roles.
- Vue token-connect flow with explicit `401` and `403` error states.
- EF Core migration `20261019031222_InitialOperationsSchema`.
- In-memory fallback for API development when no local connection secret is configured.
- Loopback-only PostgreSQL backup, restore, and synthetic restore-database helpers.

## Start here

1. Read [AGENTS.md](AGENTS.md) for write scope, safety boundaries, and secrets rules.
2. Read [PROJECT.yaml](PROJECT.yaml) for identity, ownership, and source-of-truth status.
3. Read [docs/ARCHITECTURE_MVP_20261016.md](docs/ARCHITECTURE_MVP_20261016.md) for the current architecture contract.
4. Read [frontend/README.md](frontend/README.md) and [frontend/UX_MVP_20261019.md](frontend/UX_MVP_20261019.md) for the user-visible UI flow.

## Local development flow

Configure the database password through the local User Secrets helper; never place it in Git:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\set-local-connection.ps1
```

Configure the JWT validation settings through User Secrets; the signing key must be at least 32 UTF-8 bytes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\set-local-jwt.ps1
```

Start the API:

```powershell
dotnet run --project .\src\EnterpriseOperationsPlatform.Api\EnterpriseOperationsPlatform.Api.csproj --urls http://127.0.0.1:5080
```

Start the Vue client in a second terminal:

```powershell
cd .\frontend
npm install
npm run dev -- --host 127.0.0.1
```

For a local Demo, the recommended one-click path is:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-local-demo.ps1
```

The launcher starts the API and Vue dev server, waits for `/health` and port `5173`, then opens the browser. Stop it with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-local-demo.ps1
```

Use the UI to view equipment, add a synthetic equipment record, create a work order for it, and complete the order. The UI calls the local API only; an unavailable B, C, REST integration, or MCP integration must not prevent the core local workflow.

The Development environment issues short-lived Demo JWTs. Synthetic Demo accounts are:

| Account | Password | Role |
|---|---|---|
| `viewer` | `viewer-demo` | Read only |
| `operator` | `operator-demo` | Read; create equipment and work orders |
| `supervisor` | `supervisor-demo` | Read; create equipment and work orders; complete work orders |
| `administrator` | `administrator-demo` | Full MVP operations |

These credentials are synthetic local Demo data and must not be reused in production. The current MVP still does not provide a production login/user-management service; an approved local issuer can also be used by pasting a valid JWT into the Vue connection box. The token role policies are:

| Operation | Allowed roles |
|---|---|
| Read equipment and work orders | `Viewer`, `Operator`, `Supervisor`, `Administrator` |
| Create equipment and work orders | `Operator`, `Supervisor`, `Administrator` |
| Complete work orders | `Supervisor`, `Administrator` |

Without a valid token, operations endpoints return `401`; with an authenticated but insufficient role, they return `403`.

For the local recovery drill, first run `scripts/bootstrap-recovery-postgresql.psql` as the PostgreSQL administrator against the loopback server, then use `scripts/backup-postgresql.ps1` and `scripts/restore-postgresql.ps1`. Restore requires `-ConfirmRestore` and a target database matching `enterprise_operations_restore_*`.

For the repeatable QA-01 acceptance, run `pwsh -ExecutionPolicy Bypass -File .\scripts\qa-01.ps1`. It requires the existing local User Secrets DB/JWT settings, PostgreSQL 18 client tools, Node dependencies, and local Chrome. It creates a unique `qa01_<run>` schema inside `enterprise_operations_restore_smoke`; migrations, API traffic, schema-scoped backup, and restore are confined to that schema. The runner never uses `enterprise_operations` as a connection target, never clears the existing `public` schema, and leaves the QA schema and evidence under `artifacts/` for inspection. The password stays in User Secrets and is passed to backup/restore as a short-lived process environment value; it is never printed or written to test evidence. The latest reproducible acceptance and evidence index are in [the QA-01 report](docs/A_QA-01_repeatable_demo_acceptance_2026-10-22.md).

## Evidence already completed

- `dotnet test EnterpriseOperationsPlatform.slnx --no-restore --configuration Release`: 22 passed; 1 PostgreSQL-only test intentionally skipped outside the dedicated QA runner.
- `dotnet build EnterpriseOperationsPlatform.slnx`: 0 warnings, 0 errors.
- `npm run build` in `frontend`: passed.
- Equipment create API: anonymous `401`, Viewer `403`, invalid fields `400`, duplicate ID `409`, Operator create `201`; created equipment can be used for a work order.
- QA-01 post-commit run `7d7cc605a2964c13be325b51456778d1`: full browser role flow, Viewer and Operator 320px no-overflow checks, PostgreSQL restart persistence, schema-scoped backup/restore digest, and snapshot boundary passed. Evidence: [QA-01 report](docs/A_QA-01_repeatable_demo_acceptance_2026-10-22.md).
- One-click local Demo start/stop: passed; API and Vue ports were cleaned up after verification.
- PostgreSQL application role is non-superuser; password remains in User Secrets.

## Next work: portfolio flow first

Follow [the dated A portfolio roadmap](docs/PORTFOLIO_ROADMAP_20261021.md). UX-01/02 and QA-01 are complete. M1-REM is in progress: equipment creation is complete; next finish work-order assignment/lifecycle and API contract/OpenAPI evidence. Then continue the original M2 integration demo and portfolio evidence. Formal identity, governance, CI, and deployment remain later stages; the local MVP is not production acceptance.

## Non-goals and forbidden actions

- Do not change remotes, merge, or deploy without explicit approval. Use a scoped feature branch and PR for approved GitHub updates.
- Do not modify B or C, their worktrees, Docker resources, or `factory-qdrant-data`.
- Do not commit secrets or local `.env` values.
- T7 OS-level Agent write isolation is not complete; unattended cross-project writes remain forbidden.

## Document disposition

| Class | A evidence / location | Status |
|---|---|---|
| Current | This README, `AGENTS.md`, `PROJECT.yaml`, `src/`, `frontend/`, `tests/`, `docs/ARCHITECTURE_MVP_20261016.md` | Local source of truth |
| Reference | Drive folder `1xeINSPoAKovaFh3buicYS5aPB7PAlihQ` | User-provided reference; not independently read by this checkout |
| Archive | No separate archived A copy identified in this Repo | UNKNOWN; do not infer from filenames |
| Duplicate candidate | None classified | Requires provenance review before any consolidation |
