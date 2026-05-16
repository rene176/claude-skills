# ─── count_columns ────────────────────────────────────────────────────────────


def test_count_columns_three(validate_markdown):
    assert validate_markdown.count_columns("| a | b | c |") == 3


def test_count_columns_two(validate_markdown):
    assert validate_markdown.count_columns("| x | y |") == 2


def test_count_columns_escaped_pipe(validate_markdown):
    # \| inside a cell must not be counted as a column boundary
    assert validate_markdown.count_columns(r"| a\|b | c |") == 2


def test_count_columns_one(validate_markdown):
    assert validate_markdown.count_columns("| x |") == 1


# ─── is_table_row ─────────────────────────────────────────────────────────────


def test_is_table_row_valid(validate_markdown):
    assert validate_markdown.is_table_row("| a | b |") is True


def test_is_table_row_no_trailing_pipe(validate_markdown):
    assert validate_markdown.is_table_row("| a | b") is False


def test_is_table_row_no_leading_pipe(validate_markdown):
    assert validate_markdown.is_table_row("a | b |") is False


def test_is_table_row_too_short(validate_markdown):
    assert validate_markdown.is_table_row("||") is False


def test_is_table_row_empty(validate_markdown):
    assert validate_markdown.is_table_row("") is False


# ─── is_separator_row ─────────────────────────────────────────────────────────


def test_is_separator_row_dashes(validate_markdown):
    assert validate_markdown.is_separator_row("| --- | --- |") is True


def test_is_separator_row_colons(validate_markdown):
    assert validate_markdown.is_separator_row("| :---: | ---: |") is True


def test_is_separator_row_single_dash(validate_markdown):
    assert validate_markdown.is_separator_row("| - |") is True


def test_is_separator_row_rejects_data(validate_markdown):
    assert validate_markdown.is_separator_row("| Name | Value |") is False


def test_is_separator_row_no_outer_pipes(validate_markdown):
    assert validate_markdown.is_separator_row("--- | ---") is False


# ─── is_html_comment ──────────────────────────────────────────────────────────


def test_is_html_comment_true(validate_markdown):
    assert validate_markdown.is_html_comment("<!-- comment -->") is True


def test_is_html_comment_false(validate_markdown):
    assert validate_markdown.is_html_comment("regular text") is False


def test_is_html_comment_inline(validate_markdown):
    assert validate_markdown.is_html_comment("text <!-- note --> more") is True


# ─── validate_file ────────────────────────────────────────────────────────────


def test_validate_file_clean_table(validate_markdown, tmp_path):
    f = tmp_path / "clean.md"
    f.write_text("| Col A | Col B |\n| --- | --- |\n| val1 | val2 |\n")
    assert validate_markdown.validate_file(f) == []


def test_validate_file_unclosed_code_block(validate_markdown, tmp_path):
    f = tmp_path / "unclosed.md"
    f.write_text("Some text\n```python\ndef foo(): pass\n")
    issues = validate_markdown.validate_file(f)
    assert len(issues) == 1
    assert issues[0].issue_type == validate_markdown.IssueType.UNCLOSED_CODE_BLOCK
    assert issues[0].line == 2  # ``` fence is on line 2


def test_validate_file_closed_code_block_no_issue(validate_markdown, tmp_path):
    f = tmp_path / "closed.md"
    f.write_text("```python\ndef foo(): pass\n```\n")
    assert validate_markdown.validate_file(f) == []


def test_validate_file_html_comment_in_table(validate_markdown, tmp_path):
    f = tmp_path / "html_comment.md"
    f.write_text("| Col |\n<!-- comment -->\n| --- |\n")
    issues = validate_markdown.validate_file(f)
    assert any(i.issue_type == validate_markdown.IssueType.HTML_IN_TABLE for i in issues)


def test_validate_file_missing_separator(validate_markdown, tmp_path):
    f = tmp_path / "no_sep.md"
    f.write_text("| Col A | Col B |\n| val1 | val2 |\n")
    issues = validate_markdown.validate_file(f)
    assert any(i.issue_type == validate_markdown.IssueType.MISSING_SEPARATOR for i in issues)


def test_validate_file_column_mismatch(validate_markdown, tmp_path):
    f = tmp_path / "mismatch.md"
    f.write_text("| A | B | C |\n| --- | --- | --- |\n| x | y |\n")
    issues = validate_markdown.validate_file(f)
    assert any(i.issue_type == validate_markdown.IssueType.COLUMN_MISMATCH for i in issues)


def test_validate_file_table_in_code_block_ignored(validate_markdown, tmp_path):
    f = tmp_path / "table_in_code.md"
    f.write_text("```\n| A | B |\n| val | val |\n```\n")
    assert validate_markdown.validate_file(f) == []


# ─── validate_directory ───────────────────────────────────────────────────────


def test_validate_directory_recurses(validate_markdown, tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (tmp_path / "clean.md").write_text("| A | B |\n| --- | --- |\n| x | y |\n")
    (sub / "broken.md").write_text("```\ndef foo(): pass\n")  # unclosed fence
    issues = validate_markdown.validate_directory(tmp_path)
    assert len(issues) == 1
    assert issues[0].issue_type == validate_markdown.IssueType.UNCLOSED_CODE_BLOCK
