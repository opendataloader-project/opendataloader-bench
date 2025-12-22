"""Centralised definitions for available PDF parsing engines."""

from __future__ import annotations

from typing import Callable, Dict

import pdf_parser_docling as docling
import pdf_parser_markitdown as markitdown
import pdf_parser_opendataloader as opendataloader

EngineHandler = Callable[..., None]


ENGINES: Dict[str, str] = {
    "opendataloader": "1.5.1",
    "docling": "2.65.0",
    "markitdown": "0.1.4",
}


ENGINE_DISPATCH: Dict[str, EngineHandler] = {
    "opendataloader": opendataloader.to_markdown,
    "docling": docling.to_markdown,
    "markitdown": markitdown.to_markdown,
}
