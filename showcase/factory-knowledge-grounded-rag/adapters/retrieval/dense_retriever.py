# -*- coding: utf-8 -*-
"""
Dense Semantic Retriever Adapter for Grounded Industrial RAG.
Orchestrates FastEmbed Embedder and Qdrant Vector Store to return canonical NormalizedBlocks.
"""

from typing import List, Dict, Any, Optional
from core.interfaces import BaseRetriever, BaseEmbedder, BaseVectorStoreV3
from core.schema import NormalizedBlock


class DenseRetriever(BaseRetriever):
    """
    Dense Vector Retriever implementing BaseRetriever.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStoreV3,
        top_k: int = 10
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[NormalizedBlock]:
        """Alias for search method."""
        return self.search(query, top_k=top_k, filters=filters)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[NormalizedBlock]:
        k = top_k or self.top_k
        query_vec = self.embedder.embed_query(query)
        payloads = self.vector_store.search_vector(query_vec, top_k=k, filters=filters)

        blocks: List[NormalizedBlock] = []
        for pl in payloads:
            chunk_id = pl.get("chunk_id", "UNKNOWN-CHUNK")
            doc_id = pl.get("document_id", "UNKNOWN-DOC")
            page = pl.get("page", 1)
            b_type = pl.get("block_type", "paragraph")
            heading_path = pl.get("heading_path", [])
            content = pl.get("content", "")
            parser = pl.get("parser", "docling")
            parser_version = pl.get("parser_version", "2.131.0")
            score = pl.get("score", 0.0)

            # Metadata retention
            meta = {k: v for k, v in pl.items() if k not in ["content", "score"]}
            meta["dense_score"] = score

            block = NormalizedBlock(
                block_id=chunk_id,
                document_id=doc_id,
                page=page,
                block_type=b_type,
                heading_path=heading_path,
                content=content,
                parser=parser,
                parser_version=parser_version,
                metadata=meta
            )
            blocks.append(block)

        return blocks
