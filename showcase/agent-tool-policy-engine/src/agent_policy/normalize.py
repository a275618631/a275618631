from __future__ import annotations

import hashlib
import ntpath
import os
import posixpath
import re
from dataclasses import replace
from pathlib import Path

from .model import ToolCall

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:/")


def normalize_path(value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if raw == "~" or raw.startswith("~/"):
        raw = os.path.expanduser(raw)
    raw = raw.replace("\\", "/")
    if not raw:
        return None
    if _DRIVE_PREFIX.match(raw):
        normalized = ntpath.normpath(raw).replace("\\", "/")
    else:
        normalized = posixpath.normpath(raw)
    return normalized.rstrip("/") or "/"


def normalize_repo(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip().removeprefix("https://github.com/").removeprefix("http://github.com/")
    return value.rstrip("/").removesuffix(".git").lower() or None


def normalize_branch(value: str | None) -> str | None:
    if value is None:
        return None
    return str(value).strip().removeprefix("refs/heads/").removeprefix("refs/remotes/") or None


def normalize_domain(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip().lower()
    value = re.sub(r"^[a-z]+://", "", value).split("/", 1)[0]
    return value.split(":", 1)[0] or None


def normalize_tool_call(call: ToolCall) -> ToolCall:
    target = normalize_path(call.target) if call.path or _looks_like_path(call.target) else call.target
    return replace(
        call,
        tool=str(call.tool or "").strip().lower(),
        operation=str(call.operation or "").strip().lower(),
        target=target,
        path=normalize_path(call.path),
        repo=normalize_repo(call.repo),
        branch=normalize_branch(call.branch),
        domain=normalize_domain(call.domain),
    )


def target_fingerprint(target: str | None) -> str | None:
    if target is None:
        return None
    return hashlib.sha256(target.encode("utf-8")).hexdigest()[:16]


def is_within_path(path: str | None, root: str | None) -> bool:
    path = normalize_path(path)
    root = normalize_path(root)
    if not path or not root:
        return False
    if bool(_DRIVE_PREFIX.match(path)) != bool(_DRIVE_PREFIX.match(root)):
        return False
    if not _DRIVE_PREFIX.match(path) or os.name == "nt":
        try:
            resolved_path = Path(path).expanduser().resolve(strict=False)
            resolved_root = Path(root).expanduser().resolve(strict=False)
            resolved_path.relative_to(resolved_root)
            return True
        except ValueError:
            return False
        except OSError:
            pass
    try:
        common = ntpath.commonpath([path, root]) if _DRIVE_PREFIX.match(path) else posixpath.commonpath([path, root])
    except ValueError:
        return False
    return normalize_path(common) == root


def _looks_like_path(value: str | None) -> bool:
    return bool(value and (value.startswith(("/", "~/")) or _DRIVE_PREFIX.match(value.replace("\\", "/"))))
