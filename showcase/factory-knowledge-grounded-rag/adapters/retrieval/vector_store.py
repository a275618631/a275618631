"""
Dense Vector Store Adapter for Semantic Document Retrieval.
Offline-capable, local-first vector store with Cosine Similarity.
Compatible with standard BaseVectorStore interface (can bridge to Qdrant Local).
"""

import math
import re
from typing import List, Dict, Any, Optional, Tuple
from core.interfaces import BaseVectorStore
from core.schema import NormalizedBlock


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into character bi-grams and words for dense vectorization."""
    cleaned = re.sub(r"[^\w\s\-\.]", " ", text.lower())
    words = cleaned.split()
    tokens = list(words)
    # Add character n-grams for CJK text
    for w in words:
        if len(w) > 1:
            for i in range(len(w) - 1):
                tokens.append(w[i:i+2])
    return tokens


class DenseVectorStore(BaseVectorStore):
    """
    Local in-memory dense vector store using Term-Frequency Inverse-Document-Frequency
    normalized dense vectors with cosine similarity matching.
    """

    def __init__(self) -> None:
        self._blocks: Dict[str, NormalizedBlock] = {}
        self._doc_freqs: Dict[str, int] = {}
        self._vectors: Dict[str, Dict[str, float]] = {}
        self._total_docs: int = 0

    def add_blocks(self, blocks: List[NormalizedBlock]) -> None:
        for b in blocks:
            self._blocks[b.block_id] = b
            tokens = set(tokenize_text(b.content + " " + " ".join(b.heading_path)))
            for t in tokens:
                self._doc_freqs[t] = self._doc_freqs.get(t, 0) + 1
        self._total_docs = len(self._blocks)

        # Compute TF-IDF dense normalized vectors
        for b_id, b in self._blocks.items():
            tokens = tokenize_text(b.content + " " + " ".join(b.heading_path))
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0

            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for t, count in tf.items():
                idf = math.log((self._total_docs + 1.0) / (self._doc_freqs.get(t, 1) + 1.0)) + 1.0
                weight = count * idf
                vec[t] = weight
                norm_sq += weight * weight

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self._vectors[b_id] = {t: w / norm for t, w in vec.items()}

    def _cosine_similarity(self, q_vec: Dict[str, float], doc_vec: Dict[str, float]) -> float:
        score = 0.0
        for t, qw in q_vec.items():
            if t in doc_vec:
                score += qw * doc_vec[t]
        return score

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[NormalizedBlock]:
        tokens = tokenize_text(query)
        if not tokens or self._total_docs == 0:
            return []

        # Vectorize query
        q_tf: Dict[str, float] = {}
        for t in tokens:
            q_tf[t] = q_tf.get(t, 0.0) + 1.0

        q_vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, count in q_tf.items():
            idf = math.log((self._total_docs + 1.0) / (self._doc_freqs.get(t, 1) + 1.0)) + 1.0
            w = count * idf
            q_vec[t] = w
            norm_sq += w * w

        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        norm_q_vec = {t: w / norm for t, w in q_vec.items()}

        scores: List[Tuple[float, NormalizedBlock]] = []
        for b_id, doc_vec in self._vectors.items():
            block = self._blocks[b_id]
            if filters:
                if "document_id" in filters and block.document_id != filters["document_id"]:
                    continue
                if "block_type" in filters and block.block_type != filters["block_type"]:
                    continue

            sim = self._cosine_similarity(norm_q_vec, doc_vec)
            if sim > 0:
                scores.append((sim, block))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scores[:top_k]]
