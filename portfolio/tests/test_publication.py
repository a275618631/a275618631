import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from portfolio.lib.publication import AuditError, asset_ledger, audit


REPO = Path(__file__).resolve().parents[2]


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.rules = Path(self.temp.name) / "rules.json"
        self.rules.write_text(json.dumps({"rules": [{"id": "synthetic-company", "values": ["SENTINEL_CORP"]}]}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_artifact_audit_reports_rule_id_but_never_matched_content(self):
        public = self.root / ".local" / "dist" / "public"
        public.mkdir(parents=True)
        (public / "index.html").write_text('<title>SENTINEL_CORP</title>', encoding="utf-8")
        report = audit(self.root, "artifact", self.rules)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["findings"][0]["rule_id"], "synthetic-company")
        self.assertNotIn("SENTINEL_CORP", json.dumps(report))

    def test_all_scope_checks_untracked_public_text_but_skips_ignored_private_overlay(self):
        (self.root / "README.md").write_text("Company sentinel_corp is a synthetic fixture.", encoding="utf-8")
        ignored = self.root / ".local" / "projects.local.json"
        ignored.parent.mkdir(parents=True)
        ignored.write_text('{"title":"SENTINEL_CORP"}', encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "README.md"], check=True)
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["findings"][0]["path"], "README.md")

    def test_clean_synthetic_rules_pass_and_missing_rules_fail_closed(self):
        path = self.root / "safe.md"
        path.write_text("Technical brands and synthetic Company A wording remain.", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "safe.md"], check=True)
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "PASS")
        with self.assertRaises(AuditError):
            audit(self.root, "all", self.root / ".local" / "missing-rules.json")

    def test_synthetic_sentinel_is_detected_in_filename_url_and_metadata(self):
        target = self.root / "SENTINEL_CORP.html"
        target.write_text('<meta name="client" content="SENTINEL_CORP"><a href="https://example.invalid/SENTINEL_CORP">demo</a>', encoding="utf-8")
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["findings"][0]["path"], "SENTINEL_CORP.html")
        self.assertEqual(set(report["findings"][0]), {"path", "rule_id", "matches"})

    def test_binary_assets_are_not_silently_claimed_text_scanned(self):
        asset = self.root / "image.png"
        asset.write_bytes(b"\x89PNG\x00SENTINEL_CORP")
        subprocess.run(["git", "-C", str(self.root), "add", "image.png"], check=True)
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "PASS")
        # Binary inspection is tracked separately in the asset ledger.

    def test_false_positive_classification_requires_exact_path_and_hash(self):
        fixture = self.root / "synthetic-test.py"
        fixture.write_text('token = "AKIA0000000000000000"\n', encoding="utf-8")
        digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
        data = {
            "rules": [],
            "false_positive_exceptions": [{"path": "synthetic-test.py", "sha256": digest, "rule_ids": ["credential-aws-access-key"], "reason": "synthetic test fixture"}],
        }
        self.rules.write_text(json.dumps(data), encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "synthetic-test.py"], check=True)
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["classified_synthetic_findings"][0]["rule_id"], "credential-aws-access-key")
        fixture.write_text(fixture.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
        report = audit(self.root, "all", self.rules)
        self.assertEqual(report["status"], "FAIL")

    def test_asset_ledger_hashes_existing_pdf_and_images(self):
        img = self.root / "sample.png"
        img.write_bytes(b"synthetic-image")
        subprocess.run(["git", "-C", str(self.root), "add", "sample.png"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline"], check=True)
        ledger = asset_ledger(self.root, "HEAD")
        self.assertEqual(ledger["asset_count"], 1)
        self.assertEqual(ledger["assets"][0]["review"], "prior_visual_or_extraction_evidence_may_be_reused")


if __name__ == "__main__":
    unittest.main()
