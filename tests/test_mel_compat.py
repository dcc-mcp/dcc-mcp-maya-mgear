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
