"""Tests for ``export_shifter_rig`` — the rig-export leg of the mGear tool surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
from conftest import (
    FakeScene,
    hide_maya,
    load_script,
    make_maya,
    make_mgear,
)

import pytest as _pytest


@pytest.fixture
def script() -> Any:
    return load_script("export_shifter_rig")


def _ctx(result: Dict[str, Any]) -> Dict[str, Any]:
    return result.get("context") or {}


# ---------------------------------------------------------------------------
# FBX export
# ---------------------------------------------------------------------------


def test_export_fbx_reads_back_bytes_and_metrics(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)
    make_mgear(monkeypatch)
    target = tmp_path / "nested" / "biped.fbx"

    result = script.export_shifter_rig(str(target))

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["file_path"] == str(target).replace("\\", "/")
    assert ctx["file_format"] == "fbx"
    assert ctx["file_size_bytes"] == target.stat().st_size > 0
    assert ctx["file_size_human"].endswith("KB")
    assert ctx["rig_roots"] == ["|biped_rig"]
    assert ctx["detection_method"] == "attribute:is_rig"
    assert ctx["joint_count"] == 2
    assert ctx["control_count"] == 2
    assert ctx["mesh_count"] == 1
    assert ctx["keyframe_count"] == 240
    assert ctx["start_frame"] == 1
    assert ctx["end_frame"] == 120
    assert ctx["frame_range_source"] == "timeline"
    # The keyframe query must walk the hierarchy, otherwise an animated rig
    # reports zero keys.
    assert biped_scene.keyframe_calls[0]["hierarchy"] == "below"
    assert ctx["mgear"]["available"] is True
    assert ctx["mgear"]["version"] == "5.2.1"


def test_export_fbx_uses_explicit_objects_when_given(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    cmds, _mel = make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(
        str(tmp_path / "explicit.fbx"), objects=["|biped_rig|body_ctl"]
    )

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["detection_method"] == "explicit_objects"
    assert ctx["rig_roots"] == ["|biped_rig|body_ctl"]
    # FBX exports the selection, so the roots must be selected first.
    assert biped_scene.select_calls and biped_scene.select_calls[0][0] == (
        ["|biped_rig|body_ctl"],
    )
    assert cmds.AbcExport.call_count == 0  # FBX path must not touch AbcExport


def test_export_fbx_explicit_rig_root_wins_over_detection(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(
        str(tmp_path / "root.fbx"), rig_root="|biped_rig"
    )

    assert result["success"] is True, result
    assert _ctx(result)["detection_method"] == "explicit_rig_root"


def test_export_fbx_honours_explicit_frame_range_and_bake(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    _cmds, mel = make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(
        str(tmp_path / "range.fbx"),
        start_frame=10,
        end_frame=48,
        bake_animation=False,
    )

    assert result["success"] is True, result
    assert _ctx(result)["start_frame"] == 10
    assert _ctx(result)["end_frame"] == 48
    assert _ctx(result)["frame_range_source"] == "explicit"
    commands = [c[0][0] for c in mel.eval.call_args_list]
    assert "FBXExportBakeComplexAnimation -v 0;" in commands
    assert "FBXExportBakeComplexStart -v 10;" in commands
    assert "FBXExportBakeComplexEnd -v 48;" in commands
    assert any(c.startswith("FBXExport -f") for c in commands)


def test_export_appends_missing_extension(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(str(tmp_path / "noext"))

    assert result["success"] is True, result
    assert _ctx(result)["file_path"].endswith("noext.fbx")
    assert (tmp_path / "noext.fbx").is_file()


# ---------------------------------------------------------------------------
# Alembic export
# ---------------------------------------------------------------------------


def test_export_infers_abc_from_extension(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    cmds, _mel = make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(str(tmp_path / "inferred.abc"))

    assert result["success"] is True, result
    assert _ctx(result)["file_format"] == "abc"
    assert cmds.AbcExport.call_count == 1


def test_export_explicit_format_replaces_other_supported_extension(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)
    target = tmp_path / "switched.abc"

    result = script.export_shifter_rig(str(target), file_format="fbx")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["file_format"] == "fbx"
    assert ctx["file_path"].endswith("switched.fbx")
    assert (tmp_path / "switched.fbx").is_file()
    assert not target.exists()


def test_export_abc_builds_job_string(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    cmds, mel = make_maya(monkeypatch, biped_scene)
    target = tmp_path / "biped.abc"

    result = script.export_shifter_rig(str(target), file_format="abc")

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["file_format"] == "abc"
    assert ctx["file_size_bytes"] == target.stat().st_size > 0
    job = cmds.AbcExport.call_args[1]["j"]
    target_posix = str(target).replace("\\", "/")
    assert "-frameRange 1 120" in job
    # The job string is split on whitespace, so both values must be quoted.
    assert '-root "|biped_rig"' in job
    assert '-file "{}"'.format(target_posix) in job
    # Alembic takes the roots explicitly; it must not depend on the selection.
    assert not any(c[0][0].startswith("FBXExport -f") for c in mel.eval.call_args_list)


def test_export_abc_quotes_paths_with_spaces(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    cmds, _mel = make_maya(monkeypatch, biped_scene)
    spaced = tmp_path / "My Rig" / "biped.abc"

    result = script.export_shifter_rig(str(spaced), file_format="abc")

    assert result["success"] is True, result
    job = cmds.AbcExport.call_args[1]["j"]
    # Splitting the job on whitespace must still yield the whole path.
    assert '-file "{}"'.format(str(spaced).replace("\\", "/")) in job
    assert (tmp_path / "My Rig" / "biped.abc").is_file()


def test_export_keyframe_count_handles_scalar_and_list(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    cmds, _mel = make_maya(monkeypatch, biped_scene)
    target = tmp_path / "keys.fbx"

    # Maya returns a scalar for one target and a list for several.
    for raw, expected in ((240, 240), ([120, 120], 240), (None, 0)):
        monkeypatch.setattr(cmds, "keyframe", lambda *_a, **_k: raw)
        result = script.export_shifter_rig(str(target))
        assert result["success"] is True, result
        assert _ctx(result)["keyframe_count"] == expected, (
            raw,
            _ctx(result)["keyframe_count"],
        )


def test_export_restores_the_artists_selection(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    scene = FakeScene(
        nodes={
            "|biped_rig": "transform",
            "|biped_rig|root_Jnt": "joint",
            "|thing_i_had_selected": "transform",
        },
        attrs={"|biped_rig": ("is_rig",)},
        selection=["|thing_i_had_selected"],
    )
    make_maya(monkeypatch, scene)

    result = script.export_shifter_rig(str(tmp_path / "sel.fbx"))

    assert result["success"] is True, result
    assert scene.selection == ["|thing_i_had_selected"]
    assert _ctx(result)["selection_restored"] is True


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------


def test_export_without_maya_returns_error(
    script: Any, monkeypatch: _pytest.MonkeyPatch, tmp_path: Path
) -> None:
    hide_maya(monkeypatch)

    result = script.export_shifter_rig(str(tmp_path / "x.fbx"))

    assert result["success"] is False
    assert "Maya not available" == result["message"]


def test_export_empty_file_path_returns_error(
    script: Any, monkeypatch: _pytest.MonkeyPatch, biped_scene: FakeScene
) -> None:
    make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig("   ")

    assert result["success"] is False
    assert result["error"] == "missing_file_path"


def test_export_unsupported_format_returns_error(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(str(tmp_path / "rig.obj"), file_format="obj")

    assert result["success"] is False
    assert result["error"] == "unsupported_format"
    assert _ctx(result)["supported_formats"] == ["abc", "fbx"]


def test_export_unknown_rig_root_returns_error(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene)

    result = script.export_shifter_rig(str(tmp_path / "x.fbx"), rig_root="ghost_rig")

    assert result["success"] is False
    assert result["error"] == "rig_root_not_resolved"
    assert "ghost_rig" in result["message"]
    assert _ctx(result)["detection_method"] == "explicit_rig_root"


def test_export_without_any_rig_root_returns_error(
    script: Any, monkeypatch: _pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = FakeScene(nodes={"|persp": "transform"})
    make_maya(monkeypatch, empty)

    result = script.export_shifter_rig(str(tmp_path / "x.fbx"))

    assert result["success"] is False
    assert result["message"] == "No rig root found in the scene"


def test_export_empty_file_is_a_failure(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene, write_on_fbx=False)

    result = script.export_shifter_rig(str(tmp_path / "empty.fbx"))

    assert result["success"] is False
    ctx = _ctx(result)
    assert result["error"] == "empty_export"
    assert ctx["file_exists"] is False
    assert ctx["file_size_bytes"] == 0


def test_export_rejects_a_stale_file_from_a_previous_run(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    """A file left by an earlier export must not satisfy the read-back.

    MEL reports exporter errors without raising, so without this guard a
    silently failed run would return success with the previous file's size.
    """
    make_maya(monkeypatch, biped_scene, write_on_fbx=False)
    target = tmp_path / "stale.fbx"
    target.write_bytes(b"previous export")

    result = script.export_shifter_rig(str(target))

    assert result["success"] is False
    ctx = _ctx(result)
    assert result["error"] == "empty_export"
    # The stale file must have been deleted, not read back as evidence.
    assert ctx["file_exists"] is False
    assert not target.exists()


def test_export_succeeds_when_the_stale_file_is_replaced(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    make_maya(monkeypatch, biped_scene, fbx_bytes=b"fresh export")
    target = tmp_path / "stale.fbx"
    target.write_bytes(b"previous export")

    result = script.export_shifter_rig(str(target))

    assert result["success"] is True, result
    assert target.read_bytes() == b"fresh export"
    assert _ctx(result)["file_size_bytes"] == len(b"fresh export")


def test_export_reports_advisory_mgear_context_when_absent(
    script: Any,
    monkeypatch: _pytest.MonkeyPatch,
    biped_scene: FakeScene,
    tmp_path: Path,
) -> None:
    from conftest import hide_mgear

    make_maya(monkeypatch, biped_scene)
    hide_mgear(monkeypatch)

    result = script.export_shifter_rig(str(tmp_path / "nomgear.fbx"))

    assert result["success"] is True, result
    assert _ctx(result)["mgear"] == {"available": False}


def test_export_falls_back_to_selection(
    script: Any, monkeypatch: _pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scene = FakeScene(
        nodes={
            "|sel_rig": "transform",
            "|sel_rig|spine_Jnt": "joint",
        },
        selection=["|sel_rig"],
    )
    make_maya(monkeypatch, scene)

    result = script.export_shifter_rig(str(tmp_path / "sel.fbx"))

    assert result["success"] is True, result
    assert _ctx(result)["detection_method"] == "selection"


def test_export_falls_back_to_name_heuristic(
    script: Any, monkeypatch: _pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scene = FakeScene(
        nodes={
            "|hero_rig": "transform",
            "|hero_rig|root_Jnt": "joint",
            "|persp": "transform",
        }
    )
    make_maya(monkeypatch, scene)

    result = script.export_shifter_rig(str(tmp_path / "heuristic.fbx"))

    assert result["success"] is True, result
    ctx = _ctx(result)
    assert ctx["detection_method"] == "name_heuristic"
    assert ctx["rig_roots"] == ["|hero_rig"]
