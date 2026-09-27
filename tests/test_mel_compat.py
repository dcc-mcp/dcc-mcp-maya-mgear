"""Maya's FBX MEL surface is version-dependent; the importer must survive it."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def script() -> Any:
    path = (
        Path(__file__).resolve().parent.parent
        / "skill"
        / "mgear-import-to-scene"
        / "scripts"
        / "import_to_scene.py"
    )
    spec = importlib.util.spec_from_file_location("verify_import_script", str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_import_script"] = module
    spec.loader.exec_module(module)
    return module


class MissingProcedure(RuntimeError):
    """Raised by Maya when a MEL procedure does not exist."""


def _mel(missing: str = "FBXImportMaterials"):
    class _Mel:
        def __init__(self) -> None:
            self.calls: list = []

        def eval(self, command: str) -> str:
            self.calls.append(command)
            if missing and missing in command:
                # Maya 2026: "找不到过程“FBXImportMaterials”。"
                raise MissingProcedure(
                    "Error: line 1: 找不到过程“{}”。".format(missing)
                )
            return ""

    return _Mel()


def test_missing_fbx_material_proc_is_skipped(script: Any) -> None:
    mel = _mel()

    assert script._try_mel(mel, "FBXImportMaterials -v true") is None
    assert "FBXImportMaterials -v true" in mel.calls


def test_available_mel_commands_still_run(script: Any) -> None:
    mel = _mel(missing="")

    assert script._try_mel(mel, "FBXImportMode -v add") == ""
    assert "FBXImportMode -v add" in mel.calls


def test_unrelated_mel_errors_still_raise(script: Any) -> None:
    class _BrokenMel:
        def eval(self, command: str) -> str:
            raise RuntimeError("Error: wrong number of arguments")

    with pytest.raises(RuntimeError):
        script._try_mel(_BrokenMel(), "FBXImportMaterials -v true")


def test_error_merely_mentioning_the_procedure_still_raises(script: Any) -> None:
    """P2-a regression: name-only matching swallowed real errors.

    "FBXImportMaterials: invalid flag" mentions the procedure but is not a
    missing-procedure error; swallowing it would leave the setting unapplied
    while the import continued.
    """

    class _FlagErrorMel:
        def eval(self, command: str) -> str:
            raise RuntimeError("FBXImportMaterials: invalid flag")

    with pytest.raises(RuntimeError):
        script._try_mel(_FlagErrorMel(), "FBXImportMaterials -v true")


@pytest.mark.parametrize(
    "message",
    [
        "line 1: 找不到过程“FBXImportMaterials”。",
        'Cannot find procedure "FBXImportMaterials".',
        "No such procedure FBXImportMaterials",
        "FBXImportMaterials is not a procedure",
    ],
)
def test_missing_procedure_is_skipped_in_every_locale(
    script: Any, message: str
) -> None:
    class _MissingMel:
        def __init__(self) -> None:
            self.msg = message

        def eval(self, command: str) -> str:
            raise RuntimeError(self.msg)

    assert script._try_mel(_MissingMel(), "FBXImportMaterials -v true") is None


def test_other_commands_are_never_skipped(script: Any) -> None:
    """A missing-procedure message must not excuse a different command."""

    class _MissingMel:
        def eval(self, command: str) -> str:
            raise RuntimeError('Cannot find procedure "FBXImportMaterials".')

    with pytest.raises(RuntimeError):
        script._try_mel(_MissingMel(), "FBXImportMode -v add")


def test_skip_mode_leaves_preexisting_materials_alone(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2-b: material_mode='skip' must only strip this import's materials.

    On Maya 2026 the FBX material MEL procedure no longer aborts the import,
    so the scene-wide delete in this branch became reachable and would wipe
    materials that existed before the import.
    """
    import conftest

    scene = conftest.FakeScene(
        nodes={"|imported": "transform", "|existing": "transform"}
    )
    cmds, _mel = conftest.make_maya(monkeypatch, scene)

    # The pre-existing material is reachable from |existing only.
    def _list_connections(node, type=None, **_kw):
        if type != "shadingEngine":
            return []
        return ["oldSG"] if str(node) == "|existing" else ["newSG"]

    monkeypatch.setattr(cmds, "listConnections", _list_connections)
    monkeypatch.setattr(cmds, "ls", lambda *a, **k: ["oldSG", "newSG", "lambert1"])
    deleted = []
    monkeypatch.setattr(cmds, "delete", lambda n: deleted.append(str(n)))

    warnings = script._apply_material_mode(cmds, "skip", ["|imported"])

    assert "oldSG" not in deleted, "pre-existing shading engine was deleted"
    assert "newSG" in deleted
    assert warnings == []


def test_skip_mode_leaves_unconnected_preexisting_materials(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A material with no shading engine predates the import — leave it.

    Found on a real Maya 2026 host: an early version deleted "any material
    without connections", which claimed unconnected pre-existing materials.
    """
    import conftest

    scene = conftest.FakeScene(nodes={"|imported": "transform"})
    cmds, _mel = conftest.make_maya(monkeypatch, scene)

    monkeypatch.setattr(
        cmds,
        "listConnections",
        lambda node, type=None, **_kw: (
            ["newSG"] if str(node) == "|imported" and type == "shadingEngine" else []
        ),
    )
    monkeypatch.setattr(cmds, "ls", lambda *a, **k: ["orphanMat", "lambert1"])
    deleted = []
    monkeypatch.setattr(cmds, "delete", lambda n: deleted.append(str(n)))

    script._strip_materials_from_nodes(cmds, ["|imported"])

    assert "orphanMat" not in deleted


def test_skip_mode_without_imported_nodes_refuses_to_strip(
    script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No imported nodes means no way to scope the delete — do not guess."""
    import conftest

    cmds, _mel = conftest.make_maya(
        monkeypatch, conftest.FakeScene(nodes={"|existing": "transform"})
    )
    deleted = []
    cmds.delete = lambda n: deleted.append(str(n))

    warnings = script._apply_material_mode(cmds, "skip", [])

    assert deleted == []
    assert warnings
    assert "Skipped material removal" in warnings[0].message
