# Enterprise Operations Platform — MVP Architecture Contract (2026-10-16)

## Status

This is the local architecture contract for the A MVP. The current implementation includes an ASP.NET Core 10 API, Vue 3 client, PostgreSQL 18 persistence, EF migration, and local test evidence. It is not production acceptance. The remote repository is still not created; Docker remains optional and is not required for the local MVP.

## Boundaries

- Backend: C# 14 / ASP.NET Core 10 modular monolith.
- Frontend: Vue 3, served as an independently buildable client.
- Database: PostgreSQL 18 owned only by project A.
- Integration: authorized REST API or MCP adapters only.
- Degraded mode: core business workflows must remain operable when external APIs, MCP servers, B, or C are unavailable.

## Proposed module layout

```text
src/EnterpriseOperationsPlatform.Api/
  Program.cs
  Data/OperationsDbContext.cs
  Data/Migrations/
  Operations/OperationsStore.cs
frontend/
tests/EnterpriseOperationsPlatform.Api.Tests/
docs/
```

The current tree above is the implemented MVP slice. Do not create a second orchestrator or framework for isolation.

## Dependency rules

1. Domain code has no dependency on REST, MCP, Docker, Ollama, B, or C.
2. Application use cases depend on interfaces owned by A.
3. Infrastructure implements persistence and external adapters.
4. API exposes authenticated and authorized operations without bypassing application policy.
5. External adapter failures are observable and must not corrupt local transactions.

## Runtime isolation contract

- Compose project name: `enterprise-operations-platform`.
- Container, network, volume, database, and secret names must be A-specific.
- Host ports must be checked before assignment and bind to `127.0.0.1` by default.
- A must never mount B/C paths or `factory-qdrant-data`.
- Shared host CPU, RAM, disk, GPU, or a future shared Ollama instance must be declared as shared dependency; they are not absolute hardware isolation.
- Use project-scoped lifecycle commands only. Global Docker cleanup commands are prohibited.

## Data and recovery contract

- Use synthetic data until a separate data-handling approval exists.
- Define backup, restore, retention, ownership, and a restore drill before persistent data is considered accepted.
- Recovery operations must identify exact A resources and must not stop or modify B/C.

## Security and agent boundary

- Repository guidance limits intended scope but does not constitute OS-level enforcement.
- Until T7 Allow/Deny tests pass, agent work is supervised and restricted to one approved repository at a time.
- Secrets are supplied at runtime and never written to reports, logs, Git, or tracked `.env` files.

## Future acceptance gates

- Local scaffold builds and tests without B/C.
- Compose static configuration has unique names, localhost bindings, explicit resource limits, and no cross-project mounts.
- Database backup and restore are proven using synthetic data.
- External API/MCP disconnect tests show that core business operations continue.
- Git diff, test evidence, affected files, and rollback steps are recorded for every change.
