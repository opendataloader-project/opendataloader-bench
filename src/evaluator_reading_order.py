"""Reading order similarity that ignores table content."""

import re
from typing import Tuple, Optional

from rapidfuzz import fuzz

from converter_markdown_table import convert_to_markdown_with_html_tables

_HTML_TABLE_PATTERN = re.compile(r"<table[^>]*?>.*?</table>", re.IGNORECASE | re.DOTALL)


_EMPHASIS_PATTERN = re.compile(r"(\*{1,3}|~~|__|_)(\S(?:.*?\S)?)\1", re.DOTALL)


def _strip_emphasis(text: str) -> str:
    """Remove markdown emphasis markers (bold/italic/strikethrough), keeping content.

    NID compares character streams, so engines that emit valid markdown
    emphasis (``**bold**``, ``*italic*``) are otherwise penalized on every
    marker character relative to plain-text ground truth, even when the
    extracted text and its order are identical. Applied iteratively to
    unwrap nested markers (``***both***``).
    """
    prev = None
    while prev != text:
        prev = text
        text = _EMPHASIS_PATTERN.sub(r"\2", text)
    return text


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _strip_emphasis(text)).strip()


def _strip_tables(text: str) -> str:
    without_html = _HTML_TABLE_PATTERN.sub(" ", text)
    return without_html


def evaluate_reading_order(
    gt: str, pred: str
) -> Tuple[Optional[float], Optional[float]]:
    gt_with_html = convert_to_markdown_with_html_tables(gt)
    gt_normalized = _normalize(gt_with_html)
    gt_stripped = _strip_tables(gt_with_html or "")
    gt_stripped_normalized = _normalize(gt_stripped)
    if not gt_normalized:
        return None, None

    pred_with_html = convert_to_markdown_with_html_tables(pred)
    pred_normalized = _normalize(pred_with_html)
    pred_stripped = _strip_tables(pred_with_html or "")
    pred_stripped_normalized = _normalize(pred_stripped)

    nid_score = fuzz.ratio(gt_normalized, pred_normalized) / 100.0
    nid_s_score = fuzz.ratio(gt_stripped_normalized, pred_stripped_normalized) / 100.0

    return nid_score, nid_s_score
