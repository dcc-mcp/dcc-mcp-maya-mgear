"""Tests for build_shifter_rig tool (real mGear API)."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


class TestGetGuideNodes:
    """Test _get_guide_nodes helper."""

    @pytest.fixture(autouse=True)
    def _setup(self, build_shifter_rig_module: ModuleType) -> None:
        self.mod = build_shifter_rig_module

    def test_no_maya(self) -> None:
        with pytest.raises(ImportError):
            self.mod._get_guide_nodes()

    def test_no_guides(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = []
        result = self.mod._get_guide_nodes()
        assert result == []

    def test_finds_guides_by_isGearGuide(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["spine_guide"]
        install_maya.cmds.attributeQuery.return_value = True
        result = self.mod._get_guide_nodes()
        assert "spine_guide" in result

    def test_finds_guides_by_ismodel(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["model_root"]

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr == "ismodel"

        install_maya.cmds.attributeQuery = MagicMock(side_effect=_attr_query)
        result = self.mod._get_guide_nodes()
        assert "model_root" in result

    def test_finds_guides_by_comp_type(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["arm_L0_root"]

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr == "comp_type"

        install_maya.cmds.attributeQuery = MagicMock(side_effect=_attr_query)
        result = self.mod._get_guide_nodes()
        assert "arm_L0_root" in result


class TestBuildShifterRig:
    """Test build_shifter_rig entry point."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        build_shifter_rig_module: ModuleType,
        install_maya_and_mgear: dict,
    ) -> None:
        self.mod = build_shifter_rig_module

    def test_no_maya_returns_error(self) -> None:
        saved = {}
        for name in ("maya", "maya.cmds"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod.build_shifter_rig()
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
            install_maya.cmds.ls.return_value = []
            result = self.mod.build_shifter_rig()
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "mGear is not available" in result["message"]

    def test_invalid_build_type(self) -> None:
        result = self.mod.build_shifter_rig(build_type="invalid")
        assert result["success"] is False
        assert "Invalid build_type" in result["message"]

    def test_no_guides_found(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = []
        result = self.mod.build_shifter_rig()
        assert result["success"] is False
        assert "No guides found" in result["message"]

    def test_guide_not_found_by_name(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = []
        result = self.mod.build_shifter_rig(guide_name="nonexistent_guide")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_successful_build_from_selection(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["spine_guide"]
        install_maya.cmds.attributeQuery.return_value = True
        result = self.mod.build_shifter_rig(build_type="preview")
        assert result["success"] is True

    def test_full_build_type(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["spine_guide"]
        install_maya.cmds.attributeQuery.return_value = True
        result = self.mod.build_shifter_rig(build_type="full")
        assert result["success"] is True
        assert result["context"]["build_type"] == "full"
