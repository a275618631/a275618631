# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: Qdrant Vector Store Adapter.
Validates BaseVectorStoreV3 contracts, deterministic UUIDv5 mapping, and payload filtering.
"""

import os
import shutil
import pytest
from core.interfaces import BaseVectorStoreV3
from adapters.vector.qdrant_store import QdrantStore


TEST_STORAGE_PATH = "./data/test_qdrant_tmp"


@pytest.fixture(autouse=True)
def cleanup():
    if os.path.exists(TEST_STORAGE_PATH):
        try:
            shutil.rmtree(TEST_STORAGE_PATH)
        except Exception:
            pass
    yield
    if os.path.exists(TEST_STORAGE_PATH):
        try:
            shutil.rmtree(TEST_STORAGE_PATH)
        except Exception:
            pass


def test_qdrant_store_contracts_and_deterministic_uuid():
    store = QdrantStore(
        collection_name="test_sprint2_coll",
        dimension=4,
        distance="cosine",
        mode="local",
        storage_path=TEST_STORAGE_PATH
    )
    assert isinstance(store, BaseVectorStoreV3)

    # Deterministic UUIDv5 verification
    cid = "DOC-08_Y52-P1-3025"
    uuid1 = store.chunk_id_to_uuid(cid)
    uuid2 = store.chunk_id_to_uuid(cid)
    assert uuid1 == uuid2
    assert len(uuid1) == 36

    # Upsert vectors
    ids = ["C1", "C2", "C3"]
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0]
    ]
    payloads = [
        {"document_id": "DOC-01", "approval_status": "approved", "revision": "Rev.A"},
        {"document_id": "DOC-02", "approval_status": "obsolete", "revision": "Rev.B"},
        {"document_id": "DOC-03", "approval_status": "approved", "revision": "Rev.C"}
    ]
    store.upsert_vectors(ids, vectors, payloads)
    assert store.count_points() == 3

    # Idempotent re-upsert: should NOT increase points
    store.upsert_vectors(ids, vectors, payloads)
    assert store.count_points() == 3

    # Search with filter
    res_active = store.search_vector(
        [1.0, 0.0, 0.0, 0.0],
        top_k=5,
        filters={"exclude_obsolete": True}
    )
    assert len(res_active) == 2
    assert all(r["approval_status"] != "obsolete" for r in res_active)

    # Delete point
    store.delete_vectors(["C1"])
    assert store.count_points() == 2
    store.client.close()
