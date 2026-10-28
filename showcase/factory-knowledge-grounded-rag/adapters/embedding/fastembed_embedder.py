# -*- coding: utf-8 -*-
"""
FastEmbed Multilingual Embedder Adapter for Grounded Industrial RAG.
Implements BaseEmbedder contract using Qdrant FastEmbed (ONNX runtime).
"""

import time
from typing import List, Dict, Any, Optional
from core.interfaces import BaseEmbedder


class FastEmbedEmbedder(BaseEmbedder):
    """
    Production-grade local dense embedding generator using FastEmbed.
    Default model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (dim 384).
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        batch_size: int = 32,
        threads: Optional[int] = None
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.threads = threads
        self.package_version = "0.8.1"
        self._dimension = 384
        self._model = None
        self.model_load_time_seconds: float = 0.0
        self.last_inference_latency_seconds: float = 0.0

    def _get_model(self):
        if self._model is None:
            t0 = time.time()
            from fastembed import TextEmbedding
            self._model = TextEmbedding(
                model_name=self.model_name,
                threads=self.threads
            )
            self.model_load_time_seconds = round(time.time() - t0, 4)
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate dense embeddings for a batch of documents or chunks.
        """
        if not texts:
            return []

        model = self._get_model()
        t0 = time.time()
        try:
            generator = model.embed(texts, batch_size=self.batch_size)
            vectors = [vec.tolist() if hasattr(vec, "tolist") else list(vec) for vec in generator]
            self.last_inference_latency_seconds = round(time.time() - t0, 4)
            return vectors
        except Exception as e:
            raise RuntimeError(f"FastEmbedEmbedder failed on embedding {len(texts)} texts: {str(e)}") from e

    def embed_query(self, query: str) -> List[float]:
        """
        Generate dense embedding for a single user query.
        """
        if not query or not query.strip():
            return [0.0] * self.dimension

        model = self._get_model()
        t0 = time.time()
        try:
            generator = model.query_embed(query)
            vec = next(iter(generator))
            self.last_inference_latency_seconds = round(time.time() - t0, 4)
            return vec.tolist() if hasattr(vec, "tolist") else list(vec)
        except Exception as e:
            raise RuntimeError(f"FastEmbedEmbedder failed on query '{query}': {str(e)}") from e

    @property
    def dimension(self) -> int:
        """
        Embedding vector dimensionality.
        """
        return self._dimension

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Return diagnostic metadata for inspection and logging.
        """
        return {
            "provider": "fastembed",
            "model_name": self.model_name,
            "package_version": self.package_version,
            "dimension": self.dimension,
            "batch_size": self.batch_size,
            "model_load_time_seconds": self.model_load_time_seconds,
            "last_inference_latency_seconds": self.last_inference_latency_seconds
        }
