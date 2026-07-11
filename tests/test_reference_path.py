"""Tests for reference.json path resolution.

Regression: the harness resolved reference.json under ``ground-truth/markdown/``
(the GT *markdown* dir) where the file does not exist, so ``run.py`` silently
skipped table-detection (and triage) evaluation and the ``table_detection_f1``
regression gate could never fire.
"""
import json
from pathlib import Path

import run
from evaluator_table_detection import evaluate_table_detection_batch


def test_default_reference_path_points_to_existing_file():
    """The default reference path must resolve to the real reference.json."""
    args = run._parse_args(["--engine", "opendataloader"])
    project_root = Path(run.__file__).parent.parent
    reference_path = run.resolve_reference_path(args, project_root)
    assert reference_path.name == "reference.json"
    assert reference_path.exists(), (
        f"reference.json must resolve to an existing file, got {reference_path}"
    )


def test_reference_path_independent_of_ground_truth_dir_override():
    """Overriding --ground-truth-dir must not move the reference.json path."""
    args = run._parse_args(
        ["--engine", "opendataloader", "--ground-truth-dir", "/some/other/gt"]
    )
    project_root = Path(run.__file__).parent.parent
    reference_path = run.resolve_reference_path(args, project_root)
    # Still anchored at the repo's ground-truth/reference.json, not /some/other/gt.
    assert reference_path == project_root / "ground-truth" / "reference.json"


def test_table_detection_f1_on_synthetic_corpus(tmp_path):
    """Safety net: evaluate_table_detection_batch scores tables correctly given a
    valid reference.json + markdown dir (independent of the path bug)."""
    reference = {
        "with_table.pdf": {"elements": [{"category": "Table", "page": 1}]},
        "text_only.pdf": {"elements": [{"category": "Paragraph", "page": 1}]},
    }
    reference_path = tmp_path / "reference.json"
    reference_path.write_text(json.dumps(reference), encoding="utf-8")

    markdown_dir = tmp_path / "markdown"
    markdown_dir.mkdir()
    (markdown_dir / "with_table.md").write_text(
        "| h1 | h2 |\n| --- | --- |\n| 1 | 2 |\n", encoding="utf-8"
    )
    (markdown_dir / "text_only.md").write_text("Just a paragraph.\n", encoding="utf-8")

    metrics = evaluate_table_detection_batch(reference_path, markdown_dir).to_dict()
    assert metrics["tp"] == 1 and metrics["tn"] == 1
    assert metrics["fp"] == 0 and metrics["fn"] == 0
    assert metrics["f1"] == 1.0
