"""
SQLite FTS5 Full-Text Search Adapter for Exact IDs, Alarms, Tags, and Keywords.
Zero-service, local-first search engine.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from core.interfaces import BaseRetriever
from core.schema import NormalizedBlock


class SQLiteFTSRetriever(BaseRetriever):
    """
    FTS5 Retriever optimized for exact industrial codes (ALM-3025, Y52-ENC-FB, etc.)
    and keyword retrieval.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        # Create FTS5 virtual table
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS blocks_fts USING fts5(
                block_id UNINDEXED,
                document_id,
                page UNINDEXED,
                block_type,
                heading_path,
                content,
                table_json UNINDEXED,
                metadata_json UNINDEXED,
                tokenize = 'unicode61'
            )
        """)
        self.conn.commit()

    def index_blocks(self, blocks: List[NormalizedBlock]) -> None:
        """Insert or replace normalized blocks into FTS5 index."""
        cur = self.conn.cursor()
        for b in blocks:
            # Delete if exists
            cur.execute("DELETE FROM blocks_fts WHERE block_id = ?", (b.block_id,))
            table_str = b.table_data.model_dump_json() if b.table_data else ""
            meta_str = json.dumps(b.metadata)
            headings_str = " > ".join(b.heading_path)
            cur.execute("""
                INSERT INTO blocks_fts(
                    block_id, document_id, page, block_type, heading_path,
                    content, table_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b.block_id, b.document_id, b.page, b.block_type,
                headings_str, b.content, table_str, meta_str
            ))
        self.conn.commit()

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[NormalizedBlock]:
        """
        Execute FTS5 match query with ranking.
        Supports exact alarm/tag query by quoting or tokenizing.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        cur = self.conn.cursor()

        import re
        clean_q = query.strip()
        if not clean_q:
            return []

        cur = self.conn.cursor()

        # Extract alphanumeric codes and tokens (e.g. ALM-3025, Y52-ENC-FB, 45, Nm)
        code_tokens = re.findall(r"[A-Za-z0-9\-]+", clean_q)

        # Extract Chinese words and generate 2-grams / 3-grams
        stopwords = {"是什麼", "是多少", "應使用", "何種", "規格", "為誰", "為何", "在", "的", "之", "與", "及", "有", "請", "問"}
        cjk_chunks = re.findall(r"[\u4e00-\u9fa5]+", clean_q)
        cjk_tokens = []
        for chunk in cjk_chunks:
            if len(chunk) <= 4 and chunk not in stopwords:
                cjk_tokens.append(chunk)
            else:
                for n in [2, 3]:
                    for i in range(len(chunk) - n + 1):
                        sub = chunk[i:i+n]
                        if sub not in stopwords:
                            cjk_tokens.append(sub)

        search_tokens = list(dict.fromkeys(code_tokens + cjk_tokens))
        if not search_tokens:
            search_tokens = clean_q.split()

        # Build FTS match expression
        fts_query = " OR ".join([f'"{w}"' for w in search_tokens if w])

        sql = f"""
            SELECT block_id, document_id, page, block_type, heading_path,
                   content, table_json, metadata_json, rank
            FROM blocks_fts
            WHERE blocks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """

        try:
            cur.execute(sql, (fts_query, top_k * 2))
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            # Fallback to simple LIKE if FTS expression has syntax error
            sql_fallback = """
                SELECT block_id, document_id, page, block_type, heading_path,
                       content, table_json, metadata_json, 0 as rank
                FROM blocks_fts
                WHERE content LIKE ?
                LIMIT ?
            """
            cur.execute(sql_fallback, (f"%{clean_q}%", top_k))
            rows = cur.fetchall()

        results: List[NormalizedBlock] = []
        for r in rows:
            b_id, doc_id, page, b_type, h_path, content, t_json, m_json, _ = r
            if filters:
                if "document_id" in filters and doc_id != filters["document_id"]:
                    continue
                if "block_type" in filters and b_type != filters["block_type"]:
                    continue

            table_data = None
            if t_json:
                try:
                    table_dict = json.loads(t_json)
                    from core.schema import TableData
                    table_data = TableData.model_validate(table_dict)
                except Exception:
                    pass

            meta_dict = {}
            if m_json:
                try:
                    meta_dict = json.loads(m_json)
                except Exception:
                    pass

            results.append(NormalizedBlock(
                block_id=b_id,
                document_id=doc_id,
                page=int(page),
                block_type=b_type,
                heading_path=h_path.split(" > ") if h_path else [],
                content=content,
                table_data=table_data,
                parser="sqlite_fts",
                parser_version="1.0.0",
                parse_confidence=1.0,
                metadata=meta_dict
            ))
            if len(results) >= top_k:
                break

        return results

    def close(self) -> None:
        self.conn.close()
