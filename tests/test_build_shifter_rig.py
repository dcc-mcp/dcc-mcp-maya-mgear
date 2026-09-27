"""Tests for ``build_shifter_rig`` — the build must report verifiable counts.

The rig root is resolved from the built rig, not from a return value:
upstream ``mgear.shifter.guide_manager.build_from_selection()`` has no
``return``, and ``Rig.buildFromSelection()`` only returns ``build_data`` when
the ``data_collector`` option is enabled.  Both contracts are pinned here so
the tool cannot regress to scene-wide counts being reported as rig counts.
"""

from __future__ import annotations

import sys
from typing import Any, Dict

import pytest
from conftest import FakeScene, hide_mgear, load_script, make_maya, make_mgear


@pytest.fixture
def script() -> Any:
    return load_script("build_shifter_rig")


def _ctx(result: Dict[str, Any]) -> Dict[str, Any]:
    return result.get("context") or {}


def _rig_scene() -> FakeScene:
    return FakeScene(
        nodes={
            "|biped_guide": "transform",
            "|biped_rig": "transform",
            "|biped_rig|root_Jnt": "joint",
            "|biped_rig|spine_Jnt": "joint",
            "|biped_rig|body_ctl": "transform",
            "|biped_rig|body_ctl|body_ctlShape": "nurbsCurve",
            "|stray_Jnt": "joint",  # not part of the rig
        },
        attrs={"|biped_rig": ("is_rig",)},
    )


def test_build_reads_rig_root_from_rig_model(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    # Real contract: buildFromSelection() returns build_data only with the
    # data_collector option; a normal build returns None.
    mgear.shifter.Rig.return_value.buildFromSelection.return_value = None
    mgear.shifter.Rig.return_value.model = "biped_rig"
    make_maya(monkeypatch, _rig_scene())

    result = script.build_shifter_rig("biped_guide")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["rig_roots"] == ["|biped_rig"]
    assert ctx["rig_root_source"] == "rig.model"
    assert ctx["build_method"] == "shifter.Rig.buildFromSelection"
    assert ctx["metrics_scope"] == "rig"
    # Only what is under the rig root — the stray joint is excluded.
    assert ctx["joint_count"] == 2
    assert ctx["control_count"] == 1
    assert ctx["transform_count"] == 2
    assert "2 joint(s), 1 control(s)" in result["message"]


def test_build_falls_back_to_is_rig_query_on_legacy_mgear(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mGear without ``shifter.Rig``: build_from_selection() returns None.

    This is the contract that broke the first implementation — the return
    value is always ``None``, so the root has to come from the scene.
    """
    shifter = make_mgear(monkeypatch).shifter
    guide_manager = shifter.guide_manager
    guide_manager.build_from_selection.return_value = None
    shifter.Rig = None  # older mGear: no Rig class on mgear.shifter
    make_maya(monkeypatch, _rig_scene())

    result = script.build_shifter_rig("biped_guide")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert guide_manager.build_from_selection.called
    assert ctx["build_method"] == "shifter.guide_manager.build_from_selection"
    assert ctx["rig_roots"] == ["|biped_rig"]
    assert ctx["rig_root_source"] == "attribute:is_rig"
    assert ctx["metrics_scope"] == "rig"
    assert ctx["joint_count"] == 2


def test_build_reports_scene_scope_when_root_unresolved(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.Rig.return_value.model = None
    make_maya(
        monkeypatch,
        FakeScene(nodes={"|guide1": "transform", "|a_Jnt": "joint"}),
    )

    result = script.build_shifter_rig("guide1")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["rig_roots"] == []
    assert ctx["metrics_scope"] == "scene"
    # The message must not claim a rig was located.
    assert "rig root could not be resolved" in result["message"]


def test_build_without_metrics_when_maya_missing(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.Rig.return_value.model = "biped_rig"
    monkeypatch.setitem(sys.modules, "maya", None)

    result = script.build_shifter_rig()

    assert result["success"] is True, result
    assert _ctx(result)["metrics_scope"] == "unavailable"
    assert "counts unavailable" in result["message"]


def test_build_unknown_guide_returns_error(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.Rig.return_value.buildFromSelection.return_value = None
    make_maya(monkeypatch, FakeScene(nodes={"|persp": "transform"}))

    result = script.build_shifter_rig("does_not_exist")

    assert result["success"] is False
    assert result["error"] == "guide_not_found"
    assert "does_not_exist" in result["message"]
    # The build must not run at all when the guide is missing.
    assert mgear.shifter.Rig.return_value.buildFromSelection.call_count == 0


def test_build_without_mgear_returns_error(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    hide_mgear(monkeypatch)

    result = script.build_shifter_rig()

    assert result["success"] is False
    assert result["error"] == "mgear_shifter_unavailable"


def test_build_entry_point_delegates(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    mgear = make_mgear(monkeypatch)
    mgear.shifter.Rig.return_value.model = "rig1"
    make_maya(
        monkeypatch, FakeScene(nodes={"|guide1": "transform", "|rig1": "transform"})
    )

    result = script.main(guide_name="guide1")

    assert result["success"] is True, result
    assert _ctx(result)["joint_count"] == 0
