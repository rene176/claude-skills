# ─── replace_marker ───────────────────────────────────────────────────────────


def test_replace_marker_basic(update_docs):
    content = "<!-- FOO -->42<!-- /FOO -->"
    assert update_docs.replace_marker(content, "FOO", "99") == "<!-- FOO -->99<!-- /FOO -->"


def test_replace_marker_multiline_content(update_docs):
    content = "<!-- FOO -->\n42\n<!-- /FOO -->"
    assert update_docs.replace_marker(content, "FOO", "99") == "<!-- FOO -->99<!-- /FOO -->"


def test_replace_marker_no_match_unchanged(update_docs):
    content = "No markers here"
    assert update_docs.replace_marker(content, "FOO", "99") == content


def test_replace_marker_preserves_surroundings(update_docs):
    content = "before<!-- FOO -->42<!-- /FOO -->after"
    assert update_docs.replace_marker(content, "FOO", "99") == "before<!-- FOO -->99<!-- /FOO -->after"


def test_replace_marker_spaces_in_tags(update_docs):
    content = "<!--  FOO  -->42<!--  /FOO  -->"
    assert update_docs.replace_marker(content, "FOO", "99") == "<!--  FOO  -->99<!--  /FOO  -->"


# ─── count_skills ─────────────────────────────────────────────────────────────


def test_count_skills_empty_dir(update_docs, tmp_path):
    (tmp_path / "skills").mkdir()
    assert update_docs.count_skills(tmp_path) == 0


def test_count_skills_nonexistent_dir(update_docs, tmp_path):
    assert update_docs.count_skills(tmp_path) == 0


def test_count_skills_counts_only_dirs_with_skill_md(update_docs, tmp_path):
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "has-skill").mkdir()
    (skills / "has-skill" / "SKILL.md").write_text("# Skill\n")
    (skills / "no-skill").mkdir()  # no SKILL.md
    assert update_docs.count_skills(tmp_path) == 1


def test_count_skills_three_valid(update_docs, tmp_path):
    skills = tmp_path / "skills"
    skills.mkdir()
    for name in ("skill-a", "skill-b", "skill-c"):
        (skills / name).mkdir()
        (skills / name / "SKILL.md").write_text("# Skill\n")
    assert update_docs.count_skills(tmp_path) == 3


def test_count_skills_ignores_top_level_skill_md(update_docs, tmp_path):
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "SKILL.md").write_text("# Not a skill dir\n")  # file, not inside a subdir
    assert update_docs.count_skills(tmp_path) == 0


# ─── count_references ─────────────────────────────────────────────────────────


def test_count_references_zero(update_docs, tmp_path):
    (tmp_path / "skills").mkdir()
    assert update_docs.count_references(tmp_path) == 0


def test_count_references_counts_md_files(update_docs, tmp_path):
    refs = tmp_path / "skills" / "foo" / "references"
    refs.mkdir(parents=True)
    (refs / "a.md").write_text("# A\n")
    (refs / "b.md").write_text("# B\n")
    assert update_docs.count_references(tmp_path) == 2


def test_count_references_across_multiple_skills(update_docs, tmp_path):
    for name in ("foo", "bar"):
        refs = tmp_path / "skills" / name / "references"
        refs.mkdir(parents=True)
        (refs / "ref.md").write_text("# Ref\n")
    assert update_docs.count_references(tmp_path) == 2


def test_count_references_ignores_non_md(update_docs, tmp_path):
    refs = tmp_path / "skills" / "foo" / "references"
    refs.mkdir(parents=True)
    (refs / "data.txt").write_text("not markdown")
    assert update_docs.count_references(tmp_path) == 0


# ─── count_workflows ──────────────────────────────────────────────────────────


def test_count_workflows_nonexistent(update_docs, tmp_path):
    assert update_docs.count_workflows(tmp_path) == 0


def test_count_workflows_counts_md_files(update_docs, tmp_path):
    cmd = tmp_path / "commands" / "project"
    cmd.mkdir(parents=True)
    (cmd / "workflow-a.md").write_text("# Workflow A\n")
    (cmd / "workflow-b.md").write_text("# Workflow B\n")
    assert update_docs.count_workflows(tmp_path) == 2


def test_count_workflows_recursive(update_docs, tmp_path):
    sub = tmp_path / "commands" / "project" / "subdir"
    sub.mkdir(parents=True)
    (sub / "nested.md").write_text("# Nested\n")
    assert update_docs.count_workflows(tmp_path) == 1


def test_count_workflows_ignores_yaml(update_docs, tmp_path):
    cmd = tmp_path / "commands" / "project"
    cmd.mkdir(parents=True)
    (cmd / "workflow.yaml").write_text("command: foo\n")
    assert update_docs.count_workflows(tmp_path) == 0
