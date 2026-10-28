# -*- coding: utf-8 -*-
"""
Fixed Window Chunker for Grounded Industrial RAG.
Acts as a naive baseline chunker splitting text by fixed character/token window and overlap.
Inherits from BaseChunker and assigns deterministic SHA-256 chunk IDs.
"""

from typing import List, Dict, Any, Optional
from core.interfaces import BaseChunker
from core.schema import NormalizedBlock
from adapters.chunking.identity import generate_deterministic_chunk_id


class FixedWindowChunker(BaseChunker):
    """
    Fixed Window Chunker splitting text at target_size with specified overlap.
    All parameters are config-driven.
    """

    def __init__(
        self,
        target_size: int = 512,
        overlap: int = 64,
        max_size: int = 768,
        min_size: int = 50,
        chunker_version: str = "1.0.0"
    ) -> None:
        self.target_size = target_size
        self.overlap = overlap
        self.max_size = max_size
        self.min_size = min_size
        self.chunker_version = chunker_version

    def chunk(self, blocks: List[NormalizedBlock]) -> List[NormalizedBlock]:
        """
        Splits blocks into fixed-size chunks while preserving provenance metadata.
        """
        chunks: List[NormalizedBlock] = []

        for block in blocks:
            text = block.content.strip()
            if not text:
                continue

            # If text fits comfortably in target window, keep as single chunk
            if len(text) <= self.target_size:
                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=text,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=0
                )
                chunk_block = NormalizedBlock(
                    block_id=c_id,
                    document_id=block.document_id,
                    page=block.page,
                    block_type=block.block_type,
                    heading_path=list(block.heading_path),
                    content=text,
                    table_data=block.table_data,
                    bbox=block.bbox,
                    parser=block.parser,
                    parser_version=block.parser_version,
                    parse_confidence=block.parse_confidence,
                    metadata={
                        **block.metadata,
                        "chunk_strategy": "fixed_window",
                        "chunk_index": 0,
                        "original_block_id": block.block_id
                    }
                )
                chunks.append(chunk_block)
                continue

            # Sliding window split
            start = 0
            step = max(1, self.target_size - self.overlap)
            sub_idx = 0

            while start < len(text):
                end = min(len(text), start + self.target_size)
                segment = text[start:end].strip()

                # Don't create trailing undersized chunk if remaining is tiny
                if len(segment) < self.min_size and sub_idx > 0:
                    break

                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=segment,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=sub_idx
                )

                chunk_block = NormalizedBlock(
                    block_id=c_id,
                    document_id=block.document_id,
                    page=block.page,
                    block_type=block.block_type,
                    heading_path=list(block.heading_path),
                    content=segment,
                    table_data=block.table_data if sub_idx == 0 else None,
                    bbox=block.bbox,
                    parser=block.parser,
                    parser_version=block.parser_version,
                    parse_confidence=block.parse_confidence,
                    metadata={
                        **block.metadata,
                        "chunk_strategy": "fixed_window",
                        "chunk_index": sub_idx,
                        "original_block_id": block.block_id,
                        "char_start": start,
                        "char_end": end
                    }
                )
                chunks.append(chunk_block)
                sub_idx += 1

                if end >= len(text):
                    break
                start += step

        return chunks
