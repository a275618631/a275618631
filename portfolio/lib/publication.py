"""Public content audit and explicitly invoked, SSRF-resistant link checks."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


TEXT_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".json", ".js", ".css", ".svg", ".xml", ".yml", ".yaml", ".toml", ".py", ".ps1", ".sh", ".csv"}
SKIP_PARTS = {".git", ".local", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}
SECRET_PATTERNS = {
    "credential-aws-access-key": r"AKIA[0-9A-Z]{16}",
    "credential-private-key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "credential-github-token": r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    "credential-github-pat": r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
    "credential-openai-token": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
    "credential-jwt": r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}\b",
    "credential-url-userinfo": r"\bhttps?://[^/\s:@]+:[^/@\s]+@",
}


class AuditError(ValueError):
    pass


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _load_rules(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
            raise ValueError("rules must be an object with a rules array")
        output = []
        for item in data["rules"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("values"), list):
                raise ValueError("invalid rule entry")
            values = [v for v in item["values"] if isinstance(v, str) and len(v.strip()) >= 3]
            output.append({"id": item["id"], "values": [_norm(v.strip()) for v in values]})
        exceptions = []
        for item in data.get("false_positive_exceptions", []):
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
                raise ValueError("invalid false-positive exception")
            rule_ids = item.get("rule_ids")
            if not isinstance(rule_ids, list) or not all(isinstance(rule_id, str) for rule_id in rule_ids):
                raise ValueError("invalid false-positive rule IDs")
            exceptions.append({"path": item["path"], "sha256": item["sha256"], "rule_ids": set(rule_ids), "reason": str(item.get("reason", "classified synthetic fixture"))})
        return output, exceptions
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise AuditError(f"invalid or missing audit rules ({type(exc).__name__})") from None


def _is_text(path: Path) -> bool:
    return path.suffix.casefold() in TEXT_EXTENSIONS


def _scan_paths(root: Path, paths: list[Path], rules: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import re

    findings: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for path in paths:
        try:
            rel = path.relative_to(root).as_posix()
            if any(part in SKIP_PARTS for part in Path(rel).parts):
                continue
            normalized_name = _norm(rel)
            text = ""
            if _is_text(path) and path.is_file() and not path.is_symlink():
                raw = path.read_bytes()
                if b"\x00" not in raw and len(raw) <= 4 * 1024 * 1024:
                    text = _norm(raw.decode("utf-8", "replace"))
            content = normalized_name + "\n" + text
            raw_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else ""
            exception = next((item for item in exceptions if item["path"] == rel and item["sha256"] == raw_hash), None)
            for rule in rules:
                matches = sum(content.count(token) for token in rule["values"] if token)
                if matches:
                    findings.append({"path": rel, "rule_id": rule["id"], "matches": matches})
            for rule_id, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, content, flags=re.IGNORECASE):
                    finding = {"path": rel, "rule_id": rule_id, "matches": 1}
                    if exception and rule_id in exception["rule_ids"]:
                        suppressed.append({**finding, "reason": exception["reason"]})
                    else:
                        findings.append(finding)
        except (OSError, ValueError):
            findings.append({"path": "<unreadable>", "rule_id": "file-read-error", "matches": 1})
    return findings, suppressed


def _git_files(root: Path) -> list[Path]:
    import subprocess

    result = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"], check=True, capture_output=True)
    relpaths = [p.decode("utf-8", "surrogateescape") for p in result.stdout.split(b"\x00") if p]
    return [root / rel for rel in relpaths]


def audit(root: Path, scope: str, rules_path: Path) -> dict[str, Any]:
    if scope not in {"all", "artifact"}:
        raise AuditError("scope must be all or artifact")
    root = root.resolve()
    rules, exceptions = _load_rules(rules_path)
    if scope == "artifact":
        base = root / ".local" / "dist" / "public"
        manifest_path = base / "files.sha256.json"
        if not base.is_dir() or base.is_symlink() or getattr(base, "is_junction", lambda: False)():
            raise AuditError("public artifact directory is missing or unsafe")
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise AuditError("public artifact manifest is missing or unsafe")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = manifest["files"]
            if not isinstance(entries, list) or not entries:
                raise ValueError
            if not re.fullmatch(r"[0-9a-f]{64}", manifest["digest"]):
                raise ValueError
            if hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n").hexdigest() != manifest["digest"]:
                raise ValueError
            expected = {}
            for entry in entries:
                name, digest = entry["path"], entry["sha256"]
                parts = Path(name).parts
                if not isinstance(name, str) or Path(name).is_absolute() or ".." in parts or "\\" in name or name == "files.sha256.json" or not re.fullmatch(r"[0-9a-f]{64}", digest) or name in expected:
                    raise ValueError
                expected[name] = digest
            paths = []
            for path in base.rglob("*"):
                if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                    raise ValueError
                if path.is_file() and path != manifest_path:
                    paths.append(path)
            actual = {p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
            if actual != expected:
                raise ValueError
        except (OSError, ValueError, KeyError, TypeError, UnicodeError):
            raise AuditError("public artifact manifest or contents are invalid") from None
        scan_root = base
    else:
        paths = _git_files(root)
        scan_root = root
    findings, suppressed = _scan_paths(scan_root, paths, rules, exceptions)
    return {"scope": scope, "status": "PASS" if not findings else "FAIL", "files_scanned": len(paths), "findings": findings, "classified_synthetic_findings": suppressed}


def asset_ledger(root: Path, baseline_commit: str) -> dict[str, Any]:
    import subprocess

    root = root.resolve()
    changed = subprocess.run(["git", "-C", str(root), "diff", "--name-only", baseline_commit, "--"], check=True, capture_output=True, text=True).stdout.splitlines()
    candidates = set()
    for line in subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", baseline_commit], check=True, capture_output=True, text=True).stdout.splitlines():
        if Path(line).suffix.casefold() in {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            candidates.add(line)
    for line in changed:
        if Path(line).suffix.casefold() in {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            candidates.add(line)
    rows = []
    for rel in sorted(candidates):
        path = root / rel
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            prior = subprocess.run(["git", "-C", str(root), "rev-parse", f"{baseline_commit}:{rel}"], capture_output=True, text=True)
            rows.append({"path": rel, "sha256": digest, "baseline_blob": prior.stdout.strip() if prior.returncode == 0 else None,
                         "baseline_unchanged": prior.returncode == 0 and rel not in changed,
                         "review": "prior_visual_or_extraction_evidence_may_be_reused" if prior.returncode == 0 and rel not in changed else "review_required"})
    return {"baseline_commit": baseline_commit, "asset_count": len(rows), "assets": rows}


def _public_addresses(host: str, port: int) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        return []
    addresses = sorted({info[4][0] for info in infos})
    if not addresses or any(not ipaddress.ip_address(addr.split("%", 1)[0]).is_global for addr in addresses):
        return []
    return addresses


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, ip: str, timeout: float):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_ip = ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def verify_url(url: str, timeout: float = 5.0) -> dict[str, Any]:
    current = url
    for redirect_count in range(2):
        parsed = urlsplit(current)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return {"status": "REJECTED", "reason": "unsafe_url"}
        port = parsed.port or 443
        addresses = _public_addresses(parsed.hostname, port)
        if not addresses:
            return {"status": "REJECTED", "reason": "non_public_or_unresolved_host"}
        connection = _PinnedHTTPS(parsed.hostname, port, addresses[0], timeout)
        try:
            path = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
            connection.request("HEAD", path, headers={"User-Agent": "PortfolioHub-link-check/1.0", "Connection": "close"})
            response = connection.getresponse()
            response.read(1)
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                connection.close()
                if redirect_count or not location:
                    return {"status": "UNVERIFIED", "http_status": response.status}
                from urllib.parse import urljoin

                current = urljoin(current, location)
                continue
            return {"status": "VERIFIED" if 200 <= response.status < 400 else "UNVERIFIED", "http_status": response.status}
        except (OSError, http.client.HTTPException, ssl.SSLError, ValueError) as exc:
            return {"status": "UNVERIFIED", "reason": type(exc).__name__}
        finally:
            connection.close()
    return {"status": "UNVERIFIED", "reason": "redirect_limit"}
