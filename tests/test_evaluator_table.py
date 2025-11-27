from pytest import approx

from evaluator_table import evaluate_table


def test_returns_none_scores_when_ground_truth_missing():
    teds_score, teds_s_score = evaluate_table("No table here", "No table either")
    assert teds_score is None
    assert teds_s_score is None


def test_returns_zero_when_only_ground_truth_has_table():
    gt = "<table><tr><td>cell</td></tr></table>"
    pred = "Plain text"
    teds_score, teds_s_score = evaluate_table(gt, pred)
    assert teds_score == approx(0.0)
    assert teds_s_score == approx(0.0)


def test_identical_html_tables_return_perfect_scores():
    table = "<table><tr><td>abc</td></tr></table>"
    teds_score, teds_s_score = evaluate_table(table, table)
    assert teds_score == approx(1.0)
    assert teds_s_score == approx(1.0)


def test_content_difference_affects_teds_score_only():
    gt = "<table><tr><td>abc</td></tr></table>"
    pred = "<table><tr><td>xyz</td></tr></table>"
    teds_score, teds_s_score = evaluate_table(gt, pred)
    assert teds_score > 0.0
    assert teds_score < 1.0
    assert teds_s_score == approx(1.0)


def test_markdown_table_is_converted_to_html():
    markdown = "| Col1 | Col2 |\n| --- | --- |\n| A | B |"
    html_table = "<table><tr><td>Col1</td><td>Col2</td></tr><tr><td>A</td><td>B</td></tr></table>"
    teds_score, teds_s_score = evaluate_table(markdown, html_table)
    assert teds_score == approx(1.0)
    assert teds_s_score == approx(1.0)


def test_thead_tbody_tags_are_ignored():
    gt = "<table><thead><tr><th>Col1</th></tr></thead><tbody><tr><td>A</td></tr></tbody></table>"
    pred = "<table><tr><th>Col1</th></tr><tr><td>A</td></tr></table>"
    teds_score, teds_s_score = evaluate_table(gt, pred)
    assert teds_score == approx(1.0)
    assert teds_s_score == approx(1.0)


def test_similar_but_not_identical_tables_keep_high_scores():
    gt = (
        "<table><tr><th>Item</th><th>Qty</th></tr>"
        "<tr><td>Apple</td><td>10</td></tr>"
        "<tr><td>Orange</td><td>5</td></tr></table>"
    )
    pred = (
        "<table><tr><th>Item</th><th>Qty</th></tr>"
        "<tr><td>Apple</td><td>10</td></tr>"
        "<tr><td>Orange</td><td>6</td></tr></table>"
    )

    teds_score, teds_s_score = evaluate_table(gt, pred)

    assert teds_score > 0.8
    assert teds_score < 1.0
    assert teds_s_score == approx(1.0)


def test_partially_mismatched_tables_drop_scores():
    gt = (
        "<table><thead><tr><th>Item</th><th>Qty</th></tr></thead>"
        "<tbody><tr><td>Apple</td><td>10</td></tr>"
        "<tr><td>Orange</td><td>5</td></tr></tbody></table>"
    )
    pred = (
        "<table><tr><th>Product</th><th>Price</th><th>Stock</th></tr>"
        "<tr><td>Apple</td><td>$1</td><td>Yes</td></tr>"
        "<tr><td>Orange</td><td>$2</td><td>No</td></tr></table>"
    )

    teds_score, teds_s_score = evaluate_table(gt, pred)

    assert teds_score > 0.0
    assert teds_score < 0.7
    assert teds_s_score < 0.8


def test_textual_difference_with_identical_structure_affects_teds():
    gt = (
        "| IX - Zamboanga Peninsula   |   4 |   2 |   4 |\n"
        "|----------------------------|-----|-----|-----|\n"
        "| X-Northern Mindanao        |   2 |   2 |   2 |\n"
        "| XI - Davao Region          |   1 |   3 |   5 |\n"
        "| XII - SOCCSKSARGEN         |   2 |   2 |   1 |\n"
        "| XIII - Caraga              |   1 |   3 |   3 |\n"
        "| ARMM                       |   1 |   2 |   2 |\n"
        "| Party-List                 |  10 |  15 |  20 |\n"
        "| TOTAL (w/ Party- List)     |  55 |  66 |  88 |\n"
        "| TOTAL (w/o Party- List)    |  45 |  51 |  68 |\n"
    )
    pred = (
        "<table>"
        "  <tr>"
        "    <td>IX - Zamboanga Peninsula</td>"
        "    <td>4</td>"
        "    <td>2</td>"
        "    <td>4</td>"
        "  </tr>"
        "  <tr>"
        "    <td>X - Northern Mindanao</td>"
        "    <td>2</td>"
        "    <td>2</td>"
        "    <td>2</td>"
        "  </tr>"
        "  <tr>"
        "    <td>XI - Davao Region</td>"
        "    <td>1</td>"
        "    <td>3</td>"
        "    <td>5</td>"
        "  </tr>"
        "  <tr>"
        "    <td>XII - SOCCSKSARGEN</td>"
        "    <td>2</td>"
        "    <td>2</td>"
        "    <td>1</td>"
        "  </tr>"
        "  <tr>"
        "    <td>XIII - Caraga</td>"
        "    <td>1</td>"
        "    <td>3</td>"
        "    <td>3</td>"
        "  </tr>"
        "  <tr>"
        "    <td>ARMM</td>"
        "    <td>1</td>"
        "    <td>2</td>"
        "    <td>2</td>"
        "  </tr>"
        "  <tr>"
        "    <td>Party-List</td>"
        "    <td>10</td>"
        "    <td>15</td>"
        "    <td>20</td>"
        "  </tr>"
        "  <tr>"
        "    <td>TOTAL (w/ PartyList)</td>"
        "    <td>55</td>"
        "    <td>66</td>"
        "    <td>88</td>"
        "  </tr>"
        "  <tr>"
        "    <td>TOTAL (w/o PartyList)</td>"
        "    <td>45</td>"
        "    <td>51</td>"
        "    <td>68</td>"
        "  </tr>"
        "</table>"
    )

    teds_score, teds_s_score = evaluate_table(gt, pred)

    assert teds_s_score == approx(1.0)
    assert teds_score < 1.0
    assert teds_score > 0.4


def test_calc_table_score_handles_whitespace_only_differences() -> None:
    gt = "<table><tr><td>content is here</td></tr></table>"
    pred = (
        """<table>  \n <tr><td>\n   content is \n here\n\n  </td>  \n </tr></table>"""
    )

    teds_score, teds_s_score = evaluate_table(gt, pred)

    assert teds_s_score == approx(1.0)
    assert teds_score == approx(1.0)
