# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: Dense Retriever Adapter.
Validates BaseRetriever contract and NormalizedBlock enrichment.
"""

import os
import shutil
import pytest
from core.interfaces import BaseRetriever
from core.schema import NormalizedBlock
from adapters.embedding.fastembed_embedder import FastEmbedEmbedder
from adapters.vector.qdrant_store import QdrantStore
from adapters.retrieval.dense_retriever import DenseRetriever


TEST_STORAGE_PATH = "./data/test_dense_ret_tmp"


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


def test_dense_retriever_pipeline():
    embedder = FastEmbedEmbedder()
    store = QdrantStore(
        collection_name="test_dense_ret_coll",
        dimension=embedder.dimension,
        distance="cosine",
        mode="local",
        storage_path=TEST_STORAGE_PATH
    )
    retriever = DenseRetriever(embedder=embedder, vector_store=store, top_k=2)
    assert isinstance(retriever, BaseRetriever)

    # Index sample items
    ids = ["C-MOTOR", "C-HYDRAULIC"]
    texts = [
        "Main drive spindle motor temperature exceeds 115 C.",
        "Hydraulic return line filter element replacement."
    ]
    vectors = embedder.embed_texts(texts)
    payloads = [
        {"document_id": "DOC-MOTOR", "content": texts[0], "page": 1, "heading_path": ["Motor"]},
        {"document_id": "DOC-HYD", "content": texts[1], "page": 2, "heading_path": ["Hydraulics"]}
    ]
    store.upsert_vectors(ids, vectors, payloads)

    # Query search
    blocks = retriever.search("motor overheating problem", top_k=1)
    assert len(blocks) == 1
    assert isinstance(blocks[0], NormalizedBlock)
    assert blocks[0].document_id == "DOC-MOTOR"
    assert "dense_score" in blocks[0].metadata
    assert blocks[0].metadata["dense_score"] > 0.0

    store.client.close()
