# -*- coding: utf-8 -*-
"""
Parser Router for Grounded Industrial RAG.
Dispatches incoming documents to the appropriate parser adapter based on file extension
and metadata characteristics (.md/.txt -> StructuredParser, .pdf -> DoclingParser).
Ensures non-silent error handling with detailed extraction diagnostics.
"""

import os
import time
import hashlib
from typing import List, Dict, Any, Optional
from core.interfaces import BaseParser
from core.schema import NormalizedBlock, SourceDocument
from adapters.parsers.structured_parser import StructuredParser
from adapters.parsers.docling_parser import DoclingParser


class ParserRouter(BaseParser):
    """
    Lightweight Router that chooses between StructuredParser and DoclingParser.
    """

    def __init__(
        self,
        structured_parser: Optional[BaseParser] = None,
        docling_parser: Optional[BaseParser] = None,
        enable_ocr: bool = True
    ) -> None:
        self.structured_parser = structured_parser or StructuredParser()
        self._docling_parser = docling_parser
        self.enable_ocr = enable_ocr
        self.last_run_metrics: Dict[str, Any] = {}

    def _get_docling_parser(self) -> BaseParser:
        if self._docling_parser is None:
            self._docling_parser = DoclingParser(enable_ocr=self.enable_ocr)
        return self._docling_parser

    def parse(self, file_path: str, doc_metadata: SourceDocument) -> List[NormalizedBlock]:
        """
        Routes the file to the appropriate parser adapter.
        Does not fail silently; produces comprehensive execution diagnostics.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found for parsing: {file_path}")

        start_time = time.time()
        ext = os.path.splitext(file_path)[1].lower()

        # Compute source file sha256 for verification
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            source_file_hash = hashlib.sha256(file_bytes).hexdigest()

        parser_used: str = ""
        ocr_used = False
        blocks: List[NormalizedBlock] = []

        try:
            if ext in [".md", ".markdown", ".txt"]:
                parser_used = "structured_parser"
                blocks = self.structured_parser.parse(file_path, doc_metadata)
            elif ext == ".pdf":
                parser_used = "docling"
                docling = self._get_docling_parser()
                blocks = docling.parse(file_path, doc_metadata)
                ocr_used = self.enable_ocr
            else:
                raise ValueError(
                    f"Unsupported file format '{ext}' for file {file_path}. "
                    "Supported formats: .md, .txt, .pdf"
                )

            elapsed = round(time.time() - start_time, 4)
            table_count = sum(1 for b in blocks if b.block_type == "table")
            pages = set(b.page for b in blocks) if blocks else {1}

            self.last_run_metrics = {
                "success": True,
                "file_path": file_path,
                "document_id": doc_metadata.document_id,
                "source_file_hash": source_file_hash,
                "parser_used": parser_used,
                "elapsed_seconds": elapsed,
                "page_count": len(pages),
                "blocks_extracted": len(blocks),
                "tables_extracted": table_count,
                "ocr_used": ocr_used,
                "warning_summary": None,
                "exception_summary": None
            }
            return blocks

        except Exception as e:
            elapsed = round(time.time() - start_time, 4)
            self.last_run_metrics = {
                "success": False,
                "file_path": file_path,
                "document_id": doc_metadata.document_id,
                "source_file_hash": source_file_hash,
                "parser_used": parser_used or "unknown",
                "elapsed_seconds": elapsed,
                "page_count": 0,
                "blocks_extracted": 0,
                "tables_extracted": 0,
                "ocr_used": ocr_used,
                "warning_summary": None,
                "exception_summary": str(e)
            }
            raise RuntimeError(f"ParserRouter failed on {file_path} via {parser_used}: {str(e)}") from e
