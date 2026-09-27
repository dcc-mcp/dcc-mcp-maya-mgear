"""Tests for ``build_shifter_rig`` — the build must report verifiable counts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
from conftest import (
    FakeScene,
    load_script,
    make_maya,
    make_mgear,
)


@pytest.fixture
def script() -> Any:
    return load_script("build_shifter_rig")


def _ctx(result: Dict[str, Any]) -> Dict[str, Any]:
    return result.get("context") or {}


def test_build_reports_joint_and_control_counts(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.guide_manager.build_from_selection.return_value = ["|biped_rig"]
    make_maya(
        monkeypatch,
        FakeScene(
            nodes={
                "|biped_guide": "transform",
                "|biped_rig": "transform",
                "|biped_rig|root_Jnt": "joint",
                "|biped_rig|spine_Jnt": "joint",
                "|biped_rig|body_ctl": "transform",
                "|biped_rig|body_ctl|body_ctlShape": "nurbsCurve",
            }
        ),
    )

    result = script.build_shifter_rig("biped_guide")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["built_guides"] == ["|biped_rig"]
    assert ctx["joint_count"] == 2
    assert ctx["control_count"] == 1
    assert ctx["transform_count"] == 2
    assert ctx["metrics_scope"] == "rig"
    assert "2 joint(s), 1 control(s)" in result["message"]


def test_build_counts_scene_when_mgear_returns_nothing(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.guide_manager.build_from_selection.return_value = None
    make_maya(
        monkeypatch,
        FakeScene(nodes={"|a_Jnt": "joint", "|b_Jnt": "joint"}),
    )

    result = script.build_shifter_rig()

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["built_guides"] == []
    assert ctx["metrics_scope"] == "scene"
    assert ctx["joint_count"] == 2


def test_build_without_metrics_when_maya_missing(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.guide_manager.build_from_selection.return_value = ["|biped_rig"]
    monkeypatch.setitem(__import__("sys").modules, "maya", None)

    result = script.build_shifter_rig()

    assert result["success"] is True, result
    assert _ctx(result)["metrics_scope"] == "unavailable"
    assert result["message"] == "Built 1 guide(s)"


def test_build_unknown_guide_returns_error(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_mgear(monkeypatch)
    make_maya(monkeypatch, FakeScene(nodes={"|persp": "transform"}))

    result = script.build_shifter_rig("does_not_exist")

    assert result["success"] is False
    assert "does_not_exist" in result["message"]


def test_build_without_mgear_returns_error(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(__import__("sys").modules, "mgear", None)
    monkeypatch.setitem(__import__("sys").modules, "mgear.shifter", None)

    result = script.build_shifter_rig()

    assert result["success"] is False
    assert result["message"] == "mGear Shifter is not available"


def test_build_entry_point_delegates(
    script: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.guide_manager.build_from_selection.return_value = ["|rig"]
    make_maya(
        monkeypatch, FakeScene(nodes={"|guide1": "transform", "|rig": "transform"})
    )

    result = script.main(guide_name="guide1")

    assert result["success"] is True, result
    assert _ctx(result)["joint_count"] == 0
