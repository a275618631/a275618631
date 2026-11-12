"""Validation for the portfolio registry and its local-only overlay.

This module deliberately has no filesystem or network side effects.  Callers can
use it from the CLI, the deterministic builder, or tests without starting a
server or contacting a remote URL.
"""

from __future__ import annotations

import copy
import datetime as dt
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit


SCHEMA_VERSION = "1.0"
PROJECT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SECRET_QUERY_RE = re.compile(r"(?:token|key|secret|signature|credential|password|passwd|auth)", re.I)
ALLOWED_LINK_KINDS = {"repo", "static_bundle", "local_http", "external_https"}
ALLOWED_LINK_STATUS = {"available", "manual", "unverified", "expired"}
ALLOWED_LIFECYCLE = {"active", "archived"}
ALLOWED_CAPABILITY_STATUS = {"implemented", "partial", "planned"}
ALLOWED_EVIDENCE_STATUS = {"historical", "verified", "partial", "unverified"}
ALLOWED_TOP_LEVEL = {"schema_version", "projects"}


class ValidationError(ValueError):
    """Raised when a registry or overlay violates the public data contract."""


def _fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def _object(value: object, path: str) -> dict:
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    return value  # type: ignore[return-value]


def _text(value: object, path: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        _fail(path, "expected text")
    if not value or len(value) > maximum:
        _fail(path, f"must contain 1–{maximum} characters")
    if CONTROL_RE.search(value):
        _fail(path, "contains a control character")
    return value


def _list(value: object, path: str) -> list:
    if not isinstance(value, list):
        _fail(path, "expected an array")
    return value


def _keys(value: dict, allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        _fail(path, f"unknown field(s): {', '.join(unknown)}")


def _check_unique(values: list, path: str) -> None:
    if len(values) != len(set(values)):
        _fail(path, "values must be unique")


def _is_public_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return True
    return not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def _reject_url_shape(url: str, path: str) -> tuple:
    if not isinstance(url, str) or not url:
        _fail(path, "expected a URL")
    if CONTROL_RE.search(url) or "\\" in url:
        _fail(path, "contains control characters or backslashes")
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        _fail(path, "must be an absolute URL")
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        _fail(path, "userinfo is not allowed")
    if not parts.hostname or not _is_public_host(parts.hostname):
        _fail(path, "loopback/private hosts are not allowed")
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if SECRET_QUERY_RE.search(key) or SECRET_QUERY_RE.search(value):
            _fail(path, "credential-like query parameters are not allowed")
    return parts


def validate_url(url: object, kind: str, *, public: bool = True, path: str = "url") -> str:
    """Validate a URL for one of the four link kinds and return it unchanged."""
    if not isinstance(url, str):
        _fail(path, "expected a URL")
    if kind == "local_http":
        if CONTROL_RE.search(url) or "\\" in url:
            _fail(path, "contains control characters or backslashes")
        parts = urlsplit(url)
        if parts.scheme != "http" or not parts.hostname:
            _fail(path, "local_http must use an absolute HTTP loopback URL")
        host = parts.hostname.lower().strip("[]")
        if host not in {"127.0.0.1", "localhost", "::1"}:
            _fail(path, "local_http only permits loopback hosts")
        if parts.port is None or not (1 <= parts.port <= 65535):
            _fail(path, "local_http port must be between 1 and 65535")
        if parts.username is not None or parts.password is not None or "@" in parts.netloc:
            _fail(path, "userinfo is not allowed")
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            if SECRET_QUERY_RE.search(key) or SECRET_QUERY_RE.search(value):
                _fail(path, "credential-like query parameters are not allowed")
        return url
    parts = _reject_url_shape(url, path)
    if parts.scheme.lower() != "https":
        _fail(path, f"{kind} must use HTTPS")
    if kind == "repo":
        host = parts.hostname.lower().rstrip(".")
        if host not in {"github.com", "www.github.com"}:
            _fail(path, "repo links must point to GitHub")
    return url


def validate_bundle_path(path_value: object, bundle_root: str | Path | None = None, *, path: str = "path") -> str:
    if not isinstance(path_value, str) or not path_value:
        _fail(path, "expected a relative bundle path")
    if "\\" in path_value or "\x00" in path_value:
        _fail(path, "backslashes and NUL are not allowed")
    decoded = path_value
    for _ in range(3):
        decoded = unquote(decoded)
    if decoded.startswith(("/", "//")) or re.match(r"^[A-Za-z]:", decoded):
        _fail(path, "absolute paths are not allowed")
    segments = path_value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        _fail(path, "path must not contain empty, dot, or parent segments")
    if any(segment in {".git", ".local"} for segment in segments):
        _fail(path, "private paths are not allowed")
    if ".." in decoded.split("/"):
        _fail(path, "encoded traversal is not allowed")
    if bundle_root is not None:
        root = Path(bundle_root).resolve()
        raw_candidate = root / Path(*segments)
        current = root
        for segment in segments:
            current = current / segment
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                _fail(path, "symlink and junction paths are not allowed")
        candidate = raw_candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            _fail(path, "path escapes the bundle root")
        if not candidate.is_file():
            _fail(path, "bundle entry does not exist")
    return path_value


def validate_link(link: object, *, project_id: str = "", root: str | Path | None = None, mode: str = "public") -> None:
    item = _object(link, f"projects[{project_id}].links[]")
    _keys(item, {"link_id", "label", "kind", "status", "url", "path", "binding_id", "expires_at"}, "link")
    link_id = _text(item.get("link_id"), "link.link_id", maximum=80)
    if not PROJECT_ID_RE.fullmatch(link_id):
        _fail("link.link_id", "must be a lower-case slug")
    _text(item.get("label"), "link.label", maximum=160)
    kind = item.get("kind")
    if kind not in ALLOWED_LINK_KINDS:
        _fail("link.kind", f"must be one of {sorted(ALLOWED_LINK_KINDS)}")
    if item.get("status") not in ALLOWED_LINK_STATUS:
        _fail("link.status", f"must be one of {sorted(ALLOWED_LINK_STATUS)}")
    if kind == "repo":
        url = item.get("url")
        validate_url(url, kind, path="link.url")
        path_parts = urlsplit(url).path.split("/")
        if not any(SHA40_RE.fullmatch(part) for part in path_parts):
            _fail("link.url", "repo snapshot links must include a full 40-character commit")
    elif kind == "external_https":
        validate_url(item.get("url"), kind, path="link.url")
    elif kind == "static_bundle":
        validate_bundle_path(item.get("path"), (Path(root) / "portfolio" / "public") if root else None, path="link.path")
    elif kind == "local_http":
        binding_id = item.get("binding_id")
        if not isinstance(binding_id, str) or not PROJECT_ID_RE.fullmatch(binding_id):
            _fail("link.binding_id", "must be a lower-case slug")
        if "url" in item and mode == "public":
            _fail("link.url", "public registry local_http links use binding_id only")
        if mode == "local" and "url" in item:
            validate_url(item["url"], kind, path="link.url")
    if "expires_at" in item:
        expires_at = item["expires_at"]
        if not isinstance(expires_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", expires_at):
            _fail("link.expires_at", "must be an ISO-8601 UTC datetime")
        try:
            dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError:
            _fail("link.expires_at", "must be a real calendar datetime")


def validate_project(project: object, *, root: str | Path | None = None, mode: str = "public") -> None:
    item = _object(project, "project")
    _keys(item, {"project_id", "title", "summary", "categories", "tags", "featured", "lifecycle", "capabilities", "snapshot", "evidence", "links", "extensions"}, "project")
    project_id = _text(item.get("project_id"), "project.project_id", maximum=80)
    if not PROJECT_ID_RE.fullmatch(project_id):
        _fail("project.project_id", "must be a lower-case stable slug")
    _text(item.get("title"), "project.title", maximum=100)
    _text(item.get("summary"), "project.summary", maximum=600)
    for field in ("categories", "tags"):
        values = _list(item.get(field), f"project.{field}")
        texts = [_text(v, f"project.{field}[]", maximum=80) for v in values]
        _check_unique(texts, f"project.{field}")
    if not isinstance(item.get("featured"), bool):
        _fail("project.featured", "expected boolean")
    if item.get("lifecycle") not in ALLOWED_LIFECYCLE:
        _fail("project.lifecycle", "must be active or archived")
    capabilities = _list(item.get("capabilities"), "project.capabilities")
    capability_ids = []
    for index, capability in enumerate(capabilities):
        c = _object(capability, f"project.capabilities[{index}]")
        _keys(c, {"id", "title", "description", "status"}, f"project.capabilities[{index}]")
        cid = _text(c.get("id"), f"project.capabilities[{index}].id", maximum=80)
        if not PROJECT_ID_RE.fullmatch(cid):
            _fail(f"project.capabilities[{index}].id", "must be a lower-case slug")
        capability_ids.append(cid)
        _text(c.get("title"), f"project.capabilities[{index}].title", maximum=120)
        _text(c.get("description"), f"project.capabilities[{index}].description", maximum=600)
        if c.get("status") not in ALLOWED_CAPABILITY_STATUS:
            _fail(f"project.capabilities[{index}].status", "invalid capability status")
    _check_unique(capability_ids, "project.capabilities.id")
    snapshot = _object(item.get("snapshot"), "project.snapshot")
    _keys(snapshot, {"revision", "public_ref", "reviewed_at"}, "project.snapshot")
    _text(snapshot.get("revision"), "project.snapshot.revision", maximum=160)
    public_ref = snapshot.get("public_ref")
    if public_ref is not None and (not isinstance(public_ref, str) or not SHA40_RE.fullmatch(public_ref)):
        _fail("project.snapshot.public_ref", "must be null or a full 40-character lowercase commit")
    reviewed_at = snapshot.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not DATE_RE.fullmatch(reviewed_at):
        _fail("project.snapshot.reviewed_at", "must be YYYY-MM-DD")
    try:
        dt.date.fromisoformat(reviewed_at)
    except ValueError:
        _fail("project.snapshot.reviewed_at", "must be a real calendar date")
    evidence = _object(item.get("evidence"), "project.evidence")
    _keys(evidence, {"status", "scope", "reference_urls"}, "project.evidence")
    if evidence.get("status") not in ALLOWED_EVIDENCE_STATUS:
        _fail("project.evidence.status", "invalid evidence status")
    if public_ref is None and evidence.get("status") not in {"unverified", "partial"}:
        _fail("project.evidence.status", "without a published snapshot, evidence must be unverified or partial")
    _text(evidence.get("scope"), "project.evidence.scope", maximum=1200)
    refs = _list(evidence.get("reference_urls"), "project.evidence.reference_urls")
    for ref in refs:
        validate_url(ref, "external_https", path="project.evidence.reference_urls[]")
    links = _list(item.get("links"), "project.links")
    link_ids = []
    for link in links:
        validate_link(link, project_id=project_id, root=root, mode=mode)
        link_ids.append(link["link_id"])
    _check_unique(link_ids, "project.links.link_id")
    if "extensions" in item:
        extensions = _object(item["extensions"], "project.extensions")
        if len(json.dumps(extensions, ensure_ascii=False).encode("utf-8")) > 1024 * 1024:
            _fail("project.extensions", "must be at most 1 MiB")


def validate_registry(data: object, *, root: str | Path | None = None, mode: str = "public", overlay: object | None = None, public_registry: dict | None = None) -> dict:
    registry = _object(data, "registry")
    # The local CLI accepts the overlay itself through the same validator.  Keep
    # this compatibility path explicit so public mode can never accidentally
    # consume an overlay-shaped object.
    if mode == "local" and "projects" not in registry and "local_projects" in registry:
        checked = validate_overlay(registry, registry=public_registry, root=root)
        return checked
    _keys(registry, ALLOWED_TOP_LEVEL, "registry")
    if registry.get("schema_version") != SCHEMA_VERSION:
        _fail("registry.schema_version", f"must be {SCHEMA_VERSION}")
    projects = _list(registry.get("projects"), "registry.projects")
    ids = []
    for project in projects:
        validate_project(project, root=root, mode=mode)
        ids.append(project["project_id"])
    _check_unique(ids, "registry.projects.project_id")
    result = copy.deepcopy(registry)
    if mode == "local" and overlay is not None:
        checked = validate_overlay(overlay, registry=result, root=root)
        result["projects"].extend(copy.deepcopy(checked["local_projects"]))
    elif mode not in {"public", "local"}:
        _fail("mode", "must be public or local")
    return result


def validate_overlay(overlay: object, *, registry: dict | None = None, root: str | Path | None = None) -> dict:
    data = _object(overlay, "overlay")
    _keys(data, {"schema_version", "bindings", "local_projects"}, "overlay")
    if data.get("schema_version") != SCHEMA_VERSION:
        _fail("overlay.schema_version", f"must be {SCHEMA_VERSION}")
    bindings = _list(data.get("bindings", []), "overlay.bindings")
    known: dict[str, set[str]] = {}
    if registry:
        for project in registry.get("projects", []):
            known[project["project_id"]] = {link["binding_id"] for link in project.get("links", []) if link.get("kind") == "local_http"}
    local_projects = _list(data.get("local_projects", []), "overlay.local_projects")
    local_ids = []
    for project in local_projects:
        validate_project(project, root=root, mode="local")
        local_ids.append(project["project_id"])
    _check_unique(local_ids, "overlay.local_projects.project_id")
    if registry:
        existing = {p["project_id"] for p in registry.get("projects", [])}
        overlap = sorted(existing.intersection(local_ids))
        if overlap:
            _fail("overlay.local_projects", f"project IDs already exist in public registry: {', '.join(overlap)}")
    for project in local_projects:
        known[project["project_id"]] = {link["binding_id"] for link in project.get("links", []) if link.get("kind") == "local_http"}
    seen = set()
    for index, binding in enumerate(bindings):
        item = _object(binding, f"overlay.bindings[{index}]")
        _keys(item, {"project_id", "binding_id", "url", "source_path"}, f"overlay.bindings[{index}]")
        project_id = item.get("project_id")
        binding_id = item.get("binding_id")
        if not isinstance(project_id, str) or not PROJECT_ID_RE.fullmatch(project_id):
            _fail(f"overlay.bindings[{index}].project_id", "must be a lower-case slug")
        if not isinstance(binding_id, str) or not PROJECT_ID_RE.fullmatch(binding_id):
            _fail(f"overlay.bindings[{index}].binding_id", "must be a lower-case slug")
        key = (project_id, binding_id)
        if key in seen:
            _fail(f"overlay.bindings[{index}]", "duplicate project_id/binding_id")
        seen.add(key)
        if registry is not None and (project_id not in known or binding_id not in known[project_id]):
            _fail(f"overlay.bindings[{index}].binding_id", "binding must match a declared local_http link on a known project")
        validate_url(item.get("url"), "local_http", path=f"overlay.bindings[{index}].url")
        if "source_path" in item:
            _text(item["source_path"], f"overlay.bindings[{index}].source_path", maximum=1000)
    return copy.deepcopy(data)


def load_json(path: str | Path) -> dict:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return _object(json.load(handle), str(path))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON ({exc.msg})") from exc


def load_registry(root: str | Path, *, mode: str = "public") -> dict:
    supplied = Path(root)
    # Accept both the repository root and an explicit registry/overlay file;
    # the latter is useful to the CLI's build module and keeps the API portable.
    if supplied.is_file() or supplied.name.endswith(".json"):
        if supplied.name == "projects.local.json":
            return load_json(supplied)
        root_path = supplied.parent.parent
        registry = load_json(supplied)
    else:
        root_path = supplied
        registry = load_json(root_path / "portfolio" / "projects.json")
    if mode == "public":
        return validate_registry(registry, root=root_path, mode="public")
    overlay_path = root_path / ".local" / "projects.local.json"
    overlay = load_json(overlay_path) if overlay_path.exists() else {"schema_version": SCHEMA_VERSION, "bindings": [], "local_projects": []}
    return validate_registry(registry, root=root_path, mode="local", overlay=overlay)

