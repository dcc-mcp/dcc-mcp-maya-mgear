"""Tests for export_shifter_guide_template tool (real mGear API)."""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from types import ModuleType
from unittest.mock import MagicMock

import pytest


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
        for name in list(sys.modules.keys()):
            if "mgear" in name:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod.export_shifter_guide_template(guide_name="test_guide")
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "mGear is not available" in result["message"]

    def test_guide_not_found(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = False
        result = self.mod.export_shifter_guide_template(guide_name="nonexistent_guide")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_not_valid_guide(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True

        def _attr_query(attr, node=None, exists=False, **kw):
            return False  # No guide attributes

        install_maya.cmds.attributeQuery = _attr_query
        result = self.mod.export_shifter_guide_template(guide_name="some_transform")
        assert result["success"] is False
        assert "Not a valid guide" in result["message"]

    def test_export_base64_mode(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True
        install_maya.cmds.ls.return_value = ["spine_guide"]
        install_maya.cmds.listAttr.return_value = ["isGearGuide", "comp_type"]
        install_maya.cmds.getAttr.return_value = "arm"

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr in ("isGearGuide", "ismodel", "comp_type")

        install_maya.cmds.attributeQuery = _attr_query

        result = self.mod.export_shifter_guide_template(
            guide_name="spine_guide",
            include_metadata=False,
        )
        assert result["success"] is True
        assert "base64_content" in result["context"]
        assert result["context"]["encoding"] == "base64"

        decoded = base64.b64decode(result["context"]["base64_content"])
        data = json.loads(decoded)
        assert "elements" in data

    def test_export_to_file(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr in ("isGearGuide", "ismodel", "comp_type")

        install_maya.cmds.attributeQuery = _attr_query

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "spine_template.json")
            result = self.mod.export_shifter_guide_template(
                guide_name="spine_guide",
                output_path=output_path,
            )
            assert result["success"] is True
            assert result["context"]["output_path"] == output_path
            assert os.path.exists(output_path)

    def test_export_sgt_format(self, install_maya: MagicMock) -> None:
        install_maya.cmds.objExists.return_value = True

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr in ("isGearGuide", "ismodel", "comp_type")

        install_maya.cmds.attributeQuery = _attr_query

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "spine_template.sgt")
            result = self.mod.export_shifter_guide_template(
                guide_name="spine_guide",
                output_path=output_path,
            )
            assert result["success"] is True
            assert result["context"]["format"] == "sgt"
