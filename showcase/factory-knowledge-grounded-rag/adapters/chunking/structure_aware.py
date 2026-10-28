# -*- coding: utf-8 -*-
"""
Structure-Aware Chunker for Grounded Industrial RAG.
Preserves engineering boundaries:
- Never splits individual table rows arbitrarily; injects table headers into split chunks.
- Retains section heading hierarchy and contextual path in every chunk.
- Preserves procedural steps (SOP 1., 2., 3.) and safety warnings as atomic units.
- Respects page and document provenance boundaries.
- Generates repeatable SHA-256 deterministic chunk IDs.
"""

import re
from typing import List, Dict, Any, Optional
from core.interfaces import BaseChunker
from core.schema import NormalizedBlock, TableData, TableCell
from adapters.chunking.identity import generate_deterministic_chunk_id


class StructureAwareChunker(BaseChunker):
    """
    Structural and semantic boundary chunker for industrial factory documentation.
    """

    def __init__(
        self,
        max_chunk_size: int = 768,
        min_chunk_size: int = 60,
        preserve_tables: bool = True,
        preserve_headings: bool = True,
        chunker_version: str = "1.0.0"
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.preserve_tables = preserve_tables
        self.preserve_headings = preserve_headings
        self.chunker_version = chunker_version

    def chunk(self, blocks: List[NormalizedBlock]) -> List[NormalizedBlock]:
        """
        Group or split NormalizedBlocks based on structural hierarchy and table integrity.
        """
        chunks: List[NormalizedBlock] = []

        for block in blocks:
            b_type = block.block_type.lower()
            text = block.content.strip()

            if not text:
                continue

            # 1. Table Handling: Preserve header and table row boundaries
            if b_type == "table":
                table_chunks = self._chunk_table_block(block)
                chunks.extend(table_chunks)
                continue

            # 2. Safety Warnings and Critical Procedure Steps: Keep intact if possible
            if b_type in ["warning", "caution", "safety"]:
                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=text,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=0
                )
                chunks.append(self._create_chunk(block, text, c_id, 0))
                continue

            # 3. Headings: Heading blocks attach context or stand as structural anchors
            if b_type == "heading":
                # Keep heading intact for navigation
                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=text,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=0
                )
                chunks.append(self._create_chunk(block, text, c_id, 0))
                continue

            # 4. Standard Paragraphs or Step Sequences
            if len(text) <= self.max_chunk_size:
                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=text,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=0
                )
                chunks.append(self._create_chunk(block, text, c_id, 0))
            else:
                # Break down at natural sentence / newline / itemized boundary
                split_segments = self._split_by_natural_boundaries(text, self.max_chunk_size)
                for s_idx, seg in enumerate(split_segments):
                    c_id = generate_deterministic_chunk_id(
                        document_id=block.document_id,
                        source_checksum=block.metadata.get("source_checksum", "000000"),
                        page=block.page,
                        heading_path=block.heading_path,
                        content=seg,
                        chunker_version=self.chunker_version,
                        chunk_index_in_block=s_idx
                    )
                    chunks.append(self._create_chunk(block, seg, c_id, s_idx))

        return chunks

    def _chunk_table_block(self, block: NormalizedBlock) -> List[NormalizedBlock]:
        """
        Splits oversized tables by whole rows while re-injecting column headers into every chunk.
        """
        text = block.content.strip()
        # If table fits within max_chunk_size or has no structured table_data, keep as single chunk
        if len(text) <= self.max_chunk_size or not block.table_data:
            c_id = generate_deterministic_chunk_id(
                document_id=block.document_id,
                source_checksum=block.metadata.get("source_checksum", "000000"),
                page=block.page,
                heading_path=block.heading_path,
                content=text,
                chunker_version=self.chunker_version,
                chunk_index_in_block=0
            )
            return [self._create_chunk(block, text, c_id, 0, table_data=block.table_data)]

        # Chunk table row-by-row
        t_data = block.table_data
        headers = t_data.headers
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        header_block = header_line + "\n" + sep_line

        table_chunks: List[NormalizedBlock] = []
        current_rows: List[List[str]] = []
        current_cells: List[TableCell] = []
        current_len = len(header_block)
        chunk_idx = 0

        for r_idx, row in enumerate(t_data.rows):
            row_line = "| " + " | ".join(row) + " |"
            row_len = len(row_line) + 1  # newline

            if current_rows and (current_len + row_len > self.max_chunk_size):
                # Flush current table chunk
                chunk_content = header_block + "\n" + "\n".join(["| " + " | ".join(r) + " |" for r in current_rows])
                sub_t_data = TableData(headers=headers, rows=current_rows, cells=current_cells)
                c_id = generate_deterministic_chunk_id(
                    document_id=block.document_id,
                    source_checksum=block.metadata.get("source_checksum", "000000"),
                    page=block.page,
                    heading_path=block.heading_path,
                    content=chunk_content,
                    chunker_version=self.chunker_version,
                    chunk_index_in_block=chunk_idx
                )
                table_chunks.append(self._create_chunk(
                    block, chunk_content, c_id, chunk_idx,
                    table_data=sub_t_data,
                    extra_meta={"table_split": True, "rows_in_chunk": len(current_rows)}
                ))
                chunk_idx += 1
                current_rows = []
                current_cells = []
                current_len = len(header_block)

            current_rows.append(row)
            # Find matching cells
            row_cells = [c for c in t_data.cells if c.row_idx == r_idx]
            current_cells.extend(row_cells)
            current_len += row_len

        if current_rows:
            chunk_content = header_block + "\n" + "\n".join(["| " + " | ".join(r) + " |" for r in current_rows])
            sub_t_data = TableData(headers=headers, rows=current_rows, cells=current_cells)
            c_id = generate_deterministic_chunk_id(
                document_id=block.document_id,
                source_checksum=block.metadata.get("source_checksum", "000000"),
                page=block.page,
                heading_path=block.heading_path,
                content=chunk_content,
                chunker_version=self.chunker_version,
                chunk_index_in_block=chunk_idx
            )
            table_chunks.append(self._create_chunk(
                block, chunk_content, c_id, chunk_idx,
                table_data=sub_t_data,
                extra_meta={"table_split": True if chunk_idx > 0 else False, "rows_in_chunk": len(current_rows)}
            ))

        return table_chunks

    def _split_by_natural_boundaries(self, text: str, max_size: int) -> List[str]:
        """
        Splits text by newline or sentence punctuation without breaking mid-sentence.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        segments: List[str] = []
        cur_buf: List[str] = []
        cur_len = 0

        for line in lines:
            if cur_buf and (cur_len + len(line) + 1 > max_size):
                segments.append("\n".join(cur_buf))
                cur_buf = [line]
                cur_len = len(line)
            else:
                cur_buf.append(line)
                cur_len += len(line) + 1

        if cur_buf:
            segments.append("\n".join(cur_buf))

        return segments

    def _create_chunk(
        self,
        block: NormalizedBlock,
        content: str,
        chunk_id: str,
        chunk_index: int,
        table_data: Optional[TableData] = None,
        extra_meta: Optional[Dict[str, Any]] = None
    ) -> NormalizedBlock:
        meta = {
            **block.metadata,
            "chunk_strategy": "structure_aware",
            "chunk_index": chunk_index,
            "original_block_id": block.block_id,
            "heading_context": " > ".join(block.heading_path) if block.heading_path else ""
        }
        if extra_meta:
            meta.update(extra_meta)

        return NormalizedBlock(
            block_id=chunk_id,
            document_id=block.document_id,
            page=block.page,
            block_type=block.block_type,
            heading_path=list(block.heading_path),
            content=content,
            table_data=table_data,
            bbox=block.bbox,
            parser=block.parser,
            parser_version=block.parser_version,
            parse_confidence=block.parse_confidence,
            metadata=meta
        )
