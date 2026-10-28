# -*- coding: utf-8 -*-
"""
SQLite FTS5 Full-Text Search Retriever Adapter for Grounded Industrial RAG.
Configured with trigram tokenizer for native CJK and alphanumeric substring matching.
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional
from core.interfaces import BaseRetriever
from core.schema import NormalizedBlock


class FTSRetriever(BaseRetriever):
    """
    Lexical full-text search retriever backed by SQLite FTS5 with trigram tokenizer.
    """

    def __init__(self, db_path: str = ":memory:", top_k: int = 10) -> None:
        self.db_path = db_path
        self.top_k = top_k
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_fts_table()

    def _init_fts_table(self) -> None:
        cur = self.conn.cursor()
        # Drop and recreate if needed to ensure trigram tokenizer
        cur.execute("DROP TABLE IF EXISTS chunk_fts;")
        cur.execute("""
            CREATE VIRTUAL TABLE chunk_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                page UNINDEXED,
                block_type UNINDEXED,
                heading_path UNINDEXED,
                content,
                tokenize='trigram'
            );
        """)
        # Metadata auxiliary table for filtering
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunk_metadata (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT,
                page INTEGER,
                block_type TEXT,
                heading_path TEXT,
                content TEXT,
                asset_scope TEXT,
                approval_status TEXT,
                revision TEXT,
                parser TEXT,
                parser_version TEXT
            );
        """)
        self.conn.commit()

    def index_blocks(self, blocks: List[NormalizedBlock], doc_metadata_map: Optional[Dict[str, Any]] = None) -> None:
        """
        Index a batch of NormalizedBlocks into FTS5 virtual table.
        """
        cur = self.conn.cursor()
        doc_map = doc_metadata_map or {}
        
        for b in blocks:
            doc_meta = doc_map.get(b.document_id, {})
            asset_scope_str = ",".join(doc_meta.get("asset_scope", []))
            status = doc_meta.get("approval_status", "approved")
            rev = doc_meta.get("revision", "Rev.A")
            h_path_str = "/".join(b.heading_path)

            cur.execute("""
                INSERT OR REPLACE INTO chunk_metadata 
                (chunk_id, document_id, page, block_type, heading_path, content, asset_scope, approval_status, revision, parser, parser_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b.block_id, b.document_id, b.page, b.block_type, h_path_str, b.content,
                asset_scope_str, status, rev, b.parser, b.parser_version
            ))

            cur.execute("DELETE FROM chunk_fts WHERE chunk_id = ?", (b.block_id,))
            cur.execute("""
                INSERT INTO chunk_fts (chunk_id, document_id, page, block_type, heading_path, content)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (b.block_id, b.document_id, b.page, b.block_type, h_path_str, b.content))

        self.conn.commit()

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
        if not query or not query.strip():
            return []

        clean_query = self._sanitize_query(query)
        if not clean_query:
            return []

        cur = self.conn.cursor()
        sql = """
            SELECT f.chunk_id, f.document_id, f.page, f.block_type, f.heading_path, f.content,
                   bm25(chunk_fts) AS bm25_score,
                   m.asset_scope, m.approval_status, m.revision, m.parser, m.parser_version
            FROM chunk_fts f
            JOIN chunk_metadata m ON f.chunk_id = m.chunk_id
            WHERE chunk_fts MATCH ?
        """
        params = [clean_query]

        if filters:
            if filters.get("exclude_obsolete"):
                sql += " AND m.approval_status NOT IN ('obsolete', 'superseded')"
            if filters.get("approval_status"):
                st = filters["approval_status"]
                if isinstance(st, list):
                    placeholders = ",".join(["?"] * len(st))
                    sql += f" AND m.approval_status IN ({placeholders})"
                    params.extend(st)
                else:
                    sql += " AND m.approval_status = ?"
                    params.append(st)
            if filters.get("document_id"):
                sql += " AND m.document_id = ?"
                params.append(filters["document_id"])
            if filters.get("asset_id"):
                sql += " AND (m.asset_scope LIKE ? OR m.asset_scope = '')"
                params.append(f"%{filters['asset_id']}%")

        sql += " ORDER BY bm25_score ASC LIMIT ?"
        params.append(k)

        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            return self._like_fallback(query, k, filters)

        blocks: List[NormalizedBlock] = []
        for r in rows:
            raw_bm25 = float(r["bm25_score"])
            pos_score = max(0.01, round(1.0 / (1.0 + abs(raw_bm25)), 4))

            h_list = [p for p in r["heading_path"].split("/") if p]
            block = NormalizedBlock(
                block_id=r["chunk_id"],
                document_id=r["document_id"],
                page=int(r["page"]),
                block_type=r["block_type"],
                heading_path=h_list,
                content=r["content"],
                parser=r["parser"] or "docling",
                parser_version=r["parser_version"] or "2.131.0",
                metadata={
                    "fts_score": pos_score,
                    "bm25_raw": raw_bm25,
                    "approval_status": r["approval_status"],
                    "revision": r["revision"],
                    "asset_scope": r["asset_scope"].split(",") if r["asset_scope"] else []
                }
            )
            blocks.append(block)

        return blocks

    def _sanitize_query(self, query: str) -> str:
        # Strip special punctuation and quotes
        q_clean = re.sub(r'[*":()^~+\-]', ' ', query)
        tokens = [t.strip() for t in q_clean.split() if len(t.strip()) > 0]
        if not tokens:
            return ""
        # Quote each token for trigram phrase matching
        quoted = [f'"{t}"' for t in tokens if len(t) >= 2]
        return " OR ".join(quoted) if quoted else f'"{tokens[0]}"'

    def _like_fallback(self, query: str, limit: int, filters: Optional[Dict[str, Any]]) -> List[NormalizedBlock]:
        cur = self.conn.cursor()
        sql = "SELECT * FROM chunk_metadata WHERE content LIKE ? LIMIT ?"
        cur.execute(sql, (f"%{query}%", limit))
        rows = cur.fetchall()
        blocks = []
        for r in rows:
            h_list = [p for p in r["heading_path"].split("/") if p]
            blocks.append(NormalizedBlock(
                block_id=r["chunk_id"],
                document_id=r["document_id"],
                page=int(r["page"]),
                block_type=r["block_type"],
                heading_path=h_list,
                content=r["content"],
                parser=r["parser"] or "docling",
                parser_version=r["parser_version"] or "2.131.0",
                metadata={"fts_score": 0.5, "approval_status": r["approval_status"]}
            ))
        return blocks
