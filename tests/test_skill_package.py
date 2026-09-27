"""Package-level guards: every declared tool has a script and vice versa."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skill" / "maya-mgear"


def _tool_names(skill_dir: Path) -> list:
    data = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))
    return [t["name"] for t in data.get("tools", [])]


def _script_names(skill_dir: Path) -> list:
    return sorted(
        p.stem
        for p in (skill_dir / "scripts").glob("*.py")
        if not p.stem.startswith("_")
    )


def _matches(tool_name: str, script_name: str) -> bool:
    """A tool matches its script by exact name or by a skill-name prefix.

    ``mgear-import-to-scene`` declares ``mgear_import_to_scene`` but ships
    ``import_to_scene.py``, so both spellings count as a match.
    """
    return tool_name == script_name or tool_name.endswith("_" + script_name)


@pytest.mark.parametrize(
    "skill_dir", sorted(p.parent for p in REPO_ROOT.glob("skill/*/SKILL.md"))
)
def test_every_tool_has_a_matching_script(skill_dir: Path) -> None:
    scripts = _script_names(skill_dir)
    for name in _tool_names(skill_dir):
        assert any(_matches(name, script) for script in scripts), (
            "{}: no script for tool '{}'".format(skill_dir.name, name)
        )


@pytest.mark.parametrize(
    "skill_dir", sorted(p.parent for p in REPO_ROOT.glob("skill/*/SKILL.md"))
)
def test_every_public_script_is_declared(skill_dir: Path) -> None:
    tools = _tool_names(skill_dir)
    for script in _script_names(skill_dir):
        assert any(_matches(tool, script) for tool in tools), (
            "{}: script '{}' is not declared in tools.yaml".format(
                skill_dir.name, script
            )
        )


def test_skill_frontmatter_stays_loadable() -> None:
    text = SKILL_ROOT.joinpath("SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md frontmatter not found"
    data = yaml.safe_load(match.group(1))
    assert data["name"] == "maya-mgear"
    assert "tools" in data["metadata"]["dcc-mcp"]
    assert "depends" in data["metadata"]["dcc-mcp"]


def test_export_tool_declares_required_file_path() -> None:
    data = yaml.safe_load((SKILL_ROOT / "tools.yaml").read_text(encoding="utf-8"))
    export_tool = next(t for t in data["tools"] if t["name"] == "export_shifter_rig")
    assert export_tool["input_schema"]["required"] == ["file_path"]
    assert set(export_tool["input_schema"]["properties"]["file_format"]["enum"]) == {
        "fbx",
        "abc",
    }
