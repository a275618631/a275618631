# Authenticated Desktop Media Workflow

A macOS desktop workflow combining secure session persistence, resilient media extraction, FFmpeg-based media processing, download-state tracking, and real end-to-end validation.

Designed for user-authorized media workflows.

---

## Problem

Downloading media from authenticated web services involves more than a simple HTTP request. A functional workflow requires handling session persistence across app restarts, fallback extraction strategies when primary resolvers fail, format negotiation (direct MP4 vs. HLS/fMP4 segmented streams), and safe file delivery that prevents incomplete output files from reaching the destination.

---

## Architecture

```text
User input (URL)
  → URL normalization & query-parameter stripping
  → Authentication state check (Keychain)
  → Primary resolver (yt-dlp)
     → Fallback resolver (GraphQL)
  → Quality selection
  → HLS / direct MP4 routing
  → FFmpeg encapsulation & verification
  → Atomic file move → destination
```

---

## Key Engineering Decisions

**Session persistence via macOS Keychain**
Authenticated sessions are stored in macOS Keychain using Security-Scoped Bookmarks rather than plain files. A session is only persisted after real-request validation — cookie-file presence alone is not treated as proof of successful authentication.

**Fail-safe file delivery**
Downloads write to a cache path first. FFmpeg encapsulation and file integrity checks run before the atomic move to the destination. An incomplete file never appears at the final path.

**Fallback resolver design**
The primary extractor (yt-dlp) handles the common path. A secondary resolver provides continuity when the primary is unavailable, without exposing implementation details or requiring user intervention.

**HLS/fMP4 troubleshooting**
Segmented stream handling required diagnosing resolution, segment ordering, and FFmpeg routing issues specific to HLS playlists. These were resolved through incremental testing against real content structures.

---

## Technology

- **Desktop runtime**: Tauri 2 (Rust backend + WebView frontend)
- **Language**: Rust (backend), TypeScript + React (frontend)
- **Session storage**: macOS Keychain via Security-Scoped Bookmarks
- **Extraction**: yt-dlp (primary), custom GraphQL resolver (fallback)
- **Media processing**: FFmpeg (encapsulation, format conversion, integrity check)
- **State management**: Zustand
- **Build**: Vite, Cargo

---

## Validation

End-to-end flow validated manually across:
- Anonymous and authenticated extraction paths
- Direct MP4 and HLS/fMP4 segmented streams
- Keychain persistence and session reload across app restarts
- Large file handling (>1 GB pre-confirmation gate)
- Atomic file delivery (incomplete files do not reach destination)

---

## Current Status

**Functional MVP — End-to-End Validated**

Core download pipeline, authentication flow, and file delivery are working and manually verified.

---

## Privacy & Security Boundary

- No passwords are requested or stored
- No cookies, session tokens, or signed URLs are logged or transmitted externally
- Browser session import is best-effort and explicitly labeled as such; it is not treated as equivalent to a verified in-app login
- External extractor cookie scratch files are cleared after each task
- DRM-protected content is explicitly not handled

The implementation repository is private. This document describes architecture and engineering decisions only.
