"""Tests for the sample-template lookup against the real mGear layout."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture
def script() -> Any:
    path = (
        Path(__file__).resolve().parent.parent
        / "skill"
        / "maya-mgear"
        / "scripts"
        / "import_shifter_sample_template.py"
    )
    spec = importlib.util.spec_from_file_location("verify_template_script", str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_template_script"] = module
    spec.loader.exec_module(module)
    return module


def _make_mgear(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, layout: str
) -> ModuleType:
    """Build a fake ``mgear.shifter`` package holding one .sgt at *layout*.

    Uses pytest's ``tmp_path`` so the tree is owned (and cleaned up) by pytest
    rather than an orphaned ``mkdtemp`` directory.
    """
    root = str(tmp_path)
    templates = os.path.join(root, "mgear", "shifter", layout)
    os.makedirs(templates)
    Path(templates, "biped.sgt").write_bytes(b'{"guide": true}')

    mgear = ModuleType("mgear")
    mgear.__path__ = [os.path.join(root, "mgear")]  # type: ignore[attr-defined]
    shifter = ModuleType("mgear.shifter")
    shifter.__path__ = [os.path.join(root, "mgear", "shifter")]  # type: ignore[attr-defined]
    mgear.shifter = shifter  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mgear", mgear)
    monkeypatch.setitem(sys.modules, "mgear.shifter", shifter)
    return shifter


@pytest.mark.parametrize(
    "layout",
    [
        os.path.join("component", "_templates"),
        "guide_templates",
    ],
)
def test_finds_templates_in_both_layouts(
    script: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, layout: str
) -> None:
    _make_mgear(monkeypatch, tmp_path, layout)

    found = script._find_template_path("biped.sgt")

    assert found is not None
    assert os.path.isfile(found)
    assert found.replace("\\", "/").endswith("biped.sgt")


def test_finds_template_when_extension_is_omitted(
    script: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _make_mgear(monkeypatch, tmp_path, os.path.join("component", "_templates"))

    assert script._find_template_path("biped") is not None


def test_returns_none_for_a_missing_template(
    script: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _make_mgear(monkeypatch, tmp_path, os.path.join("component", "_templates"))

    assert script._find_template_path("nope.sgt") is None


def test_resolves_the_guide_root_from_the_scene(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Upstream import_guide_template() returns None, so the root is looked up.

    get_guide() is not usable either: it returns an attribute name
    ("guide.ismodel"), the same ls("*.attr") trap as the rig-root lookups.
    """
    import conftest

    scene = conftest.FakeScene(
        nodes={"|guide": "transform", "|guide|arm": "transform"},
        attrs={"|guide": ("ismodel",)},
    )
    cmds, _mel = conftest.make_maya(monkeypatch, scene)

    assert script._find_guide_root() == "|guide"
    assert cmds.attributeQuery("ismodel", node="|guide", exists=True) is True


def test_returns_none_when_no_guide_root_exists(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import conftest

    conftest.make_maya(monkeypatch, conftest.FakeScene(nodes={"|persp": "transform"}))

    assert script._find_guide_root() is None
