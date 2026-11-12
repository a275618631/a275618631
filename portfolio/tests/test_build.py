import json
import shutil
import tempfile
import unittest
from pathlib import Path

from portfolio.lib.build import BuildError, build_site


REPO = Path(__file__).resolve().parents[2]


def copy_fixture_root(target: Path) -> Path:
    (target / "portfolio").mkdir(parents=True)
    shutil.copy2(REPO / "portfolio" / "projects.json", target / "portfolio" / "projects.json")
    shutil.copytree(REPO / "portfolio" / "web", target / "portfolio" / "web")
    (target / "portfolio" / "public").mkdir(parents=True)
    if (REPO / "portfolio" / "public").exists():
        shutil.copytree(REPO / "portfolio" / "public", target / "portfolio" / "public", dirs_exist_ok=True)
    return target


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = copy_fixture_root(Path(self.temp.name) / "repo")

    def tearDown(self):
        self.temp.cleanup()

    def test_public_build_is_deterministic_and_has_static_fallback(self):
        first, digest_a = build_site(self.root)
        html = (first / "index.html").read_text(encoding="utf-8")
        self.assertIn("設備知識庫與地端診斷助手", html)
        self.assertIn("noscript", html)
        _, digest_b = build_site(self.root)
        self.assertEqual(digest_a, digest_b)

    def test_public_build_never_reads_or_leaks_overlay(self):
        _, baseline = build_site(self.root)
        overlay = self.root / ".local" / "projects.local.json"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text("not-json COMPANY_SENTINEL private/path", encoding="utf-8")
        _, after = build_site(self.root, "public")
        self.assertEqual(baseline, after)
        self.assertNotIn("COMPANY_SENTINEL", (self.root / ".local" / "dist" / "public" / "projects.json").read_text(encoding="utf-8"))

    def test_local_projection_contains_overlay_data_but_not_source_path(self):
        overlay = {
            "schema_version": "1.0",
            "bindings": [{"project_id": "factory-knowledge-grounded-rag", "binding_id": "local-demo", "url": "http://127.0.0.1:8766/demo", "source_path": "C:/private/worktree"}],
            "local_projects": [],
        }
        path = self.root / ".local" / "projects.local.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(overlay), encoding="utf-8")
        out, _ = build_site(self.root, "local")
        rendered = (out / "projects.json").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:8766/demo", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:/private/worktree", rendered)

    def test_unknown_existing_file_and_root_output_are_preserved(self):
        output, _ = build_site(self.root)
        unknown = output / "keep-me.txt"
        unknown.write_text("user data", encoding="utf-8")
        with self.assertRaises(BuildError):
            build_site(self.root)
        self.assertEqual(unknown.read_text(encoding="utf-8"), "user data")
        with self.assertRaises(BuildError):
            build_site(self.root, out=self.root)

    def test_public_projection_strips_local_http_links(self):
        registry_path = self.root / "portfolio" / "projects.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        data["projects"][0]["links"].append({"link_id": "local-preview-alt", "label": "Local Demo", "kind": "local_http", "status": "manual", "binding_id": "demo"})
        registry_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        out, _ = build_site(self.root)
        self.assertNotIn("local-preview-alt", (out / "projects.json").read_text(encoding="utf-8"))

    def test_expired_https_link_is_inert_and_offline_build_succeeds(self):
        registry_path = self.root / "portfolio" / "projects.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        data["projects"][0]["links"].append({
            "link_id": "expired-demo", "label": "過期 Demo", "kind": "external_https",
            "status": "expired", "url": "https://example.invalid/demo", "expires_at": "2020-01-01T00:00:00Z",
        })
        registry_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        out, digest = build_site(self.root, "public")
        rendered = (out / "index.html").read_text(encoding="utf-8")
        self.assertTrue(digest)
        self.assertIn("過期 Demo（已過期）", rendered)
        self.assertNotIn('href="https://example.invalid/demo"', rendered)


if __name__ == "__main__":
    unittest.main()
