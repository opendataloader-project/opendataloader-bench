# src/speed_benchmark/parsers/__init__.py
import importlib


def get_available_parsers():
    parsers = []
    parser_classes = [
        ("opendataloader", "OpenDataLoaderParser"),
        ("docling", "DoclingParser"),
        ("markitdown", "MarkItDownParser"),
        ("pymupdf", "PyMuPDFParser"),
        ("pypdf", "PyPDFParser"),
        ("liteparse_cli", "LiteParseCliParser"),
        ("liteparse_js", "LiteParseJsParser"),
        ("edgeparse", "EdgeParseParser"),
        ("unstructured", "UnstructuredParser"),
        ("nutrient", "NutrientParser"),
    ]
    for module_name, class_name in parser_classes:
        try:
            mod = importlib.import_module(f".{module_name}", package="speed_benchmark.parsers")
            cls = getattr(mod, class_name)
            parsers.append(cls())
        except (ImportError, AttributeError):
            pass
    return parsers


ALL_PARSERS = get_available_parsers()
