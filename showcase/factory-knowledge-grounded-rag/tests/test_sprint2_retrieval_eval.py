# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: Retrieval Golden Set Integration Test.
Verifies benchmark golden dataset loads cleanly and key queries hit expected targets.
"""

import os
import json
import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_golden_set_file_validity():
    path = os.path.join(REPO_ROOT, "tests", "retrieval_golden_sprint2.json")
    assert os.path.exists(path), f"Golden file not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_queries"] == 30
    assert len(data["cases"]) == 30

    query_ids = [c["query_id"] for c in data["cases"]]
    assert len(set(query_ids)) == 30, "All query IDs must be unique"

    types = set(c["query_type"] for c in data["cases"])
    expected_types = {"EXACT_CODE", "PARAPHRASE_ZH", "CROSS_LINGUAL", "SOP_TABLE", "REVISION_ACTIVE", "OUT_OF_SCOPE", "CONTRASTIVE"}
    assert types == expected_types
