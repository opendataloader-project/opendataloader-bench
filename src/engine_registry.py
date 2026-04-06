"""Centralised definitions for available PDF parsing engines."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

EngineHandler = Callable[..., None]

# All known engines and their versions.
# Engines with existing prediction/ data are included even if not currently installable.
ENGINES: Dict[str, str] = {
    "opendataloader": "2.1.1",
    "opendataloader-hybrid": "2.1.1",
    "opendataloader-hybrid-docling-fast": "2.1.1",
    "opendataloader-hybrid-hancom": "2.1.1",
    "docling": "2.82.0",
    "markitdown": "0.1.4",
    "marker": "1.6.2",
    "mineru": "1.3.3",
    "pymupdf4llm": "0.0.17",
    "unstructured": "0.17.2",
    "edgeparse": "0.3.0",
    "nutrient": "1.0.0",
}

# Maps engine name → Python module name for lazy import.
_ENGINE_MODULES: Dict[str, str] = {
    "opendataloader": "pdf_parser_opendataloader",
    "opendataloader-hybrid": "pdf_parser_opendataloader_hybrid",
    "opendataloader-hybrid-docling-fast": "pdf_parser_opendataloader_hybrid_docling_fast",
    "opendataloader-hybrid-hancom": "pdf_parser_opendataloader_hybrid_hancom",
    "docling": "pdf_parser_docling",
    "markitdown": "pdf_parser_markitdown",
    "marker": "pdf_parser_marker",
    "mineru": "pdf_parser_mineru",
    "pymupdf4llm": "pdf_parser_pymupdf4llm",
    "unstructured": "pdf_parser_unstructured",
    "edgeparse": "pdf_parser_edgeparse",
    "nutrient": "pdf_parser_nutrient",
}


def get_engine_handler(engine_name: str) -> Optional[EngineHandler]:
    """Lazily import and return the to_markdown handler for the given engine.

    Returns None if the engine module or its dependencies are not installed.
    """
    module_name = _ENGINE_MODULES.get(engine_name)
    if module_name is None:
        logging.warning("No module mapping for engine '%s'", engine_name)
        return None

    try:
        import importlib
        mod = importlib.import_module(module_name)
        return mod.to_markdown
    except (ImportError, ModuleNotFoundError) as exc:
        logging.warning(
            "Engine '%s' is not available (module '%s'): %s",
            engine_name, module_name, exc,
        )
        return None


# Backward-compatible ENGINE_DISPATCH — populated lazily on first access.
class _LazyDispatch(dict):
    """Dict that lazily resolves engine handlers on first access."""

    def __getitem__(self, key: str) -> Optional[EngineHandler]:
        if key not in dict.keys(self):
            handler = get_engine_handler(key)
            if handler is not None:
                dict.__setitem__(self, key, handler)
                return handler
            return None
        return dict.__getitem__(self, key)

    def get(self, key: str, default=None) -> Optional[EngineHandler]:
        result = self.__getitem__(key)
        return result if result is not None else default


ENGINE_DISPATCH = _LazyDispatch()
