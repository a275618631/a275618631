# -*- coding: utf-8 -*-
import pytest
import os
import yaml
from typing import List, Dict, Any, Optional

from core.interfaces import (
    BaseParser,
    BaseRetriever,
    BaseVectorStore,
    BaseVectorStoreV3,
    BaseChunker,
    BaseEmbedder,
    BaseFusion,
    BaseReranker,
    BaseLLM
)
from core.schema import NormalizedBlock
from adapters.rerank.bge_reranker import BGEReranker


def test_abstract_interfaces_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseChunker()

    with pytest.raises(TypeError):
        BaseEmbedder()

    with pytest.raises(TypeError):
        BaseVectorStoreV3()

    with pytest.raises(TypeError):
        BaseFusion()

    with pytest.raises(TypeError):
        BaseReranker()


def make_dummy_block(block_id: str, content: str = 'Dummy content') -> NormalizedBlock:
    return NormalizedBlock(
        block_id=block_id,
        document_id='DOC-001',
        page=1,
        block_type='paragraph',
        heading_path=['Overview'],
        content=content,
        parser='test_parser',
        parser_version='1.0.0'
    )


def test_base_chunker_concrete_contract():
    class DummyChunker(BaseChunker):
        def chunk(self, blocks: List[NormalizedBlock]) -> List[NormalizedBlock]:
            return blocks

    chunker = DummyChunker()
    assert isinstance(chunker, BaseChunker)
    blocks = [make_dummy_block('b1', 'Test chunk content')]
    assert len(chunker.chunk(blocks)) == 1



def test_base_embedder_concrete_contract():
    class DummyEmbedder(BaseEmbedder):
        @property
        def dimension(self) -> int:
            return 128

        def embed_texts(self, texts: List[str]) -> List[List[float]]:
            return [[0.1] * self.dimension for _ in texts]

        def embed_query(self, query: str) -> List[float]:
            return [0.1] * self.dimension

    embedder = DummyEmbedder()
    assert isinstance(embedder, BaseEmbedder)
    assert embedder.dimension == 128
    vecs = embedder.embed_texts(['sample text'])
    assert len(vecs) == 1
    assert len(vecs[0]) == 128
    q_vec = embedder.embed_query('query text')
    assert len(q_vec) == 128


def test_base_vector_store_v3_concrete_contract():
    class DummyVectorStoreV3(BaseVectorStoreV3):
        def __init__(self):
            self.store = {}

        def upsert_vectors(self, ids: List[str], vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> None:
            for i, v, p in zip(ids, vectors, payloads):
                self.store[i] = {'vector': v, 'payload': p}

        def search_vector(self, query_vector: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            results = []
            for i, data in self.store.items():
                results.append({'id': i, 'score': 0.99, 'payload': data['payload']})
            return results[:top_k]

        def delete_vectors(self, ids: List[str]) -> None:
            for i in ids:
                self.store.pop(i, None)

    vs = DummyVectorStoreV3()
    assert isinstance(vs, BaseVectorStoreV3)
    vs.upsert_vectors(['c1'], [[0.1, 0.2]], [{'doc': 'test'}])
    hits = vs.search_vector([0.1, 0.2], top_k=1)
    assert len(hits) == 1
    assert hits[0]['id'] == 'c1'
    vs.delete_vectors(['c1'])
    assert len(vs.search_vector([0.1, 0.2])) == 0


def test_base_fusion_concrete_contract():
    class DummyRRF(BaseFusion):
        def fuse(self, ranked_lists: List[List[NormalizedBlock]], weights: Optional[List[float]] = None, top_k: int = 5) -> List[NormalizedBlock]:
            merged = []
            seen = set()
            for r_list in ranked_lists:
                for b in r_list:
                    if b.block_id not in seen:
                        seen.add(b.block_id)
                        merged.append(b)
            return merged[:top_k]

    fusion = DummyRRF()
    assert isinstance(fusion, BaseFusion)
    b1 = make_dummy_block('b1', 'Content 1')
    b2 = make_dummy_block('b2', 'Content 2')
    res = fusion.fuse([[b1], [b1, b2]], top_k=2)
    assert len(res) == 2
    assert res[0].block_id == 'b1'
    assert res[1].block_id == 'b2'


def test_bge_reranker_scoring_contract():
    reranker = BGEReranker(calibrated_threshold=0.30)
    assert isinstance(reranker, BaseReranker)

    query = 'ALM-3025 伺服驅動異常'
    texts = [
        '警報代號 ALM-3025 伺服驅動異常 處置方式：檢查光纖',
        '無關文字 這是產線一般清潔規定'
    ]
    scores = reranker.compute_scores(query, texts)
    assert len(scores) == 2
    assert isinstance(scores[0], float)
    assert isinstance(scores[1], float)
    assert scores[0] > scores[1]
    assert scores[0] >= 0.30


def test_config_profiles_validity():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    with open(os.path.join(base_path, 'base.yaml'), 'r', encoding='utf-8') as f:
        base_cfg = yaml.safe_load(f)
        assert base_cfg['version'] == '3.0.0'
        assert 'core' in base_cfg

    profiles = ['unit_test.yaml', 'dev_local.yaml', 'portfolio.yaml', 'benchmark.yaml']
    for p in profiles:
        p_path = os.path.join(base_path, 'profiles', p)
        assert os.path.exists(p_path)
        with open(p_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            assert 'profile' in cfg
