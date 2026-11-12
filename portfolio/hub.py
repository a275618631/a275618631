#!/usr/bin/env python3
"""Single command-line entry point for the portable portfolio hub."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath


PORTFOLIO = Path(__file__).resolve().parent
ROOT = PORTFOLIO.parent
sys.path.insert(0, str(PORTFOLIO / "lib"))
sys.path.insert(0, str(ROOT))

from contracts import SCHEMA_VERSION, ValidationError, load_json, load_registry, validate_project, validate_registry, validate_url
from build import BuildError, build_site, canonical_json
from publication import AuditError, asset_ledger, audit, verify_url
from server import SafeServerError, serve


EXIT_DATA = 2
EXIT_IO = 3
EXIT_BOUNDARY = 4
EXIT_AUDIT = 5
EXIT_TIMEOUT = 6


def _print(value, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
    elif isinstance(value, dict):
        for key, item in value.items():
            print(f"{key}: {item}")
    else:
        print(value)


def cmd_doctor(args) -> int:
    import sysconfig
    import platform

    try:
        version = sys.version_info
        files = ["projects.json", "projects.schema.json", "local.schema.json", "web/index.template.html", "web/app.js", "web/styles.css"]
        missing = [name for name in files if not (PORTFOLIO / name).is_file()]
        staged = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--name-only", "-z"], capture_output=True, check=True)
        staged_paths = [p.decode("utf-8", "replace") for p in staged.stdout.split(b"\x00") if p]
        issue_files = [p for p in staged_paths if p.startswith(".local/") or "venv" in p.casefold() or p.endswith(".log")]
        report = {
            "status": "PASS" if version >= (3, 12) and not missing and not issue_files else "FAIL",
            "python": platform.python_version(), "python_supported": version >= (3, 12),
            "repository_root": str(ROOT), "default_branch_base": "308063538eaec8df533416b3972039551f04677d",
            "portfolio_files_missing": missing, "managed_output": str(ROOT / ".local" / "dist"),
            "staged_local_or_log_paths": issue_files, "schema_version": SCHEMA_VERSION,
        }
        _print(report, args.json)
        return 0 if report["status"] == "PASS" else EXIT_IO
    except (OSError, subprocess.SubprocessError) as exc:
        _print({"status": "FAIL", "error": type(exc).__name__}, args.json)
        return EXIT_IO


def cmd_validate(args) -> int:
    try:
        if args.mode == "public":
            # Public mode loads exactly one source. It never stats the local overlay.
            data = load_registry(ROOT)
            count = len(data["projects"])
        else:
            data = load_registry(ROOT, mode="local")
            overlay = data.get("projects", [])
            count = len(overlay)
        _print({"status": "PASS", "mode": args.mode, "projects": count, "offline": bool(args.offline)}, args.json)
        return 0
    except ValidationError as exc:
        _print({"status": "FAIL", "mode": args.mode, "error": str(exc)}, args.json)
        return EXIT_DATA
    except OSError as exc:
        _print({"status": "FAIL", "mode": args.mode, "error": type(exc).__name__}, args.json)
        return EXIT_IO


def cmd_build(args) -> int:
    try:
        target, digest = build_site(ROOT, mode=args.mode)
        _print({"status": "PASS", "mode": args.mode, "output": target.relative_to(ROOT).as_posix(), "digest": digest}, args.json)
        return 0
    except ValidationError as exc:
        _print({"status": "FAIL", "error": str(exc)}, args.json)
        return EXIT_DATA
    except BuildError as exc:
        _print({"status": "FAIL", "error": str(exc)}, args.json)
        return EXIT_BOUNDARY
    except (OSError, ValueError) as exc:
        _print({"status": "FAIL", "error": type(exc).__name__}, args.json)
        return EXIT_IO


def _atomic_json(path: Path, data) -> None:
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise OSError("registry path must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical_json(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def cmd_upsert(args) -> int:
    path = PORTFOLIO / "projects.json"
    try:
        incoming = load_json(args.input)
        validate_project(incoming, root=ROOT)
        if args.previous_id and args.previous_id != incoming["project_id"]:
            raise ValidationError("renaming project_id is not supported; keep the existing stable ID")
        registry = load_registry(path)
        before = next((p for p in registry["projects"] if p["project_id"] == incoming["project_id"]), None)
        after = [dict(p) for p in registry["projects"]]
        if before is None:
            after.append(incoming)
            action = "add"
        elif before == incoming:
            action = "unchanged"
        else:
            after = [incoming if p["project_id"] == incoming["project_id"] else p for p in after]
            action = "update"
        candidate = {"schema_version": SCHEMA_VERSION, "projects": after}
        validate_registry(candidate, root=ROOT)
        if not args.dry_run and action != "unchanged":
            _atomic_json(path, candidate)
        _print({"status": "PASS", "action": action, "dry_run": args.dry_run, "project_id": incoming["project_id"],
                "before_sha256": hashlib.sha256(canonical_json(registry)).hexdigest(),
                "after_sha256": hashlib.sha256(canonical_json(candidate)).hexdigest()}, args.json)
        return 0
    except ValidationError as exc:
        _print({"status": "FAIL", "error": str(exc)}, args.json)
        return EXIT_DATA
    except (OSError, ValueError) as exc:
        _print({"status": "FAIL", "error": type(exc).__name__}, args.json)
        return EXIT_IO


def _bundle_path(raw: str, source: Path) -> Path:
    from contracts import validate_bundle_path

    validate_bundle_path(raw)
    parts = PurePosixPath(raw).parts
    if any(part.startswith(".") or part.casefold().endswith(".map") for part in parts):
        raise ValidationError("dotfiles and source maps are not importable")
    path = source.joinpath(*parts)
    current = source
    for part in parts:
        current = current / part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValidationError("symlink or junction entries are not importable")
    resolved = path.resolve(strict=True)
    resolved.relative_to(source)
    if not resolved.is_file():
        raise ValidationError("allowlist entry must be a file")
    return resolved


def _validate_bundle_references(files: dict[str, bytes], allowed: set[str]) -> None:
    import html.parser
    import urllib.parse

    class AssetParser(html.parser.HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.refs = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            for key in ("src", "poster"):
                if key in attrs:
                    self.refs.append((tag, attrs[key]))
            if tag == "link" and "stylesheet" in attrs.get("rel", "").split() and "href" in attrs:
                self.refs.append((tag, attrs["href"]))

    for filename, raw in files.items():
        if filename.casefold().endswith((".html", ".htm")):
            parser = AssetParser()
            parser.feed(raw.decode("utf-8", "strict"))
            references = parser.refs
        elif filename.casefold().endswith(".css"):
            references = [("css", match.group(1).strip(" '\"")) for match in re.finditer(r"url\(([^)]+)\)", raw.decode("utf-8", "strict"), re.I)]
        else:
            references = []
        for tag, ref in references:
            if ref.startswith(("data:", "#")):
                continue
            if ref.startswith(("http://", "https://")):
                raise ValidationError("bundle executable/style/image assets may not load remotely")
            parsed = urllib.parse.urlsplit(ref)
            if parsed.scheme or parsed.netloc or ref.startswith("/") or "\\" in ref:
                raise ValidationError("bundle assets must use allowlisted relative paths")
            target = (PurePosixPath(filename).parent / urllib.parse.unquote(parsed.path)).as_posix()
            normalized = PurePosixPath(target)
            if any(part in {"..", "."} for part in normalized.parts) or normalized.as_posix() not in allowed:
                raise ValidationError("bundle references an asset outside the allowlist")


def cmd_import_bundle(args) -> int:
    try:
        descriptor = load_json(args.input)
        required = {"project_id", "revision", "source_dir", "entry", "files"}
        if set(descriptor) != required:
            raise ValidationError("bundle descriptor requires project_id, revision, source_dir, entry, files")
        project_id = descriptor["project_id"]
        revision = descriptor["revision"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,80}", revision):
            raise ValidationError("invalid project_id or revision")
        allowed_lexical = ROOT / ".local" / "imports" / project_id / revision
        source_lexical = ROOT / descriptor["source_dir"]
        chain = (ROOT / ".local", ROOT / ".local" / "imports", ROOT / ".local" / "imports" / project_id, allowed_lexical)
        if any(p.is_symlink() or getattr(p, "is_junction", lambda: False)() for p in chain):
            raise ValidationError("import root must not contain symlinks or junctions")
        allowed_root = allowed_lexical.resolve()
        source = source_lexical.resolve(strict=True)
        if source != allowed_root:
            raise ValidationError("source_dir must be the isolated .local/imports/<id>/<revision> directory")
        manifest = descriptor["files"]
        if not isinstance(manifest, list) or not 1 <= len(manifest) <= 500:
            raise ValidationError("bundle must contain between 1 and 500 allowlisted files")
        names = [entry.get("path") for entry in manifest if isinstance(entry, dict)]
        if len(names) != len(manifest) or len(set(names)) != len(names):
            raise ValidationError("bundle file paths must be unique")
        normalized_names = [unicodedata.normalize("NFKC", name).casefold() for name in names]
        if len(set(normalized_names)) != len(normalized_names):
            raise ValidationError("bundle file paths collide under case-fold/NFKC")
        content = {}
        size_total = 0
        for entry in manifest:
            raw_path = entry.get("path")
            if not isinstance(raw_path, str) or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
                raise ValidationError("each file needs a path and lowercase SHA-256")
            path = _bundle_path(raw_path, source)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValidationError("bundle checksum mismatch")
            size_total += len(raw)
            if size_total > 50 * 1024 * 1024:
                raise ValidationError("bundle exceeds the 50 MiB limit")
            content[PurePosixPath(raw_path).as_posix()] = raw
        if descriptor["entry"] not in content or not descriptor["entry"].casefold().endswith((".html", ".htm")):
            raise ValidationError("entry must be an allowlisted HTML file")
        _validate_bundle_references(content, set(content))
        dest = ROOT / "portfolio" / "public" / "demos" / project_id / revision
        if dest.exists():
            same = all((dest / name).is_file() and hashlib.sha256((dest / name).read_bytes()).hexdigest() == hashlib.sha256(raw).hexdigest() for name, raw in content.items())
            if same and {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()} == set(content):
                action = "unchanged"
            else:
                raise ValidationError("bundle revision already exists with different content; choose a new revision")
        else:
            action = "import"
        if not args.dry_run and action == "import":
            dest.parent.mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=".bundle-stage-", dir=dest.parent))
            try:
                for name, raw in content.items():
                    output = stage.joinpath(*PurePosixPath(name).parts)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(raw)
                os.replace(stage, dest)
            finally:
                if stage.exists(): shutil.rmtree(stage)
        _print({"status": "PASS", "action": action, "dry_run": args.dry_run, "file_count": len(content), "size_bytes": size_total,
                "entry": f"demos/{project_id}/{revision}/{descriptor['entry']}"}, args.json)
        return 0
    except (ValidationError, ValueError, OSError, KeyError, TypeError) as exc:
        _print({"status": "FAIL", "error": str(exc) if isinstance(exc, ValidationError) else type(exc).__name__}, args.json)
        return EXIT_DATA if isinstance(exc, ValidationError) else EXIT_IO


def cmd_audit(args) -> int:
    try:
        result = audit(ROOT, args.scope, Path(args.rules))
        result["asset_ledger"] = "not_generated; use --asset-ledger with a baseline commit" if not args.asset_ledger else None
        if args.asset_ledger:
            ledger = asset_ledger(ROOT, args.asset_ledger)
            target = ROOT / ".local" / "evidence" / "asset-ledger.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical_json(ledger))
            result["asset_ledger"] = {"path": target.relative_to(ROOT).as_posix(), "asset_count": ledger["asset_count"]}
        _print(result, True if args.json else True)
        return 0 if result["status"] == "PASS" else EXIT_AUDIT
    except AuditError as exc:
        _print({"status": "FAIL", "error": str(exc)}, True)
        return EXIT_AUDIT
    except (OSError, subprocess.SubprocessError) as exc:
        _print({"status": "FAIL", "error": type(exc).__name__}, True)
        return EXIT_IO


def cmd_serve(args) -> int:
    try:
        target, digest = build_site(ROOT, mode=args.mode)
        httpd, url, thread = serve(target, port=args.port, open_browser=args.open_browser)
        print(json.dumps({"status": "SERVING", "mode": args.mode, "url": url, "pid": os.getpid(), "digest": digest}, ensure_ascii=False))
        try:
            httpd.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)
        print("Stopped portfolio server.")
        return 0
    except (BuildError, SafeServerError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return EXIT_BOUNDARY
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        return EXIT_IO


def cmd_verify_links(args) -> int:
    if not args.remote:
        _print({"status": "UNVERIFIED", "reason": "--remote is required to perform network reads"}, args.json)
        return EXIT_DATA
    try:
        registry = load_registry(ROOT)
        results = []
        for project in registry["projects"]:
            for link in project["links"]:
                if link["kind"] not in {"repo", "external_https"}:
                    continue
                checked = verify_url(link["url"], timeout=5.0)
                results.append({"project_id": project["project_id"], "link_id": link["link_id"], "status": checked["status"], **checked})
        report = {"status": "PASS" if all(item["status"] in {"VERIFIED", "UNVERIFIED"} for item in results) else "FAIL", "results": results}
        _print(report, args.json)
        return 0 if report["status"] == "PASS" else EXIT_BOUNDARY
    except ValidationError as exc:
        _print({"status": "FAIL", "error": str(exc)}, args.json)
        return EXIT_DATA


def build_parser():
    parser = argparse.ArgumentParser(description="Local-first, data-driven engineering portfolio hub")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor"); doctor.add_argument("--json", action="store_true"); doctor.set_defaults(run=cmd_doctor)
    validate = commands.add_parser("validate"); validate.add_argument("--mode", choices=["public", "local"], required=True); validate.add_argument("--offline", action="store_true"); validate.add_argument("--json", action="store_true"); validate.set_defaults(run=cmd_validate)
    build = commands.add_parser("build"); build.add_argument("--mode", choices=["public", "local"], required=True); build.add_argument("--json", action="store_true"); build.set_defaults(run=cmd_build)
    upsert = commands.add_parser("upsert"); upsert.add_argument("--input", required=True); upsert.add_argument("--dry-run", action="store_true"); upsert.add_argument("--previous-id"); upsert.add_argument("--json", action="store_true"); upsert.set_defaults(run=cmd_upsert)
    bundle = commands.add_parser("import-bundle"); bundle.add_argument("--input", required=True); bundle.add_argument("--dry-run", action="store_true"); bundle.add_argument("--json", action="store_true"); bundle.set_defaults(run=cmd_import_bundle)
    audit_parser = commands.add_parser("audit"); audit_parser.add_argument("--mode", choices=["public"], required=True); audit_parser.add_argument("--scope", choices=["all", "artifact"], required=True); audit_parser.add_argument("--rules", required=True); audit_parser.add_argument("--asset-ledger"); audit_parser.add_argument("--json", action="store_true"); audit_parser.set_defaults(run=cmd_audit)
    serve_parser = commands.add_parser("serve"); serve_parser.add_argument("--mode", choices=["public", "local"], required=True); serve_parser.add_argument("--port", type=int, default=8765); serve_parser.add_argument("--open", dest="open_browser", action="store_true"); serve_parser.add_argument("--no-open", dest="open_browser", action="store_false"); serve_parser.set_defaults(open_browser=False, run=cmd_serve)
    links = commands.add_parser("verify-links"); links.add_argument("--remote", action="store_true"); links.add_argument("--json", action="store_true"); links.set_defaults(run=cmd_verify_links)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
