import http.client
import socket
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from portfolio.lib.server import SafeServerError, create_server, health_check


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text("<!doctype html><html><body>local hub</body></html>", encoding="utf-8")
        (self.root / "asset.txt").write_text("asset", encoding="utf-8")
        self.server, self.url = create_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_loopback_get_head_health_and_no_directory_listing(self):
        self.assertTrue(self.url.startswith("http://127.0.0.1:"))
        with urlopen(self.url, timeout=2) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"local hub", response.read())
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=2)
        connection.request("HEAD", "/asset.txt")
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"")
        connection.close()
        self.assertTrue(health_check(self.url))
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.url + "nested/", timeout=2)
        caught.exception.close()

    def test_traversal_double_encoding_dotfiles_and_unknown_paths_are_rejected(self):
        root_connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=2)
        for path in ("/%2e%2e/secret", "/%252e%252e/secret", "/.env", "/missing"):
            root_connection.request("GET", path)
            response = root_connection.getresponse()
            response.read()
            self.assertIn(response.status, {403, 404}, path)
        root_connection.close()

    def test_occupied_port_uses_fallback_without_terminating_listener(self):
        occupied = socket.socket()
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        requested = occupied.getsockname()[1]
        other, url = create_server(self.root, requested)
        self.assertNotEqual(other.server_address[1], requested)
        self.assertEqual(occupied.getsockname()[1], requested)
        other.server_close()
        occupied.close()

    def test_root_symlink_is_rejected(self):
        alias = self.root / "alias"
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlink creation is unavailable")
        with self.assertRaises(SafeServerError):
            create_server(alias, 0)

    def test_root_junction_is_rejected_when_supported(self):
        target = self.root / "junction-target"
        target.mkdir()
        alias = self.root / "junction-alias"
        try:
            subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(target)], check=True, capture_output=True)
            if not alias.is_junction():
                self.skipTest("directory junction creation is unavailable")
        except (OSError, NotImplementedError, subprocess.CalledProcessError):
            self.skipTest("directory junction creation is unavailable")
        with self.assertRaises(SafeServerError):
            create_server(alias, 0)

    def test_path_symlink_guard_rejects_when_filesystem_creation_is_unavailable(self):
        alias = self.root / "forced-symlink"
        alias.mkdir()
        original = Path.is_symlink
        def pretend_symlink(path):
            return True if path == alias else original(path)
        with patch.object(Path, "is_symlink", pretend_symlink):
            with self.assertRaises(SafeServerError):
                create_server(alias, 0)


if __name__ == "__main__":
    unittest.main()
