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
  → Authenticated session state (macOS Keychain)
  → yt-dlp media resolution
  → Quality selection
  → Direct MP4 / HLS-fMP4 routing
  → FFmpeg encapsulation & verification
  → Atomic file move → destination (Security-Scoped Bookmark)
```

---

## Key Engineering Decisions

**Session persistence via macOS Keychain**
Authenticated session state is securely persisted in macOS Keychain and restored across application restarts. A session is only stored after real-request validation — cookie-file presence alone is not treated as proof of successful authentication.

**Destination access via Security-Scoped Bookmarks**
User-selected destination folders retain sandbox-compatible access through macOS Security-Scoped Bookmarks. When a Bookmark becomes stale, the system marks the destination as invalid and prompts for re-selection rather than failing silently.

**Fail-safe file delivery**
Downloads write to a cache path first. FFmpeg encapsulation and file integrity checks run before the atomic move to the destination. An incomplete file never appears at the final path.

**HLS/fMP4 troubleshooting**
Segmented stream handling required diagnosing resolution, segment ordering, and FFmpeg routing issues specific to HLS playlists. These were resolved through incremental testing against real content structures.

---

## Technology

- **Desktop runtime**: Tauri 2 (Rust backend + WebView frontend)
- **Language**: Rust (backend), TypeScript + React (frontend)
- **Session storage**: macOS Keychain (authenticated session state)
- **Destination access**: macOS Security-Scoped Bookmarks (folder permission persistence)
- **Extraction**: yt-dlp
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
