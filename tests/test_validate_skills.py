# ─── helpers ──────────────────────────────────────────────────────────────────


def _fm(
    name: str = "test-skill",
    description: str = "Does things. Use when needed.",
    scope: str = "implementation",
    output_format: str = "code",
    domain: str = "backend",
    triggers: str = "test",
    extra_metadata: str = "",
) -> str:
    """Build a minimal valid frontmatter string."""
    return (
        f"name: {name}\n"
        f"description: {description}\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        f"  domain: {domain}\n"
        f"  triggers: {triggers}\n"
        "  role: specialist\n"
        f"  scope: {scope}\n"
        f"  output-format: {output_format}\n"
        '  related-skills: ""\n' + extra_metadata
    )


def _body_with_lines(n: int) -> str:
    """Return a body string with exactly n non-blank lines."""
    return "".join(f"- Line {i}\n" for i in range(n))


# ─── YamlChecker ──────────────────────────────────────────────────────────────


def test_yaml_checker_missing_skill_md(validate_skills, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    issues = validate_skills.YamlChecker().check(skill_dir, "my-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.ERROR
    assert "Missing SKILL.md" in issues[0].message


def test_yaml_checker_no_frontmatter_delimiter(validate_skills, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Title\nSome content\n")
    issues = validate_skills.YamlChecker().check(skill_dir, "my-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.ERROR


def test_yaml_checker_unclosed_frontmatter(validate_skills, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: foo\n")  # missing closing ---
    issues = validate_skills.YamlChecker().check(skill_dir, "my-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.ERROR


def test_yaml_checker_valid(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()
    assert validate_skills.YamlChecker().check(skill_dir, "test-skill") == []


# ─── RequiredFieldsChecker ────────────────────────────────────────────────────


def test_required_fields_missing_name(make_skill_dir, validate_skills):
    fm = "description: Does things. Use when needed.\nmetadata:\n  triggers: foo\n"
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.RequiredFieldsChecker().check(skill_dir, "test-skill")
    assert any("name" in i.message for i in issues)
    assert all(i.severity == validate_skills.Severity.ERROR for i in issues)


def test_required_fields_missing_description(make_skill_dir, validate_skills):
    fm = "name: test-skill\nmetadata:\n  triggers: foo\n"
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.RequiredFieldsChecker().check(skill_dir, "test-skill")
    assert any("description" in i.message for i in issues)


def test_required_fields_both_present(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()
    assert validate_skills.RequiredFieldsChecker().check(skill_dir, "test-skill") == []


def test_required_fields_invalid_yaml_defers(validate_skills, tmp_path):
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: foo\n")  # no closing ---
    # _extract_frontmatter returns None → defers to YamlChecker
    assert validate_skills.RequiredFieldsChecker().check(skill_dir, "bad-skill") == []


# ─── NameFormatChecker ────────────────────────────────────────────────────────


def test_name_format_valid_kebab(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(skill_name="my-skill-01")
    issues = validate_skills.NameFormatChecker().check(skill_dir, "my-skill-01")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert errors == []


def test_name_format_invalid_underscore(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(frontmatter=_fm(name="my_skill"))
    issues = validate_skills.NameFormatChecker().check(skill_dir, "test-skill")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert len(errors) == 1
    assert "my_skill" in errors[0].message


def test_name_format_dir_mismatch_is_warning(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(skill_name="test-skill", frontmatter=_fm(name="other-name"))
    issues = validate_skills.NameFormatChecker().check(skill_dir, "test-skill")
    warnings = [i for i in issues if i.severity == validate_skills.Severity.WARNING]
    assert any("test-skill" in w.message and "other-name" in w.message for w in warnings)


def test_name_format_match_no_mismatch_warning(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(skill_name="test-skill")
    issues = validate_skills.NameFormatChecker().check(skill_dir, "test-skill")
    warnings = [i for i in issues if i.severity == validate_skills.Severity.WARNING]
    assert warnings == []


# ─── DescriptionLengthChecker ─────────────────────────────────────────────────


def test_description_length_within_limit(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()
    assert validate_skills.DescriptionLengthChecker().check(skill_dir, "test-skill") == []


def test_description_length_exactly_at_limit(make_skill_dir, validate_skills):
    desc = "A" * 1012 + " Use when X."  # exactly 1024 chars
    skill_dir = make_skill_dir(frontmatter=_fm(description=desc))
    assert validate_skills.DescriptionLengthChecker().check(skill_dir, "test-skill") == []


def test_description_length_exceeds_limit(make_skill_dir, validate_skills):
    desc = "A" * 1013 + " Use when X."  # 1025 chars
    skill_dir = make_skill_dir(frontmatter=_fm(description=desc))
    issues = validate_skills.DescriptionLengthChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "1025" in issues[0].message


# ─── DescriptionFormatChecker ─────────────────────────────────────────────────


def test_description_format_contains_use_when(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()  # default description contains "Use when"
    assert validate_skills.DescriptionFormatChecker().check(skill_dir, "test-skill") == []


def test_description_format_missing_use_when(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(frontmatter=_fm(description="Just does things without trigger."))
    issues = validate_skills.DescriptionFormatChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "Use when" in issues[0].message


# ─── ScopeEnumChecker ─────────────────────────────────────────────────────────


def test_scope_enum_valid(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()  # default scope: implementation
    assert validate_skills.ScopeEnumChecker().check(skill_dir, "test-skill") == []


def test_scope_enum_invalid(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(frontmatter=_fm(scope="bogus-scope"))
    issues = validate_skills.ScopeEnumChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "bogus-scope" in issues[0].message


def test_scope_enum_missing_field_no_error(make_skill_dir, validate_skills):
    # Absence of the field is not an enum error (MetadataFieldsChecker handles that)
    fm = (
        "name: test-skill\n"
        "description: Does things. Use when needed.\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        "  domain: backend\n"
        "  triggers: test\n"
        "  role: specialist\n"
        "  output-format: code\n"  # no scope field
        '  related-skills: ""\n'
    )
    skill_dir = make_skill_dir(frontmatter=fm)
    assert validate_skills.ScopeEnumChecker().check(skill_dir, "test-skill") == []


# ─── OutputFormatEnumChecker ──────────────────────────────────────────────────


def test_output_format_enum_valid(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir()  # default output-format: code
    assert validate_skills.OutputFormatEnumChecker().check(skill_dir, "test-skill") == []


def test_output_format_enum_invalid(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(frontmatter=_fm(output_format="pdf"))
    issues = validate_skills.OutputFormatEnumChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "pdf" in issues[0].message


# ─── MetadataFieldsChecker ────────────────────────────────────────────────────


def test_metadata_fields_all_required_present(tmp_path, validate_skills):
    # Create sibling so related-skills reference resolves
    (tmp_path / "other-skill").mkdir()
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "ref.md").write_text("# Ref\n")
    fm = (
        "name: test-skill\n"
        "description: Does things. Use when needed.\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        "  domain: backend\n"
        "  triggers: test, example\n"
        "  role: specialist\n"
        "  scope: implementation\n"
        "  output-format: code\n"
        "  related-skills: other-skill\n"
    )
    (skill_dir / "SKILL.md").write_text(f"---\n{fm}---\n# Body\n")
    issues = validate_skills.MetadataFieldsChecker().check(skill_dir, "test-skill")
    assert issues == []


def test_metadata_fields_missing_triggers(make_skill_dir, validate_skills):
    fm = (
        "name: test-skill\n"
        "description: Does things. Use when needed.\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        "  domain: backend\n"
        # no triggers
        "  role: specialist\n"
        "  scope: implementation\n"
        "  output-format: code\n"
        '  related-skills: ""\n'
    )
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.MetadataFieldsChecker().check(skill_dir, "test-skill")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert any("triggers" in i.message for i in errors)


def test_metadata_fields_no_metadata_key(make_skill_dir, validate_skills):
    fm = "name: test-skill\ndescription: Does things. Use when needed.\nlicense: MIT\n"
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.MetadataFieldsChecker().check(skill_dir, "test-skill")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert any("metadata" in i.message.lower() for i in errors)


def test_metadata_fields_metadata_not_dict(make_skill_dir, validate_skills):
    fm = "name: test-skill\ndescription: Does things. Use when needed.\nlicense: MIT\nmetadata: not-a-dict\n"
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.MetadataFieldsChecker().check(skill_dir, "test-skill")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert any("mapping" in i.message for i in errors)


def test_metadata_fields_empty_triggers(make_skill_dir, validate_skills):
    fm = (
        "name: test-skill\n"
        "description: Does things. Use when needed.\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        "  domain: backend\n"
        '  triggers: ""\n'
        "  role: specialist\n"
        "  scope: implementation\n"
        "  output-format: code\n"
        '  related-skills: ""\n'
    )
    skill_dir = make_skill_dir(frontmatter=fm)
    issues = validate_skills.MetadataFieldsChecker().check(skill_dir, "test-skill")
    errors = [i for i in issues if i.severity == validate_skills.Severity.ERROR]
    assert any("triggers" in i.message for i in errors)


# ─── LineCountChecker ─────────────────────────────────────────────────────────


def test_line_count_at_minimum(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(body=_body_with_lines(80))
    assert validate_skills.LineCountChecker().check(skill_dir, "test-skill") == []


def test_line_count_at_maximum(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(body=_body_with_lines(100))
    assert validate_skills.LineCountChecker().check(skill_dir, "test-skill") == []


def test_line_count_below_minimum(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(body=_body_with_lines(79))
    issues = validate_skills.LineCountChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "79" in issues[0].message


def test_line_count_above_maximum(make_skill_dir, validate_skills):
    skill_dir = make_skill_dir(body=_body_with_lines(101))
    issues = validate_skills.LineCountChecker().check(skill_dir, "test-skill")
    assert len(issues) == 1
    assert issues[0].severity == validate_skills.Severity.WARNING
    assert "101" in issues[0].message


def test_line_count_blank_lines_not_counted(make_skill_dir, validate_skills):
    # 85 non-blank lines plus many blank lines → still valid
    blank_section = "\n" * 50
    content_section = _body_with_lines(85)
    skill_dir = make_skill_dir(body=blank_section + content_section)
    assert validate_skills.LineCountChecker().check(skill_dir, "test-skill") == []


# ─── simple_yaml_parse ────────────────────────────────────────────────────────


def test_simple_yaml_parse_scalar_values(validate_skills):
    result = validate_skills.simple_yaml_parse("name: foo\ndescription: bar")
    assert result == {"name": "foo", "description": "bar"}


def test_simple_yaml_parse_quoted_value(validate_skills):
    result = validate_skills.simple_yaml_parse('version: "1.0.0"')
    assert result == {"version": "1.0.0"}


def test_simple_yaml_parse_list_value(validate_skills):
    result = validate_skills.simple_yaml_parse("items:\n  - alpha\n  - beta")
    assert result == {"items": ["alpha", "beta"]}


def test_simple_yaml_parse_nested_dict(validate_skills):
    result = validate_skills.simple_yaml_parse("metadata:\n  triggers: foo\n  role: bar")
    assert result == {"metadata": {"triggers": "foo", "role": "bar"}}


def test_simple_yaml_parse_empty_string(validate_skills):
    assert validate_skills.simple_yaml_parse("") == {}
