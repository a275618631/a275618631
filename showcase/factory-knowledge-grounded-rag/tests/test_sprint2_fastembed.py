# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: FastEmbed Multilingual Embedder.
Validates BaseEmbedder contract, dimension, and query/passage embedding outputs.
"""

import pytest
from core.interfaces import BaseEmbedder
from adapters.embedding.fastembed_embedder import FastEmbedEmbedder


def test_fastembed_inheritance_and_dimension():
    embedder = FastEmbedEmbedder()
    assert isinstance(embedder, BaseEmbedder)
    assert embedder.dimension == 384
    assert embedder.model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def test_fastembed_embed_texts_and_query():
    embedder = FastEmbedEmbedder()
    texts = [
        "機台主軸軸承異常升溫警報 ALM-3025",
        "Linear guide rail lubrication frequency table"
    ]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

    q_vec = embedder.embed_query("馬達過熱檢修步驟")
    assert len(q_vec) == 384
    assert all(isinstance(v, float) for v in q_vec)


def test_fastembed_empty_query():
    embedder = FastEmbedEmbedder()
    empty_vec = embedder.embed_query("")
    assert len(empty_vec) == 384
    assert all(v == 0.0 for v in empty_vec)
