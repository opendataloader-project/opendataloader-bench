"""Centralised definitions for available PDF parsing engines."""

from __future__ import annotations

from typing import Callable, Dict

import pdf_parser_docling as docling
import pdf_parser_marker as marker
import pdf_parser_markitdown as markitdown
import pdf_parser_opendataloader as opendataloader
import pdf_parser_opendataloader_hybrid as opendataloader_hybrid

EngineHandler = Callable[..., None]


ENGINES: Dict[str, str] = {
    "opendataloader": "1.6.2",
    "opendataloader-hybrid": "1.6.2",
    "docling": "2.65.0",
    "markitdown": "0.1.4",
    "marker": "1.10.1",
}


ENGINE_DISPATCH: Dict[str, EngineHandler] = {
    "opendataloader": opendataloader.to_markdown,
    "opendataloader-hybrid": opendataloader_hybrid.to_markdown,
    "docling": docling.to_markdown,
    "markitdown": markitdown.to_markdown,
    "marker": marker.to_markdown,
}
