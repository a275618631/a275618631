# -*- coding: utf-8 -*-
"""
Qdrant Vector Store Adapter for Grounded Industrial RAG.
Implements BaseVectorStoreV3 decoupled contract supporting both Local (embedded) and Server (Docker) modes.
Translates canonical chunk_id into deterministic UUIDv5 point IDs.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from core.interfaces import BaseVectorStoreV3
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


class QdrantStore(BaseVectorStoreV3):
    """
    Production-grade vector store adapter interfacing with Qdrant.
    """

    def __init__(
        self,
        collection_name: str = "factory_knowledge_v3_sprint2",
        dimension: int = 384,
        distance: str = "cosine",
        mode: str = "local",
        storage_path: Optional[str] = None,
        server_url: Optional[str] = None,
        url: Optional[str] = None
    ) -> None:
        self.collection_name = collection_name
        self.dimension = dimension
        self.distance = distance.lower()
        self.mode = mode.lower()
        self.storage_path = storage_path or "./data/qdrant_storage"
        self.server_url = url or server_url or "http://localhost:6333"

        if self.mode == "server":
            self.client = QdrantClient(url=self.server_url)
        else:
            os.makedirs(self.storage_path, exist_ok=True)
            self.client = QdrantClient(path=self.storage_path)

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        distance_map = {
            "cosine": qmodels.Distance.COSINE,
            "dot": qmodels.Distance.DOT,
            "euclidean": qmodels.Distance.EUCLID
        }
        dist = distance_map.get(self.distance, qmodels.Distance.COSINE)
        
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.dimension,
                    distance=dist
                )
            )

    def create_collection_if_not_exists(self) -> None:
        """Explicit alias for _ensure_collection."""
        self._ensure_collection()

    @staticmethod

    def chunk_id_to_uuid(chunk_id: str) -> str:
        """
        Generate deterministic UUID v5 from canonical chunk_id.
        Ensures idempotent point upserts and eliminates duplicate storage points.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def upsert_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> None:
        """
        Upsert vectors with metadata payloads.
        """
        if not ids:
            return

        points = []
        for cid, vec, pl in zip(ids, vectors, payloads):
            point_id = self.chunk_id_to_uuid(cid)
            # Ensure raw chunk_id is recorded in payload
            enriched_payload = dict(pl)
            enriched_payload["chunk_id"] = cid
            points.append(qmodels.PointStruct(
                id=point_id,
                vector=vec,
                payload=enriched_payload
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

    def search_vector(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search nearest vectors and return list of payload records with similarity scores.
        Supports structured metadata filtering (asset_scope, approval_status, revision).
        """
        query_filter = self._build_filter(filters) if filters else None

        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )
            results = res.points
        else:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )

        output: List[Dict[str, Any]] = []
        for r in results:
            item = dict(r.payload) if r.payload else {}
            item["score"] = float(r.score)
            item["point_id"] = str(r.id)
            output.append(item)

        return output

    def delete_vectors(self, ids: List[str]) -> None:
        """
        Delete vectors by canonical chunk IDs.
        """
        if not ids:
            return
        point_ids = [self.chunk_id_to_uuid(cid) for cid in ids]
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.PointIdsList(points=point_ids),
            wait=True
        )

    def count_points(self) -> int:
        """
        Return total points currently indexed in the collection.
        """
        res = self.client.count(collection_name=self.collection_name, exact=True)
        return res.count

    def _build_filter(self, filters: Dict[str, Any]) -> qmodels.Filter:
        must_conditions = []
        must_not_conditions = []

        for k, v in filters.items():
            if k == "asset_id" or k == "asset_scope":
                # Matches either string equality or array membership
                if isinstance(v, list):
                    must_conditions.append(qmodels.FieldCondition(
                        key="asset_scope",
                        match=qmodels.MatchAny(any=v)
                    ))
                else:
                    must_conditions.append(qmodels.FieldCondition(
                        key="asset_scope",
                        match=qmodels.MatchValue(value=v)
                    ))
            elif k == "approval_status":
                if isinstance(v, list):
                    must_conditions.append(qmodels.FieldCondition(
                        key="approval_status",
                        match=qmodels.MatchAny(any=v)
                    ))
                else:
                    must_conditions.append(qmodels.FieldCondition(
                        key="approval_status",
                        match=qmodels.MatchValue(value=v)
                    ))
            elif k == "exclude_obsolete" and v is True:
                must_not_conditions.append(qmodels.FieldCondition(
                    key="approval_status",
                    match=qmodels.MatchAny(any=["obsolete", "superseded"])
                ))
            elif k == "document_id":
                must_conditions.append(qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchValue(value=v)
                ))
            elif k == "revision":
                must_conditions.append(qmodels.FieldCondition(
                    key="revision",
                    match=qmodels.MatchValue(value=v)
                ))
            else:
                must_conditions.append(qmodels.FieldCondition(
                    key=k,
                    match=qmodels.MatchValue(value=v)
                ))

        return qmodels.Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None
        )
