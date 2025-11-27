from pytest import approx

from evaluator_heading_level import evaluate_heading_level


def test_empty_documents_return_none_scores():
    mhs, mhs_s = evaluate_heading_level("", "")
    assert mhs is None
    assert mhs_s is None


def test_ground_truth_without_headings_returns_none_scores():
    mhs, mhs_s = evaluate_heading_level("Just some text", "# Heading\nContent")
    assert mhs is None
    assert mhs_s is None


def test_identical_documents_return_perfect_score():
    markdown = "# Title\nSome content\nAnother line"
    mhs, mhs_s = evaluate_heading_level(markdown, markdown)
    assert mhs == approx(1.0)
    assert mhs_s == approx(1.0)


def test_prediction_missing_heading_returns_zero_scores():
    gt = "# Title\nSome content"
    pred = "Title\nSome content"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs == approx(0.0)
    assert mhs_s == approx(0.0)


def test_heading_levels_are_treated_equally():
    gt = "# Title\nDetails\n## Subsection\nMore text"
    pred = "### Title\nDetails\n# Subsection\nMore text"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs == approx(1.0)
    assert mhs_s == approx(1.0)


def test_missing_section_penalizes_similarity():
    gt = "# Intro\nWelcome\n# Details\nDeep dive"
    pred = "# Intro\nWelcome"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs > 0.0
    assert mhs < 1.0
    assert mhs_s < 1.0
    assert mhs_s >= mhs


def test_content_change_within_section_impacts_score():
    gt = "# Intro\nWelcome to the document"
    pred = "# Intro\nGreetings from another document"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs > 0.5
    assert mhs < 1.0
    assert mhs_s == approx(1.0)


def test_markdown_table_content_is_ignored_for_text_similarity():
    gt = "# Section\n| Col1 | Col2 |\n| --- | --- |\n| A | B |"
    pred = "# Section\n| Col1 | Col2 |\n| --- | --- |\n| Different | Values |"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs < 1.0
    assert mhs_s == approx(1.0)


def test_html_table_content_is_ignored_for_text_similarity():
    gt = "# Section\n<table><tr><td>A</td><td>B</td></tr></table>"
    pred = "# Section\n<table><tr><td>X</td><td>Y</td></tr></table>"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs < 1.0
    assert mhs_s == approx(1.0)


def test_cross_format_tables_are_ignored_for_text_similarity():
    gt = "# Section\n<table><tr><td>A</td><td>B</td></tr></table>"
    pred = "# Section\n| Col1 | Col2 |\n| --- | --- |\n| A | B |"
    mhs, mhs_s = evaluate_heading_level(gt, pred)
    assert mhs < 1.0
    assert mhs_s == approx(1.0)
