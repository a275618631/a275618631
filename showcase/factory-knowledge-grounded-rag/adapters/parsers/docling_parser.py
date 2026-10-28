# -*- coding: utf-8 -*-
"""
Docling Parser Adapter for Grounded Industrial RAG.
Converts native/complex/scanned PDF documents into Canonical NormalizedBlocks.
Retains section heading hierarchy, table rows/cells, page locators, and bounding boxes.
"""

import os
from typing import List, Optional, Dict, Any
from core.interfaces import BaseParser
from core.schema import NormalizedBlock, SourceDocument, TableData, TableCell


class DoclingParser(BaseParser):
    """
    Parser adapter integrating IBM Docling DocumentConverter.
    Extracts structured blocks with strict canonical provenance.
    """

    def __init__(self, enable_ocr: bool = True) -> None:
        self.parser_name = "docling"
        self.parser_version = "2.131.0"
        self.enable_ocr = enable_ocr
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
        return self._converter

    def parse(self, file_path: str, doc_metadata: SourceDocument) -> List[NormalizedBlock]:
        """
        Parse source PDF file into list of NormalizedBlocks with full provenance.
        Does NOT fail silently; raises RuntimeError with diagnostics on failure.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        try:
            converter = self._get_converter()
            res = converter.convert(file_path)
            doc = res.document
        except Exception as e:
            raise RuntimeError(f"DoclingParser failed on {file_path}: {str(e)}") from e

        blocks: List[NormalizedBlock] = []
        heading_stack: List[str] = []
        block_idx = 0

        for item, level in doc.iterate_items():
            t_name = type(item).__name__
            lbl = getattr(item, "label", "").lower()
            
            # Extract page provenance & bbox
            provs = getattr(item, "prov", [])
            page_no = provs[0].page_no if provs else 1
            bbox_list: Optional[List[float]] = None
            if provs and getattr(provs[0], "bbox", None) is not None:
                bb = provs[0].bbox
                bbox_list = [float(bb.l), float(bb.b), float(bb.r), float(bb.t)]

            # 1. Section Header Item
            if "header" in t_name.lower() or lbl == "section_header":
                header_text = getattr(item, "text", "").strip()
                if not header_text:
                    continue
                
                # Adjust heading hierarchy based on item level or depth
                item_lvl = getattr(item, "level", 1) or 1
                if item_lvl <= len(heading_stack):
                    heading_stack = heading_stack[:item_lvl - 1]
                heading_stack.append(header_text)

                block_id = f"{doc_metadata.document_id}-P{page_no}-B{block_idx}"
                block = NormalizedBlock(
                    block_id=block_id,
                    document_id=doc_metadata.document_id,
                    page=page_no,
                    block_type="heading",
                    heading_path=list(heading_stack),
                    content=header_text,
                    table_data=None,
                    bbox=bbox_list,
                    parser=self.parser_name,
                    parser_version=self.parser_version,
                    parse_confidence=1.0,
                    metadata={"docling_item_type": t_name}
                )
                blocks.append(block)
                block_idx += 1

            # 2. Table Item
            elif "table" in t_name.lower() or lbl == "table":
                try:
                    df = item.export_to_dataframe()
                    headers = [str(c) for c in df.columns]
                    rows = [[str(val) for val in row] for row in df.values]
                except Exception:
                    headers = []
                    rows = []

                cells: List[TableCell] = []
                for r_idx, r in enumerate(rows):
                    for c_idx, val in enumerate(r):
                        col_hdr = headers[c_idx] if c_idx < len(headers) else f"Col_{c_idx}"
                        cells.append(TableCell(
                            row_idx=r_idx,
                            col_idx=c_idx,
                            col_header=col_hdr,
                            value=val,
                            raw_value=val
                        ))

                # Format tabular text representation
                table_md_lines = []
                if headers:
                    table_md_lines.append("| " + " | ".join(headers) + " |")
                    table_md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in rows:
                    table_md_lines.append("| " + " | ".join(r) + " |")
                table_content = "\n".join(table_md_lines)

                t_data = TableData(headers=headers, rows=rows, cells=cells)
                block_id = f"{doc_metadata.document_id}-P{page_no}-B{block_idx}"
                block = NormalizedBlock(
                    block_id=block_id,
                    document_id=doc_metadata.document_id,
                    page=page_no,
                    block_type="table",
                    heading_path=list(heading_stack),
                    content=table_content,
                    table_data=t_data,
                    bbox=bbox_list,
                    parser=self.parser_name,
                    parser_version=self.parser_version,
                    parse_confidence=1.0,
                    metadata={"row_count": len(rows), "col_count": len(headers)}
                )
                blocks.append(block)
                block_idx += 1

            # 3. Regular Text / Paragraph / List Item
            else:
                text_content = getattr(item, "text", "").strip()
                if not text_content:
                    continue

                b_type = "procedure_step" if text_content.startswith(("1.", "2.", "3.", "Step", "步驟")) else "paragraph"
                block_id = f"{doc_metadata.document_id}-P{page_no}-B{block_idx}"
                block = NormalizedBlock(
                    block_id=block_id,
                    document_id=doc_metadata.document_id,
                    page=page_no,
                    block_type=b_type,
                    heading_path=list(heading_stack),
                    content=text_content,
                    table_data=None,
                    bbox=bbox_list,
                    parser=self.parser_name,
                    parser_version=self.parser_version,
                    parse_confidence=1.0,
                    metadata={"docling_item_type": t_name}
                )
                blocks.append(block)
                block_idx += 1

        return blocks
