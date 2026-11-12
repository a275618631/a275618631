import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from portfolio import hub
from portfolio.lib.build import build_site


REPO = Path(__file__).resolve().parents[2]


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        (self.root / "portfolio").mkdir(parents=True)
        shutil.copy2(REPO / "portfolio" / "projects.json", self.root / "portfolio" / "projects.json")
        shutil.copytree(REPO / "portfolio" / "web", self.root / "portfolio" / "web")
        (self.root / "portfolio" / "public").mkdir(parents=True)
        if (REPO / "portfolio" / "public").exists():
            shutil.copytree(REPO / "portfolio" / "public", self.root / "portfolio" / "public", dirs_exist_ok=True)
        self.registry_path = self.root / "portfolio" / "projects.json"

    def tearDown(self):
        self.temp.cleanup()

    def registry(self):
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def save(self, data):
        self.registry_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_data_only_project_and_feature_changes_do_not_touch_ui_code(self):
        app_hash = hashlib.sha256((self.root / "portfolio" / "web" / "app.js").read_bytes()).hexdigest()
        template_hash = hashlib.sha256((self.root / "portfolio" / "web" / "index.template.html").read_bytes()).hexdigest()
        registry = self.registry()
        project = copy.deepcopy(registry["projects"][0])
        project["project_id"] = "synthetic-extension"
        project["title"] = "合成接入作品"
        project["categories"] = ["新分類"]
        project["tags"] = ["新標籤"]
        project["snapshot"]["public_ref"] = None
        project["snapshot"]["revision"] = "local-demo"
        project["evidence"]["status"] = "unverified"
        project["links"] = []
        registry["projects"].append(project)
        self.save(registry)
        output, _ = build_site(self.root)
        listing = json.loads((output / "projects.json").read_text(encoding="utf-8"))
        added = next(item for item in listing["projects"] if item["project_id"] == "synthetic-extension")
        self.assertEqual(added["categories"], ["新分類"])
        self.assertIn("synthetic-extension", (output / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(app_hash, hashlib.sha256((self.root / "portfolio" / "web" / "app.js").read_bytes()).hexdigest())
        self.assertEqual(template_hash, hashlib.sha256((self.root / "portfolio" / "web" / "index.template.html").read_bytes()).hexdigest())
        added["capabilities"].append({"id": "planned-export", "title": "匯出功能", "description": "稍後實作。", "status": "planned"})
        added["snapshot"]["revision"] = "v2"
        registry = self.registry()
        registry["projects"] = [added if item["project_id"] == added["project_id"] else item for item in registry["projects"]]
        self.save(registry)
        output, _ = build_site(self.root)
        self.assertIn("planned", (output / "index.html").read_text(encoding="utf-8"))
        self.assertIn("v2", (output / "index.html").read_text(encoding="utf-8"))

    def test_local_only_project_never_enters_public_output(self):
        overlay = {
            "schema_version": "1.0", "bindings": [], "local_projects": [{
                "project_id": "private-local-demo", "title": "本機合成作品", "summary": "僅本機展示。", "categories": ["Local"], "tags": ["local"],
                "featured": False, "lifecycle": "active", "capabilities": [{"id": "demo", "title": "本機 Demo", "description": "使用者自行啟動。", "status": "partial"}],
                "snapshot": {"revision": "local", "public_ref": None, "reviewed_at": "2026-11-12"},
                "evidence": {"status": "unverified", "scope": "本機尚未公開。", "reference_urls": []},
                "links": [{"link_id": "local-preview", "label": "本機預覽", "kind": "local_http", "status": "manual", "binding_id": "preview"}],
            }],
        }
        overlay_path = self.root / ".local" / "projects.local.json"
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        overlay_path.write_text(json.dumps(overlay, ensure_ascii=False), encoding="utf-8")
        local, _ = build_site(self.root, "local")
        public, _ = build_site(self.root, "public")
        self.assertIn("private-local-demo", (local / "projects.json").read_text(encoding="utf-8"))
        for path in public.rglob("*"):
            if path.is_file() and path.suffix.casefold() in {".html", ".json", ".js", ".css"}:
                self.assertNotIn("private-local-demo", path.read_text(encoding="utf-8"))
        self.assertNotIn("source_path", (local / "projects.json").read_text(encoding="utf-8"))

    def test_external_and_static_bundle_links_use_relative_paths(self):
        data = self.registry()
        project = data["projects"][0]
        project["links"].append({"link_id": "static-sample", "label": "合成 Demo", "kind": "static_bundle", "status": "available", "path": "demos/sample/1/index.html"})
        self.save(data)
        demo = self.root / "portfolio" / "public" / "demos" / "sample" / "1"
        demo.mkdir(parents=True)
        (demo / "index.html").write_text("<h1>demo</h1>", encoding="utf-8")
        output, _ = build_site(self.root)
        self.assertTrue((output / "demos" / "sample" / "1" / "index.html").is_file())
        self.assertIn("demos/sample/1/index.html", (output / "projects.json").read_text(encoding="utf-8"))
        self.assertIn("href=\"demos/sample/1/index.html\"", (output / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
