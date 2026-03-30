"""Centralised definitions for available PDF parsing engines."""

from __future__ import annotations

from typing import Callable, Dict

import pdf_parser_docling as docling
import pdf_parser_liteparse as liteparse
import pdf_parser_markitdown as markitdown
import pdf_parser_opendataloader as opendataloader
import pdf_parser_opendataloader_hybrid as opendataloader_hybrid
import pdf_parser_opendataloader_hybrid_docling_fast as opendataloader_hybrid_docling_fast
import pdf_parser_opendataloader_hybrid_hancom as opendataloader_hybrid_hancom

EngineHandler = Callable[..., None]


ENGINES: Dict[str, str] = {
    "opendataloader": "2.1.1",
    "opendataloader-hybrid": "2.1.1",
    "opendataloader-hybrid-docling-fast": "2.1.1",
    "opendataloader-hybrid-hancom": "2.1.1",
    "docling": "2.82.0",
    "liteparse": "0.1.0",
    "markitdown": "0.1.4",
}


ENGINE_DISPATCH: Dict[str, EngineHandler] = {
    "opendataloader": opendataloader.to_markdown,
    "opendataloader-hybrid": opendataloader_hybrid.to_markdown,
    "opendataloader-hybrid-docling-fast": opendataloader_hybrid_docling_fast.to_markdown,
    "opendataloader-hybrid-hancom": opendataloader_hybrid_hancom.to_markdown,
    "docling": docling.to_markdown,
    "liteparse": liteparse.to_markdown,
    "markitdown": markitdown.to_markdown,
}
