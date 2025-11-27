from pytest import approx

from evaluator_reading_order import evaluate_reading_order


def test_empty_ground_truth_returns_none():
    nid, nid_s = evaluate_reading_order("", "Anything")
    assert nid is None
    assert nid_s is None


def test_identical_sequences_return_perfect_score():
    text = "Cell 1 Cell 2 Cell 3"
    nid, nid_s = evaluate_reading_order(text, text)
    assert nid == approx(1.0)
    assert nid_s == approx(1.0)


def test_whitespace_differences_are_ignored():
    gt = "Cell 1\nCell 2\tCell 3"
    pred = "Cell 1   Cell 2  Cell 3"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid == approx(1.0)
    assert nid_s == approx(1.0)


def test_partial_mismatch_reduces_score():
    gt = "Cell 1 Cell 2 Cell 3"
    pred = "Cell 1 Cell X Cell 3"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid > 0.5
    assert nid < 1.0
    assert nid_s > 0.5
    assert nid_s < 1.0


def test_completely_different_sequences_have_low_score():
    gt = "Cell 1 Cell 2 Cell 3"
    pred = "Row A Row B Row C"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid < 0.5
    assert nid_s < 0.5


def test_table_content_is_ignored():
    gt = "Cell 1\n<table><tr><td>Table data</td></tr></table>\nCell 2"
    pred = "Cell 1\n<table><tr><td>Different</td></tr></table>\nCell 2"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid < 1.0
    assert nid_s == approx(1.0)


def test_markdown_table_content_is_ignored():
    gt = "Intro\n| A | B |\n| - | - |\n| 1 | 2 |\nOutro"
    pred = "Intro\n| A | B |\n| - | - |\n| X | Y |\nOutro"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid < 1.0
    assert nid_s == approx(1.0)


def test_cross_format_tables_are_ignored():
    gt = "Intro\n<table><tr><td>A</td><td>B</td></tr></table>\nOutro"
    pred = "Intro\n| Col1 | Col2 |\n| --- | --- |\n| A | B |\nOutro"
    nid, nid_s = evaluate_reading_order(gt, pred)
    print(nid, nid_s)
    assert nid < 1.0
    assert nid_s == approx(1.0)


def test_very_different_length():
    gt = "Cell 1 Cell 2 Cell 3 Cell 4 Cell 5 Cell 6 Cell 7 Cell 8 Cell 9 Cell 10"
    pred = "Cell 1"
    nid, nid_s = evaluate_reading_order(gt, pred)
    assert nid < 0.3
    assert nid_s < 0.3
