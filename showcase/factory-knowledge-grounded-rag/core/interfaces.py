"""
Abstract Interfaces for Adapters (Parser, Retriever, VectorStore, Reranker, LLM, LiveState).
Ensures core remains decoupled from concrete libraries.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from core.schema import NormalizedBlock, SourceDocument, CurrentObservation


class BaseParser(ABC):
    """Abstract interface for document parsers (Docling, OCR, Structured, CAD)."""

    @abstractmethod
    def parse(self, file_path: str, doc_metadata: SourceDocument) -> List[NormalizedBlock]:
        """Parse source document into list of NormalizedBlocks."""
        pass


class BaseRetriever(ABC):
    """Abstract interface for exact or keyword searchers."""

    @abstractmethod
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[NormalizedBlock]:
        """Perform search and return matching blocks."""
        pass


class BaseVectorStore(ABC):
    """Abstract interface for dense semantic embedding search (V2 legacy / integrated)."""

    @abstractmethod
    def add_blocks(self, blocks: List[NormalizedBlock]) -> None:
        """Embed and index blocks."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[NormalizedBlock]:
        """Vector semantic search."""
        pass


class BaseVectorStoreV3(ABC):
    """
    V3 Vector Store contract: strictly decoupled from embedding logic.
    Accepts raw vectors and structured payloads (e.g. Qdrant, Milvus).
    """

    @abstractmethod
    def upsert_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> None:
        """Upsert vectors with metadata payloads."""
        pass

    @abstractmethod
    def search_vector(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search nearest vectors and return list of payload records with similarity scores."""
        pass

    @abstractmethod
    def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        pass


class BaseChunker(ABC):
    """Abstract interface for text/document chunking strategies."""

    @abstractmethod
    def chunk(self, blocks: List[NormalizedBlock]) -> List[NormalizedBlock]:
        """Split or group NormalizedBlocks into retrieval-sized chunks with deterministic IDs."""
        pass


class BaseEmbedder(ABC):
    """Abstract interface for dense embedding models (FastEmbed, BGE, etc.)."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings for a batch of documents/chunks."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate dense embedding for a single user query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimensionality."""
        pass


class BaseFusion(ABC):
    """Abstract interface for multi-retriever result fusion (e.g. RRF, weighted sum)."""

    @abstractmethod
    def fuse(
        self,
        ranked_lists: List[List[NormalizedBlock]],
        weights: Optional[List[float]] = None,
        top_k: int = 5
    ) -> List[NormalizedBlock]:
        """Fuse multiple ranked candidate lists into a single deduplicated list."""
        pass


class BaseReranker(ABC):
    """Abstract interface for cross-encoder or rerank scoring."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[NormalizedBlock], threshold: float = 0.3) -> List[NormalizedBlock]:
        """Rerank candidates and filter by threshold."""
        pass

    @abstractmethod
    def compute_scores(self, query: str, texts: List[str]) -> List[float]:
        """Scoring contract: compute pair-wise relevance scores for (query, text)."""
        pass



class BaseLLM(ABC):
    """Abstract interface for local language models (Ollama, vLLM, Mock)."""

    @abstractmethod
    def generate_structured(self, prompt: str, schema_cls: Any) -> Any:
        """Generate structured output adhering to schema_cls."""
        pass


class BaseLiveStateProvider(ABC):
    """Abstract interface for current state observations."""

    @abstractmethod
    def get_latest_observation(self, asset_id: str, tag_id: str) -> Optional[CurrentObservation]:
        """Fetch latest sensor or PLC tag observation."""
        pass
