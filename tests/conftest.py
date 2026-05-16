import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture(scope="session")
def validate_markdown():
    return _load_module("validate_markdown", "validate-markdown.py")


@pytest.fixture(scope="session")
def validate_skills():
    return _load_module("validate_skills", "validate-skills.py")


@pytest.fixture(scope="session")
def update_docs():
    return _load_module("update_docs", "update-docs.py")


def _default_frontmatter(skill_name: str = "test-skill") -> str:
    return (
        f"name: {skill_name}\n"
        "description: Does useful things. Use when you need testing.\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: https://github.com/test\n"
        '  version: "1.0.0"\n'
        "  domain: backend\n"
        "  triggers: test, example\n"
        "  role: specialist\n"
        "  scope: implementation\n"
        "  output-format: code\n"
        '  related-skills: ""\n'
    )


def _default_body() -> str:
    header = (
        "\n"
        "## Role Definition\n"
        "\n"
        "You are a test skill for testing purposes.\n"
        "\n"
        "## When to Use This Skill\n"
        "\n"
        "- When you need to test something\n"
        "- When you want to verify behavior\n"
        "\n"
        "## Core Workflow\n"
        "\n"
        "1. Step one\n"
        "2. Step two\n"
        "3. Step three\n"
        "4. Step four\n"
        "5. Step five\n"
        "\n"
    )
    # 11 non-blank lines in header; add 74 filler lines to reach 85 total
    filler = "".join(f"- Filler line {i}\n" for i in range(74))
    return header + filler


@pytest.fixture
def make_skill_dir(tmp_path):
    def _factory(
        skill_name: str = "test-skill",
        frontmatter: str | None = None,
        body: str | None = None,
        include_references: bool = True,
    ) -> Path:
        skill_dir = tmp_path / skill_name
        skill_dir.mkdir()
        fm = frontmatter if frontmatter is not None else _default_frontmatter(skill_name)
        bd = body if body is not None else _default_body()
        (skill_dir / "SKILL.md").write_text(f"---\n{fm}---\n{bd}")
        if include_references:
            refs = skill_dir / "references"
            refs.mkdir()
            (refs / "reference.md").write_text("# Reference\nContent.\n")
        return skill_dir

    return _factory
