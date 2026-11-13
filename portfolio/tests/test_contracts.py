import copy
import json
import re
import unittest
from pathlib import Path

from portfolio.lib.contracts import (
    SCHEMA_VERSION,
    ValidationError,
    load_json,
    validate_bundle_path,
    validate_link,
    validate_overlay,
    validate_registry,
    validate_url,
)


ROOT = Path(__file__).resolve().parents[2]


class RegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(ROOT / "portfolio" / "projects.json")

    def test_initial_registry_has_exact_nine_stable_projects(self):
        result = validate_registry(self.registry, root=ROOT)
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(len(result["projects"]), 9)
        ids = [item["project_id"] for item in result["projects"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("npi", ids)

    def test_all_initial_repo_links_pin_full_sha(self):
        validate_registry(self.registry, root=ROOT)
        for project in self.registry["projects"]:
            self.assertTrue(project["snapshot"]["public_ref"])
            for link in project["links"]:
                if link["kind"] == "repo":
                    self.assertIn(project["snapshot"]["public_ref"], link["url"])

    def test_repo_link_sha_must_match_snapshot_and_null_snapshot_cannot_have_repo_link(self):
        from portfolio.lib.contracts import validate_project
        project = copy.deepcopy(self.registry["projects"][0])
        validate_project(project)
        project["snapshot"]["public_ref"] = "0" * 40
        with self.assertRaises(ValidationError):
            validate_project(project)
        project = copy.deepcopy(self.registry["projects"][0])
        project["snapshot"]["public_ref"] = None
        project["evidence"]["status"] = "partial"
        with self.assertRaises(ValidationError):
            validate_project(project)

    def test_duplicate_project_capability_and_link_ids_are_rejected(self):
        duplicate_project = copy.deepcopy(self.registry)
        duplicate_project["projects"].append(copy.deepcopy(duplicate_project["projects"][0]))
        with self.assertRaises(ValidationError):
            validate_registry(duplicate_project)

        duplicate_capability = copy.deepcopy(self.registry)
        duplicate_capability["projects"][0]["capabilities"].append(copy.deepcopy(duplicate_capability["projects"][0]["capabilities"][0]))
        with self.assertRaises(ValidationError):
            validate_registry(duplicate_capability)

        duplicate_link = copy.deepcopy(self.registry)
        duplicate_link["projects"][0]["links"].append(copy.deepcopy(duplicate_link["projects"][0]["links"][0]))
        with self.assertRaises(ValidationError):
            validate_registry(duplicate_link)

    def test_short_sha_unknown_schema_and_control_text_rejected(self):
        short_sha = copy.deepcopy(self.registry)
        short_sha["projects"][0]["snapshot"]["public_ref"] = "abc123"
        with self.assertRaises(ValidationError):
            validate_registry(short_sha)
        bad_schema = copy.deepcopy(self.registry)
        bad_schema["schema_version"] = "2.0"
        with self.assertRaises(ValidationError):
            validate_registry(bad_schema)
        control = copy.deepcopy(self.registry)
        control["projects"][0]["title"] = "bad\x01title"
        with self.assertRaises(ValidationError):
            validate_registry(control)
        invalid_date = copy.deepcopy(self.registry)
        invalid_date["projects"][0]["snapshot"]["reviewed_at"] = "2026-99-45"
        with self.assertRaises(ValidationError):
            validate_registry(invalid_date)

    def test_four_link_kinds_have_explicit_contracts(self):
        base = {"link_id":"demo-link","label":"Demo","status":"available"}
        repo = dict(base, kind="repo", url="https://github.com/a275618631/a275618631/tree/308063538eaec8df533416b3972039551f04677d")
        external = dict(base, kind="external_https", url="https://example.com/demo")
        local = dict(base, kind="local_http", binding_id="local-demo")
        bundle = dict(base, kind="static_bundle", path="demos/sample/index.html")
        for item in (repo, external, local, bundle):
            validate_link(item, project_id="sample-project")
        with self.assertRaises(ValidationError):
            validate_link(dict(base, kind="repo", url="https://github.com/a275618631/a275618631/tree/main"))
        with self.assertRaises(ValidationError):
            validate_link(dict(base, kind="external_https", url="javascript:alert(1)"))

    def test_url_and_bundle_boundaries(self):
        validate_url("https://example.com/demo?view=1#top", "external_https")
        validate_url("http://127.0.0.1:8765/demo", "local_http")
        for url in ("file:///secret", "https://user:pass@example.com", "https://example.com/?token=abc", "http://10.0.0.2:9"):
            with self.assertRaises(ValidationError):
                validate_url(url, "external_https")
        with self.assertRaises(ValidationError):
            validate_url("https://127.0.0.1:8765", "local_http")
        validate_bundle_path("demos/sample/index.html")
        for path in ("../secret.txt", "demos/%2e%2e/secret.txt", "/absolute.html", "C:/absolute.html", "demos//index.html"):
            with self.assertRaises(ValidationError):
                validate_bundle_path(path)

    def test_local_overlay_adds_projects_but_public_registry_is_unchanged(self):
        overlay = {
            "schema_version": "1.0", "bindings": [{"project_id":"factory-knowledge-grounded-rag","binding_id":"local-demo","url":"http://127.0.0.1:8766/demo"}],
            "local_projects": [{
                "project_id":"local-only-demo","title":"本機測試作品","summary":"只供本機驗證的合成作品。","categories":["系統整合"],"tags":["Local"],"featured":False,"lifecycle":"active",
                "capabilities":[{"id":"demo","title":"本機頁面","description":"由使用者自行啟動。","status":"partial"}],
                "snapshot":{"revision":"local","public_ref":None,"reviewed_at":"2026-11-11"},
                "evidence":{"status":"unverified","scope":"尚無公開版本。","reference_urls":[]},
                "links":[{"link_id":"local-demo","label":"本機 Demo","kind":"local_http","status":"manual","binding_id":"local-demo"}]
            }]
        }
        result = validate_registry(self.registry, mode="local", overlay=overlay)
        self.assertEqual(len(result["projects"]), 10)
        self.assertEqual(len(self.registry["projects"]), 9)
        with self.assertRaises(ValidationError):
            validate_overlay({**overlay, "bindings":[{"project_id":"factory-knowledge-grounded-rag","binding_id":"unknown","url":"http://127.0.0.1:8766"}]}, registry=self.registry)
        with self.assertRaises(ValidationError):
            validate_overlay({**overlay, "bindings":[{"project_id":"unlisted-project","binding_id":"local-demo","url":"http://127.0.0.1:8766"}]}, registry=self.registry)


if __name__ == "__main__":
    unittest.main()
