"""Centralised definitions for available PDF parsing engines."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

EngineHandler = Callable[..., None]

# Runnable engines — have parser code in this repo.
ENGINES: Dict[str, str] = {
    "opendataloader": "2.2.1",
    "opendataloader-hybrid": "2.2.1",
    "opendataloader-hybrid-docling-fast": "2.2.1",
    "docling": "2.84.0",
    "markitdown": "0.1.5",
    "unstructured": "0.17.2",
    "unstructured-hires": "0.17.2",
    "edgeparse": "0.3.0",
    "liteparse": "1.2.1",
}

# Data-only engines — no parser code, but prediction/ results are preserved
# for chart display. Code removed to avoid license/commercial-tier entanglement
# (AGPL/GPL/commercial).
DATA_ONLY_ENGINES: Dict[str, str] = {
    "marker": "1.6.2",
    "mineru": "1.3.3",
    "pymupdf4llm": "0.0.17",
    "nutrient": "1.0.1",
    "opendataloader-hybrid-hydrogen": "2.2.1",
    "opendataloader-hybrid-helium": "0.2.0",
}

# Engines excluded from chart display (internal/experimental).
_CHART_EXCLUDED: set = {
    "opendataloader-hybrid-hydrogen",
    "opendataloader-hybrid-helium",
}

# All engines whose evaluation data should appear in charts.
ALL_CHART_ENGINES: Dict[str, str] = {
    k: v for k, v in {**ENGINES, **DATA_ONLY_ENGINES}.items()
    if k not in _CHART_EXCLUDED
}

# Maps engine name → Python module name for lazy import.
_ENGINE_MODULES: Dict[str, str] = {
    "opendataloader": "pdf_parser_opendataloader",
    "opendataloader-hybrid": "pdf_parser_opendataloader_hybrid",
    "opendataloader-hybrid-docling-fast": "pdf_parser_opendataloader_hybrid_docling_fast",
    "docling": "pdf_parser_docling",
    "markitdown": "pdf_parser_markitdown",
    "unstructured": "pdf_parser_unstructured",
    "unstructured-hires": "pdf_parser_unstructured_hires",
    "edgeparse": "pdf_parser_edgeparse",
    "liteparse": "pdf_parser_liteparse",
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
