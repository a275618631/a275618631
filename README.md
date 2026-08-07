# Che-Yu Wu

I turn ambiguous real-world problems into structured, testable, and safe AI-assisted systems.

My work focuses on system integration, AI-assisted workflows, agent engineering, automation, and translating operational requirements into reliable, validated systems.

---

## Focus

- AI Agent Engineering & Workflow Orchestration
- System Integration & Automation
- Human-in-the-loop Design & Safety Boundaries
- Requirements → Architecture → Validation
- Cross-platform & Portable Tooling

---

## Featured Projects

### [Portable AI Agent Engineering Environment](https://github.com/a275618631/portable-ai-agent-environment)
`AI Agents · System Architecture · Security · Cross-platform`

Addresses the problem of copying an entire AI agent environment between machines — which can inadvertently copy session state, credentials, and machine identity. Establishes a categorized portable boundary, separates multi-agent responsibilities (Planning / Research / Engineering / Delivery), implements fail-closed staged secret scanning, and validates safety controls with a targeted regression suite. Cross-platform validated on Windows and macOS.

→ [Case Study](https://github.com/a275618631/portable-ai-agent-environment/blob/main/docs/case-study.md)

---

### [Constraint-Based Workforce Scheduling System](https://github.com/a275618631/workforce-scheduling-system)
`System Analysis · Rule Engine · Scheduling · Validation`

Translates complex rotating-shift operational constraints into a structured scheduling workflow. Covers personnel management, team assignment, locked and manual duty handling, violation and warning states, calendar-based overview, and iterative rule validation. Developed through multiple evolutionary phases. The underlying private implementation reached 56 validated automated test cases.

Originally developed around a rotating-shift public-sector scheduling use case using anonymized synthetic data.

→ [Case Study](https://github.com/a275618631/workforce-scheduling-system/blob/main/docs/case-study.md)

---

### Authenticated Desktop Media Workflow *(private implementation)*
`Tauri · Rust · TypeScript · FFmpeg · Integration`

A macOS desktop workflow (Tauri 2 + Rust + React) exploring secure session persistence, resilient media extraction, and verified download pipelines. Implemented authenticated session handling with macOS Keychain storage, yt-dlp integration, HLS/fMP4 resolution, FFmpeg-based processing with atomic file moves, and real end-to-end validation across the full authentication → extraction → download pipeline.

Designed for user-authorized media workflows.

→ [Case Study](projects/authenticated-desktop-media-workflow.md)

---

## Prototype / Exploration

### Privacy-Aware Meeting Intelligence Workflow *(Prototype / Partially Validated MVP)*
`AI Workflow · Privacy · Human-in-the-loop · Evidence`

A prototype for a privacy-oriented meeting intelligence pipeline: transcript input → PII masking → LLM summarization → decision and action-item extraction → evidence traceability → human review. Built with Streamlit, FastAPI, Docker Compose, and SQLite WAL.

Transcript processing, PII masking, structured output, and evidence validation have been implemented and locally verified. Real-world MP4 → STT → speaker diarization → external LLM full E2E is designed but not end-to-end validated at this stage.

*Architecture and partial implementation stage.*

---

## Experiments & Reusable Components

- **[codex-agent-skills](https://github.com/a275618631/codex-agent-skills)** — Bilingual, safety-first agent skill library for reliable delivery, automation, and review workflows
