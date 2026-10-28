# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: Qdrant Docker Server Integration Test.
Validates BaseVectorStoreV3 contracts over real HTTP connection to Qdrant Docker container.
"""

import pytest
import urllib.request
from core.interfaces import BaseVectorStoreV3
from adapters.vector.qdrant_store import QdrantStore

SERVER_URL = "http://127.0.0.1:6333"


def is_qdrant_server_online() -> bool:
    try:
        with urllib.request.urlopen(f"{SERVER_URL}/healthz", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.mark.skipif(not is_qdrant_server_online(), reason="Qdrant Docker server is not online")
def test_qdrant_server_contracts_and_http_search():
    coll_name = "test_sprint2_server_unit"
    store = QdrantStore(
        collection_name=coll_name,
        dimension=4,
        distance="cosine",
        mode="server",
        url=SERVER_URL
    )
    assert isinstance(store, BaseVectorStoreV3)
    assert store.mode == "server"

    # Upsert test points
    ids = ["SERVER_C1", "SERVER_C2"]
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ]
    payloads = [
        {"document_id": "SRV_DOC1", "approval_status": "approved", "exclude_obsolete": False},
        {"document_id": "SRV_DOC2", "approval_status": "obsolete", "exclude_obsolete": True}
    ]

    store.upsert_vectors(ids, vectors, payloads)
    assert store.count_points() >= 2

    # Query with filter
    res = store.search_vector(
        [1.0, 0.0, 0.0, 0.0],
        top_k=2,
        filters={"exclude_obsolete": True}
    )
    assert len(res) >= 1
    assert all(r.get("exclude_obsolete") is not True for r in res)

    # Clean up test points
    store.delete_vectors(ids)
    store.client.close()
