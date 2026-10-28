# -*- coding: utf-8 -*-
"""
Deterministic Chunk Identity Generator for Factory Knowledge Grounded RAG.
Produces strictly repeatable, cross-process, cross-platform SHA-256 chunk identifiers.
Prohibits Python's built-in hash() to prevent salt-induced variance across runs.
"""

import hashlib
from typing import List, Optional


def generate_deterministic_chunk_id(
    document_id: str,
    source_checksum: str,
    page: int,
    heading_path: List[str],
    content: str,
    chunker_version: str = "1.0.0",
    chunk_index_in_block: int = 0
) -> str:
    """
    Generate a 16-character deterministic hex chunk ID based on canonical attributes.
    
    Formula:
        SHA-256(
            document_id
            + source_checksum
            + page
            + heading_path
            + normalized_content
            + chunker_version
            + chunk_index
        )[:16]
    """
    clean_content = " ".join(content.split()).strip()
    structural_path = "/".join(heading_path).strip()
    
    components = [
        str(document_id).strip(),
        str(source_checksum).strip(),
        f"P{page}",
        structural_path,
        clean_content,
        str(chunker_version).strip(),
        f"IDX{chunk_index_in_block}"
    ]
    raw_payload = "|".join(components).encode("utf-8")
    full_sha = hashlib.sha256(raw_payload).hexdigest()
    
    # Prefix with doc_id and page for human-readable debugging
    return f"{document_id}-P{page}-{full_sha[:12]}"
