"""Loopback-only file server for generated portfolio outputs."""

from __future__ import annotations

import mimetypes
import os
import socket
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SafeServerError(ValueError):
    pass


def _decode_request_path(raw_path: str) -> str:
    if "\\" in raw_path or "\x00" in raw_path or any(ord(c) < 32 for c in raw_path):
        raise SafeServerError("invalid path")
    decoded = raw_path
    for _ in range(4):
        newer = unquote(decoded, errors="strict")
        if newer == decoded:
            break
        decoded = newer
    if "%" in decoded or "\\" in decoded or "\x00" in decoded or any(ord(c) < 32 for c in decoded):
        raise SafeServerError("invalid encoded path")
    parts = decoded.split("/")
    if any(part in {".", ".."} for part in parts) or any(part.startswith(".") for part in parts if part):
        raise SafeServerError("dot segments and dotfiles are not served")
    return decoded


def make_handler(output_root: Path):
    root = output_root.resolve(strict=True)
    if not root.is_dir() or output_root.is_symlink() or getattr(output_root, "is_junction", lambda: False)():
        raise SafeServerError("output root must be a real generated directory")

    class Handler(BaseHTTPRequestHandler):
        server_version = "PortfolioHub/1.0"
        sys_version = ""

        def _respond(self, include_body: bool) -> None:
            try:
                parsed = urlsplit(self.path)
                if parsed.scheme or parsed.netloc or parsed.query:
                    raise SafeServerError("unsupported request target")
                path = _decode_request_path(parsed.path)
                if path in {"", "/"}:
                    path = "/index.html"
                elif path.endswith("/"):
                    path = path + "index.html"
                candidate = (root / path.lstrip("/")).resolve(strict=True)
                if root not in candidate.parents and candidate != root:
                    raise SafeServerError("path escapes generated output")
                relative = candidate.relative_to(root)
                if any(part.startswith(".") for part in relative.parts) or not candidate.is_file():
                    raise FileNotFoundError
                # Refuse a symlink at any traversed component, including Windows junctions.
                current = root
                for segment in relative.parts:
                    current = current / segment
                    if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                        raise SafeServerError("symlink targets are not served")
                body = candidate.read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            except (SafeServerError, OSError, UnicodeError):
                self.send_error(403)
                return
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json", "image/svg+xml"}:
                content_type += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def do_GET(self):
            self._respond(True)

        def do_HEAD(self):
            self._respond(False)

        def log_message(self, _format, *_args):
            return

    return Handler


def create_server(output_root: Path, port: int = 8765) -> tuple[ThreadingHTTPServer, str]:
    if port < 0 or port > 65535:
        raise SafeServerError("port must be between 0 and 65535")
    ports = [port] if port == 0 else list(dict.fromkeys([*range(port, min(port + 11, 65536)), 0]))
    last_error: OSError | None = None
    handler = make_handler(output_root)
    for candidate in ports:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), handler)
            server.daemon_threads = True
            server.timeout = 0.5
            actual = server.server_address[1]
            return server, f"http://127.0.0.1:{actual}/"
        except OSError as exc:
            last_error = exc
    raise SafeServerError(f"could not bind loopback port: {last_error}")


def health_check(url: str, timeout: float = 3.0) -> bool:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200 and "<html" in response.read(2048).decode("utf-8", "ignore").lower()
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def serve(output_root: Path, port: int = 8765, open_browser: bool = False) -> tuple[ThreadingHTTPServer, str, threading.Thread]:
    server, url = create_server(output_root, port)
    thread = threading.Thread(target=server.serve_forever, name="portfolio-hub-http", daemon=True)
    thread.start()
    if not health_check(url):
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        raise SafeServerError("loopback health check failed")
    if open_browser:
        import webbrowser

        webbrowser.open(url, new=2)
    return server, url, thread
