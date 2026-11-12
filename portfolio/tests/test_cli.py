import copy
import contextlib
import io
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from portfolio import hub


REPO = Path(__file__).resolve().parents[2]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        (self.root / "portfolio").mkdir(parents=True)
        shutil.copy2(REPO / "portfolio" / "projects.json", self.root / "portfolio" / "projects.json")
        shutil.copytree(REPO / "portfolio" / "web", self.root / "portfolio" / "web")
        (self.root / "portfolio" / "public").mkdir(parents=True)
        if (REPO / "portfolio" / "public").exists():
            shutil.copytree(REPO / "portfolio" / "public", self.root / "portfolio" / "public", dirs_exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, function, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(hub, "ROOT", self.root), patch.object(hub, "PORTFOLIO", self.root / "portfolio"):
            return function(SimpleNamespace(**kwargs))

    def descriptor(self):
        project = copy.deepcopy(json.loads((self.root / "portfolio" / "projects.json").read_text(encoding="utf-8"))["projects"][0])
        project.update(project_id="new-synthetic-work", title="新合成作品", featured=False)
        project["snapshot"].update(public_ref=None, revision="local-draft")
        project["evidence"].update(status="unverified", scope="合成 CLI 測試。")
        project["links"] = []
        path = Path(self.temp.name) / "project.json"
        path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
        return path, project

    def test_public_validate_ignores_corrupt_overlay_but_local_rejects_it(self):
        overlay = self.root / ".local" / "projects.local.json"
        overlay.parent.mkdir(parents=True)
        overlay.write_text("{corrupt", encoding="utf-8")
        self.assertEqual(self.run_cmd(hub.cmd_validate, mode="public", offline=True, json=True), 0)
        self.assertEqual(self.run_cmd(hub.cmd_validate, mode="local", offline=True, json=True), hub.EXIT_DATA)

    def test_upsert_dry_run_add_update_and_explicit_rename_rejection(self):
        descriptor, project = self.descriptor()
        registry_path = self.root / "portfolio" / "projects.json"
        before = registry_path.read_bytes()
        self.assertEqual(self.run_cmd(hub.cmd_upsert, input=str(descriptor), dry_run=True, previous_id=None, json=True), 0)
        self.assertEqual(registry_path.read_bytes(), before)
        self.assertEqual(self.run_cmd(hub.cmd_upsert, input=str(descriptor), dry_run=False, previous_id=None, json=True), 0)
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertIn("new-synthetic-work", [p["project_id"] for p in data["projects"]])
        project["title"] = "更新後作品"
        descriptor.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.run_cmd(hub.cmd_upsert, input=str(descriptor), dry_run=False, previous_id=None, json=True), 0)
        self.assertEqual(self.run_cmd(hub.cmd_upsert, input=str(descriptor), dry_run=False, previous_id="old-id", json=True), hub.EXIT_DATA)

    def make_bundle(self, *, mismatch=False):
        source = self.root / ".local" / "imports" / "sample-work" / "1.0.0"
        source.mkdir(parents=True, exist_ok=True)
        files = {"index.html": b'<!doctype html><html><link rel="stylesheet" href="style.css"><script src="app.js"></script></html>', "style.css": b"body { color: #123; }", "app.js": b"document.title='Synthetic';"}
        entries = []
        for name, raw in files.items():
            (source / name).write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            entries.append({"path": name, "sha256": "0" * 64 if mismatch and name == "app.js" else digest})
        descriptor = {"project_id": "sample-work", "revision": "1.0.0", "source_dir": ".local/imports/sample-work/1.0.0", "entry": "index.html", "files": entries}
        path = Path(self.temp.name) / ("bundle-bad.json" if mismatch else "bundle.json")
        path.write_text(json.dumps(descriptor), encoding="utf-8")
        return path

    def test_bundle_import_dry_run_real_import_idempotency_and_checksum(self):
        descriptor = self.make_bundle()
        dest = self.root / "portfolio" / "public" / "demos" / "sample-work" / "1.0.0"
        self.assertEqual(self.run_cmd(hub.cmd_import_bundle, input=str(descriptor), dry_run=True, json=True), 0)
        self.assertFalse(dest.exists())
        self.assertEqual(self.run_cmd(hub.cmd_import_bundle, input=str(descriptor), dry_run=False, json=True), 0)
        self.assertEqual(self.run_cmd(hub.cmd_import_bundle, input=str(descriptor), dry_run=False, json=True), 0)
        self.assertTrue((dest / "index.html").is_file())
        bad = self.make_bundle(mismatch=True)
        self.assertEqual(self.run_cmd(hub.cmd_import_bundle, input=str(bad), dry_run=False, json=True), hub.EXIT_DATA)

    def test_bundle_remote_or_unlisted_assets_are_rejected(self):
        descriptor = self.make_bundle()
        data = json.loads(descriptor.read_text(encoding="utf-8"))
        data["project_id"] = "unsafe-work"
        data["source_dir"] = ".local/imports/sample-work/1.0.0"
        index = self.root / ".local" / "imports" / "sample-work" / "1.0.0" / "index.html"
        index.write_text('<script src="https://cdn.example/script.js"></script>', encoding="utf-8")
        data["files"][0]["sha256"] = hashlib.sha256(index.read_bytes()).hexdigest()
        descriptor.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cmd(hub.cmd_import_bundle, input=str(descriptor), dry_run=True, json=True), hub.EXIT_DATA)


if __name__ == "__main__":
    unittest.main()
