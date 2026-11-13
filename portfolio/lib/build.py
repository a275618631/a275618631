"""Deterministic, offline static projection for the portfolio hub."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

try:
    from .contracts import load_registry, validate_registry
except ImportError:  # CLI loads lib/ directly when hub.py is invoked as a script.
    from contracts import load_registry, validate_registry


class BuildError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _esc(value: Any) -> str:
    from html import escape

    return escape(str(value), quote=True)


def project_projection(registry: dict[str, Any], overlay: dict[str, Any] | None, mode: str) -> dict[str, Any]:
    projects = [dict(item) for item in registry["projects"]]
    if mode == "local" and overlay:
        by_id = {p["project_id"]: p for p in projects}
        for item in overlay.get("local_projects", []):
            by_id[item["project_id"]] = dict(item)
        projects = list(by_id.values())
        bindings = overlay.get("bindings", [])
        lookup = {(b["project_id"], b["binding_id"]): b for b in bindings}
        for project in projects:
            safe_links = []
            for link in project.get("links", []):
                if link.get("kind") == "local_http":
                    binding = lookup.get((project["project_id"], link["binding_id"]))
                    if binding:
                        safe_links.append({**link, "url": binding["url"], "status": "unverified"})
                    else:
                        safe_links.append({**link, "status": "unverified"})
                    continue
                if link.get("kind") == "static_bundle" and link.get("path"):
                    safe_links.append({**link, "url": link["path"]})
                    continue
                safe_links.append(link)
            project["links"] = safe_links
            project.pop("source_path", None)
    else:
        for project in projects:
            public_links = []
            for link in project.get("links", []):
                if link.get("kind") == "local_http":
                    continue
                if link.get("kind") == "static_bundle" and link.get("path"):
                    public_links.append({**link, "url": link["path"]})
                    continue
                public_links.append(link)
            project["links"] = public_links

    projects.sort(key=lambda p: (not p.get("featured", False), p["title"].casefold(), p["project_id"]))
    categories = sorted({category for p in projects for category in p.get("categories", [])}, key=str.casefold)
    return {"schema_version": registry["schema_version"], "mode": mode, "categories": categories, "projects": projects}


def render_static_index(data: dict[str, Any], base_path: str = "") -> str:
    clean_base = base_path.strip("/")
    if any(part in {".", ".."} for part in clean_base.split("/")) or "\\" in clean_base:
        raise BuildError("base path must be a safe relative prefix")
    prefix = (clean_base + "/") if clean_base else ""
    cards: list[str] = []
    for p in data["projects"]:
        features = "".join(f"<li><span>{_esc(f['title'])}</span><span class=\"state\">{_esc(f['status'])}</span></li>" for f in p.get("capabilities", []))
        link_items = []
        for link in p.get("links", []):
            state = "（未檢查）" if link.get("kind") == "local_http" else "（尚未驗證）" if link.get("status") in {"manual", "unverified"} else ""
            label = _esc(link["label"] + state)
            if link.get("status") == "expired":
                link_items.append(f'<span class="quiet">{_esc(link["label"])}（已過期）</span>')
            elif link.get("url"):
                link_items.append(f'<a href="{_esc(link["url"])}" target="_blank" rel="noopener noreferrer">{label}</a>')
        links = "".join(link_items)
        if not links:
            links = '<span class="quiet">請查看作品說明</span>'
        cards.append(
            f'<article class="project-card" data-project-id="{_esc(p["project_id"])}">'
            f'<p class="eyebrow">{_esc(" · ".join(p.get("categories", [])))}</p>'
            f'<h2>{_esc(p["title"])}</h2>'
            f'<p>{_esc(p["summary"])}</p><ul class="feature-list">{features}</ul>'
            f'<p class="evidence">證據：{_esc(p.get("evidence", {}).get("status", "unverified"))} · '
            f'版本：{_esc(p.get("snapshot", {}).get("revision", "未發布"))}</p><nav>{links}</nav></article>'
        )
    template_path = Path(__file__).resolve().parents[1] / "web" / "index.template.html"
    template = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{CSS_PATH}}": f"{prefix}styles.css",
        "{{JS_PATH}}": f"{prefix}app.js",
        "{{CATEGORY_OPTIONS}}": "".join(f'<option value="{_esc(c)}">{_esc(c)}</option>' for c in data["categories"]),
        "{{PROJECT_COUNT}}": str(len(data["projects"])),
        "{{STATIC_CARDS}}": "".join(cards),
    }
    for marker, replacement in replacements.items():
        template = template.replace(marker, replacement)
    return template


def _safe_out(root: Path, mode: str, out: str | Path | None) -> Path:
    lexical = root / ".local" / "dist" / mode
    managed = (root / ".local", root / ".local" / "dist", lexical)
    if any(p.is_symlink() or getattr(p, "is_junction", lambda: False)() for p in managed):
        raise BuildError("managed output path must not contain symlinks")
    expected = lexical.resolve()
    target = Path(out).resolve() if out is not None else expected
    if target != expected and not (".local" in target.parts and "tests" in target.parts):
        raise BuildError("output path is outside the managed build directory")
    if target == root.resolve():
        raise BuildError("refusing to use repository root as output")
    if target.is_symlink() or getattr(target, "is_junction", lambda: False)():
        raise BuildError("output path must not be a symlink")
    return target


def _existing_output_is_owned(target: Path) -> None:
    if not target.exists():
        return
    manifest_path = target / "files.sha256.json"
    if not manifest_path.is_file():
        raise BuildError("existing output is unrecognized; preserving it")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        known = {entry["path"] for entry in manifest["files"]}
    except (OSError, ValueError, KeyError, TypeError):
        raise BuildError("existing output manifest is invalid; preserving it")
    entries = list(target.rglob("*"))
    if any(p.is_symlink() or getattr(p, "is_junction", lambda: False)() for p in entries):
        raise BuildError("existing output contains a symlink; preserving it")
    actual = {p.relative_to(target).as_posix() for p in entries if p.is_file()}
    expected_files = known | {"files.sha256.json"}
    expected_dirs = set()
    for name in expected_files:
        parts = Path(name).parts[:-1]
        for depth in range(1, len(parts) + 1):
            expected_dirs.add(Path(*parts[:depth]).as_posix())
    actual_dirs = {p.relative_to(target).as_posix() for p in entries if p.is_dir()}
    if actual != expected_files or actual_dirs != expected_dirs:
        raise BuildError("existing output contains unknown files; preserving it")


def _copy_bundles(source_root: Path, dest_root: Path) -> None:
    if not source_root.exists():
        return
    if source_root.is_symlink() or getattr(source_root, "is_junction", lambda: False)():
        raise BuildError("public demos root must not be a symlink")
    seen = set()
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise BuildError("public demo assets must not contain symlinks")
        rel = path.relative_to(source_root)
        if any(part.startswith(".") for part in rel.parts) or path.suffix.casefold() == ".map":
            raise BuildError("private dotfiles and source maps cannot enter public output")
        canonical = unicodedata.normalize("NFKC", rel.as_posix()).casefold()
        if canonical in seen:
            raise BuildError("public demo assets collide under case-fold/NFKC")
        seen.add(canonical)
        if path.is_file():
            target = dest_root / "demos" / Path(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def _write_manifest(stage: Path) -> str:
    entries = []
    for path in sorted((p for p in stage.rglob("*") if p.is_file()), key=lambda p: p.relative_to(stage).as_posix()):
        rel = path.relative_to(stage).as_posix()
        entries.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    digest = hashlib.sha256(canonical_json(entries)).hexdigest()
    (stage / "files.sha256.json").write_bytes(canonical_json({"files": entries, "digest": digest}))
    return digest


def build_site(root: Path, mode: str = "public", out: str | Path | None = None) -> tuple[Path, str]:
    if mode not in {"public", "local"}:
        raise BuildError("mode must be public or local")
    root = root.resolve()
    registry = load_registry(root / "portfolio" / "projects.json")
    validate_registry(registry, root=root, mode="public")
    overlay = None
    # Deliberately do not even stat/read the overlay in public mode.
    if mode == "local":
        overlay_path = root / ".local" / "projects.local.json"
        if overlay_path.exists():
            overlay = load_registry(overlay_path)
            validate_registry(overlay, root=root, mode="local", public_registry=registry)
    data = project_projection(registry, overlay, mode)
    target = _safe_out(root, mode, out)
    _existing_output_is_owned(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{mode}-stage-", dir=target.parent))
    try:
        (stage / "index.html").write_text(render_static_index(data), encoding="utf-8", newline="\n")
        for name in ("app.js", "styles.css"):
            shutil.copyfile(root / "portfolio" / "web" / name, stage / name)
        (stage / "projects.json").write_bytes(canonical_json(data))
        public_demos = root / "portfolio" / "public" / "demos"
        _copy_bundles(public_demos, stage)
        digest = _write_manifest(stage)
        previous = target.with_name(target.name + ".previous")
        if previous.exists():
            raise BuildError("previous output backup exists; preserving all copies")
        if target.exists():
            os.replace(target, previous)
        try:
            os.replace(stage, target)
        except OSError:
            if previous.exists() and not target.exists():
                os.replace(previous, target)
            raise
        if previous.exists():
            shutil.rmtree(previous)
        return target, digest
    finally:
        if stage.exists():
            shutil.rmtree(stage)
