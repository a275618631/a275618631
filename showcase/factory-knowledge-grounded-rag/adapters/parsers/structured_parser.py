"""
Structured Document Parser for SOPs, Manuals, and Industrial Specifications.
Parses headings, procedure steps, warnings, and markdown/csv tables into NormalizedBlocks.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from core.interfaces import BaseParser
from core.schema import NormalizedBlock, SourceDocument, TableData, TableCell


class StructuredParser(BaseParser):
    """
    Local structured parser that preserves heading paths, page/block hierarchy,
    and row/cell level structured table representation.
    """

    def __init__(self, parser_version: str = "1.0.0") -> None:
        self.parser_name = "structured_parser"
        self.parser_version = parser_version

    def parse(self, file_path: str, doc_metadata: SourceDocument) -> List[NormalizedBlock]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        return self.parse_text(lines, doc_metadata)

    def parse_text(self, lines: List[str], doc_metadata: SourceDocument) -> List[NormalizedBlock]:
        blocks: List[NormalizedBlock] = []
        heading_stack: List[str] = []
        current_page = 1
        block_idx = 1

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # Check page break markers (e.g. <!-- PAGE 2 --> or form feed)
            page_match = re.search(r"<!--\s*PAGE\s*(\d+)\s*-->", stripped, re.IGNORECASE)
            if page_match:
                current_page = int(page_match.group(1))
                i += 1
                continue

            # Check Markdown Headings
            if stripped.startswith("#"):
                hashes = len(stripped) - len(stripped.lstrip("#"))
                title = stripped.lstrip("#").strip()
                # Adjust stack
                heading_stack = heading_stack[: hashes - 1]
                heading_stack.append(title)

                block = NormalizedBlock(
                    block_id=f"{doc_metadata.document_id}-P{current_page:03d}-B{block_idx:03d}",
                    document_id=doc_metadata.document_id,
                    page=current_page,
                    block_type="heading",
                    heading_path=list(heading_stack),
                    content=title,
                    parser=self.parser_name,
                    parser_version=self.parser_version,
                    parse_confidence=1.0
                )
                blocks.append(block)
                block_idx += 1
                i += 1
                continue

            # Check Markdown Table (line starts with '|')
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                table_data, table_text = self._parse_markdown_table(table_lines)
                block = NormalizedBlock(
                    block_id=f"{doc_metadata.document_id}-P{current_page:03d}-B{block_idx:03d}",
                    document_id=doc_metadata.document_id,
                    page=current_page,
                    block_type="table",
                    heading_path=list(heading_stack),
                    content=table_text,
                    table_data=table_data,
                    parser=self.parser_name,
                    parser_version=self.parser_version,
                    parse_confidence=0.98
                )
                blocks.append(block)
                block_idx += 1
                continue

            # Check Warning / Caution
            block_type = "paragraph"
            if stripped.upper().startswith(("WARNING", "CAUTION", "警告", "注意", "危險", "DANGER")):
                block_type = "warning"
            elif re.match(r"^(\d+\.|\([0-9a-zA-Z]\)|-|\*)\s+", stripped):
                block_type = "procedure_step"

            # Accumulate paragraph text
            para_lines = [stripped]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line or next_line.startswith("#") or (next_line.startswith("|") and next_line.endswith("|")) or "<!-- PAGE" in next_line:
                    break
                para_lines.append(next_line)
                i += 1

            full_content = " ".join(para_lines)
            block = NormalizedBlock(
                block_id=f"{doc_metadata.document_id}-P{current_page:03d}-B{block_idx:03d}",
                document_id=doc_metadata.document_id,
                page=current_page,
                block_type=block_type,
                heading_path=list(heading_stack),
                content=full_content,
                parser=self.parser_name,
                parser_version=self.parser_version,
                parse_confidence=1.0
            )
            blocks.append(block)
            block_idx += 1

        return blocks

    def _parse_markdown_table(self, table_lines: List[str]) -> Tuple[TableData, str]:
        if not table_lines:
            return TableData(headers=[], rows=[], cells=[]), ""

        def split_row(line: str) -> List[str]:
            cells = line.strip().strip("|").split("|")
            return [c.strip() for c in cells]

        raw_headers = split_row(table_lines[0])
        headers = raw_headers

        rows: List[List[str]] = []
        cells: List[TableCell] = []

        start_row = 1
        if len(table_lines) > 1 and set(table_lines[1].replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            # Second line is separator |---|---|
            start_row = 2

        row_idx = 0
        for line in table_lines[start_row:]:
            row_vals = split_row(line)
            rows.append(row_vals)
            for col_idx, val in enumerate(row_vals):
                header = headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx}"
                cells.append(TableCell(
                    row_idx=row_idx,
                    col_idx=col_idx,
                    col_header=header,
                    value=val,
                    raw_value=val
                ))
            row_idx += 1

        table_text = "\n".join(table_lines)
        return TableData(headers=headers, rows=rows, cells=cells), table_text
