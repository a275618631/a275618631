# Portfolio Hub Architecture Decisions

## ADR-001 — Extend the Profile repository

**Decision:** Keep the existing public Profile repo as canonical owner and place the independent app in `portfolio/`.

**Context:** The repo had profile documentation and source snapshots but no runnable portfolio home. No repo rule or ownership boundary prohibits adding a local static app.

**Trade-off:** Readers can inspect one source repository, while an app change also creates a focused PR beside profile copy. A standalone repository would add a second publication and registry owner without solving a current boundary.

## ADR-002 — Static HTML with a Python standard-library CLI

**Decision:** Generate portable HTML/CSS/JavaScript using one JSON registry; use Python 3.12+ only for validation, builds, safe local serving, imports and audits.

**Trade-off:** The experience avoids Node, databases, API keys, external assets and cloud accounts at runtime. The implementation owns explicit URL/path checks and a limited local preview server instead of delegating those boundaries to a framework.

## ADR-003 — Keep source projects independent

**Decision:** The hub links to fixed public snapshots, explicitly imported static bundles, user-started loopback apps and optional public HTTPS demos. It never launches, proxies or shares state with a source app.

**Trade-off:** Dynamic demos open in their own tab and users start them using their source README. The hub stays usable even when a project is offline, archived or still being changed.

## ADR-004 — Separate public data from local bindings

**Decision:** `portfolio/projects.json` is the public registry. `.local/projects.local.json` is a private local overlay and is never opened in public mode.

**Trade-off:** Local demo URLs and source paths require one local configuration file. In exchange, local machine details cannot leak into public artifacts through ordinary builds.

## ADR-005 — Treat static imports as explicit publications

**Decision:** Import only a caller-provided file allowlist from `.local/imports/<project>/<revision>/`; verify checksums, size, path and references; never run imported code or build scripts.

**Trade-off:** A framework-built page must be exported and reviewed before import. Arbitrary source checkouts and dynamic assets do not enter the public bundle automatically.

## ADR-006 — Preserve evidence and make cloud hosting optional

**Decision:** Product readiness and evidence are registry fields; remote link verification is explicit; public build is host-independent and uses relative assets and hash routes.

**Trade-off:** A broken external demo is reported for that link only. The hub provides no automatic deployment, tunnel, DNS, rewrite rule or false claim that the linked source is currently healthy.
