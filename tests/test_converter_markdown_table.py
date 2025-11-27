from textwrap import dedent

from converter_markdown_table import convert_to_markdown_with_html_tables


def test_markdown_tables_are_converted_with_surrounding_content_preserved() -> None:
    markdown = dedent(
        """
        # Title

        Intro paragraph.

        - item 1
        - item 2

        | Header A | Header B |
        | -------- | -------- |
        | cell 1   | cell 2   |
        | cell 3   | cell 4   |

        Closing paragraph.
        """
    ).lstrip()

    expected_table = (
        "<table><tr><th>Header A</th><th>Header B</th></tr>"
        "<tr><td>cell 1</td><td>cell 2</td></tr>"
        "<tr><td>cell 3</td><td>cell 4</td></tr></table>\n"
    )

    converted = convert_to_markdown_with_html_tables(markdown)

    assert "# Title" in converted
    assert "Intro paragraph." in converted
    assert "- item 1" in converted
    assert "- item 2" in converted
    assert expected_table in converted
    assert "Closing paragraph." in converted


def test_markdown_tables_reconstruction() -> None:
    markdown = dedent(
        r"""
        |  |  |  |  |  |  |  |
        | --- | --- | --- | --- | --- | --- | --- |
        | AMS | Average Annual Growth | Remittance inflows in 2020 (US$ Million) |
        |  | 2000-2004 |  | 2004-2009 | 2009-2014 | 2014-2019 | 2019-2020 |
        | Cambodia | 7.5% | \-0.7% | 50.6% | 6.7% | \-16.6% | 1,272 |
        | Indonesia | 9.4% | 29.5% | 4.7% | 6.4% | \-17.3% | 9,651 |
        | Lao PDR | 4.0% | 115.7% | 38.0% | 9.5% | \-10.6% | 265 |
        | Malaysia | 18.6% | 7.1% | 6.9% | 0.7% | \-11.2% | 1,454 |
        | Myanmar | 2.7% | \-14.1% | 102.7% | 5.4% | \-7.1% | 2,250 |
        | Philippines | 10.6% | 11.7% | 7.5% | 4.2% | \-0.7% | 34,913 |
        | Thailand | \-0.9% | 18.6% | 11.4% | 4.6% | \-1.2% | 8,067 |
        | Viet Nam | 11.5% | 21.1% | 14.8% | 7.2% | 1.2% | 17,200 |
        """
    ).lstrip()

    expected_table = (
        "<table>"
        "<tr><th>AMS</th><th>Average Annual Growth</th><th>Average Annual Growth</th>"
        "<th>Average Annual Growth</th><th>Average Annual Growth</th>"
        "<th>Average Annual Growth</th><th>Remittance inflows in 2020 (US$ Million)</th></tr>"
        "<tr><td></td><td>2000-2004</td><td></td><td>2004-2009</td>"
        "<td>2009-2014</td><td>2014-2019</td><td>2019-2020</td></tr>"
        "<tr><td>Cambodia</td><td>7.5%</td><td>\\-0.7%</td><td>50.6%</td>"
        "<td>6.7%</td><td>\\-16.6%</td><td>1,272</td></tr>"
        "<tr><td>Indonesia</td><td>9.4%</td><td>29.5%</td><td>4.7%</td>"
        "<td>6.4%</td><td>\\-17.3%</td><td>9,651</td></tr>"
        "<tr><td>Lao PDR</td><td>4.0%</td><td>115.7%</td><td>38.0%</td>"
        "<td>9.5%</td><td>\\-10.6%</td><td>265</td></tr>"
        "<tr><td>Malaysia</td><td>18.6%</td><td>7.1%</td><td>6.9%</td>"
        "<td>0.7%</td><td>\\-11.2%</td><td>1,454</td></tr>"
        "<tr><td>Myanmar</td><td>2.7%</td><td>\\-14.1%</td><td>102.7%</td>"
        "<td>5.4%</td><td>\\-7.1%</td><td>2,250</td></tr>"
        "<tr><td>Philippines</td><td>10.6%</td><td>11.7%</td><td>7.5%</td>"
        "<td>4.2%</td><td>\\-0.7%</td><td>34,913</td></tr>"
        "<tr><td>Thailand</td><td>\\-0.9%</td><td>18.6%</td><td>11.4%</td>"
        "<td>4.6%</td><td>\\-1.2%</td><td>8,067</td></tr>"
        "<tr><td>Viet Nam</td><td>11.5%</td><td>21.1%</td><td>14.8%</td>"
        "<td>7.2%</td><td>1.2%</td><td>17,200</td></tr>"
        "</table>\n"
    )

    converted = convert_to_markdown_with_html_tables(markdown)
    assert expected_table in converted
