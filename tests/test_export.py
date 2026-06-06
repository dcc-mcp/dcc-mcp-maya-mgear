"""Tests for export_shifter_guide_template tool."""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from types import ModuleType
from unittest.mock import MagicMock

import pytest


class TestGetGuideExportData:
    """Test _get_guide_export_data helper."""

    @pytest.fixture(autouse=True)
    def _setup(self, export_shifter_guide_template_module: ModuleType) -> None:
        self.mod = export_shifter_guide_template_module

    def test_guide_not_found(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = False
        with pytest.raises(ValueError, match="does not exist"):
            self.mod._get_guide_export_data("nonexistent_guide")

    def test_export_existing_guide(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True
        install_maya.cmds.objectType.return_value = "transform"
        install_maya.cmds.listAttr.return_value = ["translate", "rotate", "scale"]
        install_maya.cmds.getAttr.return_value = 0.0
        install_maya.cmds.listRelatives.return_value = ["child_ctrl"]
        result = self.mod._get_guide_export_data("spine_guide")
        assert result["guide_name"] == "spine_guide"
        assert result["type"] == "transform"
        assert "attributes" in result
        assert "children" in result
        assert "child_ctrl" in result["children"]


class TestExportShifterGuideTemplate:
    """Test export_shifter_guide_template entry point."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        export_shifter_guide_template_module: ModuleType,
        install_maya_and_mgear: dict,
    ) -> None:
        self.mod = export_shifter_guide_template_module

    def test_no_maya_returns_error(self) -> None:
        saved = {}
        for name in ("maya", "maya.cmds"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod.export_shifter_guide_template(guide_name="test_guide")
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "Maya is not available" in result["message"]

    def test_no_mgear_returns_error(self, install_maya: MagicMock) -> None:
        saved = {}
        for name in ("mgear", "mgear.shifter", "mgear.shifter.component", "mgear.shifter.rig"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod.export_shifter_guide_template(guide_name="test_guide")
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "mGear is not available" in result["message"]

    def test_export_base64_mode(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True
        install_maya.cmds.objectType.return_value = "transform"
        install_maya.cmds.listAttr.return_value = ["translate"]
        install_maya.cmds.getAttr.return_value = 0.0
        install_maya.cmds.listRelatives.return_value = []
        install_maya.cmds.about.return_value = "2024.1"
        install_maya.cmds.file.return_value = "/tmp/test.ma"

        result = self.mod.export_shifter_guide_template(
            guide_name="spine_guide",
            include_metadata=False,
        )
        assert result["success"] is True
        assert "base64_content" in result["context"]
        assert result["context"]["encoding"] == "base64"

        decoded = base64.b64decode(result["context"]["base64_content"])
        data = json.loads(decoded)
        assert data["guide_name"] == "spine_guide"

    def test_export_to_file(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True
        install_maya.cmds.objectType.return_value = "transform"
        install_maya.cmds.listAttr.return_value = ["translate"]
        install_maya.cmds.getAttr.return_value = 0.0
        install_maya.cmds.listRelatives.return_value = []
        install_maya.cmds.about.return_value = "2024.1"
        install_maya.cmds.file.return_value = "/tmp/test.ma"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "spine_template.json")
            result = self.mod.export_shifter_guide_template(
                guide_name="spine_guide",
                output_path=output_path,
            )
            assert result["success"] is True
            assert result["context"]["output_path"] == output_path
            assert os.path.exists(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                content = json.loads(f.read())
            assert content["guide_name"] == "spine_guide"

    def test_guide_not_found_in_scene(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = False
        result = self.mod.export_shifter_guide_template(guide_name="nonexistent_guide")
        assert result["success"] is False
