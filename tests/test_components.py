"""Tests for list_shifter_components tool (real mGear API)."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


class TestGetComponentTypes:
    """Test _get_component_types helper (uses getComponentDirectories API)."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        list_shifter_components_module: ModuleType,
        install_mgear: dict,
    ) -> None:
        self.mod = list_shifter_components_module

    def test_no_mgear(self) -> None:
        saved = {}
        for name in list(sys.modules.keys()):
            if "mgear" in name:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod._get_component_types()
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["count"] == 0
        assert result["types"] == []

    def test_with_mgear(self) -> None:
        result = self.mod._get_component_types()
        assert result["count"] > 0
        assert "arm" in result["types"]
        assert "leg" in result["types"]
        assert "spine" in result["types"]


class TestGetSceneGuides:
    """Test _get_scene_guides helper (uses isGearGuide/ismodel/comp_type)."""

    @pytest.fixture(autouse=True)
    def _setup(self, list_shifter_components_module: ModuleType) -> None:
        self.mod = list_shifter_components_module

    def test_no_maya(self) -> None:
        with patch("builtins.__import__", side_effect=ImportError("maya.cmds not found")):
            result = self.mod._get_scene_guides()
        assert result == []

    def test_finds_guides_by_isGearGuide(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["spine_guide"]

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr == "isGearGuide"

        install_maya.cmds.attributeQuery = _attr_query
        install_maya.cmds.getAttr.return_value = True
        result = self.mod._get_scene_guides()
        assert len(result) > 0
        assert result[0]["name"] == "spine_guide"

    def test_finds_guides_by_ismodel(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["model_root"]

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr == "ismodel"

        install_maya.cmds.attributeQuery = _attr_query
        result = self.mod._get_scene_guides()
        assert len(result) > 0
        assert result[0]["name"] == "model_root"

    def test_finds_guides_by_comp_type(self, install_maya: MagicMock) -> None:
        install_maya.cmds.ls.return_value = ["arm_L0_root"]

        def _attr_query(attr, node=None, exists=False, **kw):
            return attr == "comp_type"

        install_maya.cmds.attributeQuery = _attr_query
        result = self.mod._get_scene_guides()
        assert len(result) > 0
        assert result[0]["name"] == "arm_L0_root"


class TestListShifterComponents:
    """Test list_shifter_components entry point."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        list_shifter_components_module: ModuleType,
        install_mgear: dict,
    ) -> None:
        self.mod = list_shifter_components_module

    def test_no_mgear_no_maya(self) -> None:
        saved = {}
        for name in list(sys.modules.keys()):
            if "mgear" in name:
                saved[name] = sys.modules.pop(name)
        try:
            with patch("builtins.__import__", side_effect=ImportError("not found")):
                result = self.mod.list_shifter_components()
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is True
        assert result["context"]["component_types"]["count"] == 0

    def test_filter_by_valid_type(self) -> None:
        result = self.mod.list_shifter_components(component_type="spine", include_guides=False)
        assert result["success"] is True
        assert "filtered_component" in result["context"]
        assert result["context"]["filtered_component"]["name"] == "spine"

    def test_filter_by_invalid_type(self) -> None:
        result = self.mod.list_shifter_components(component_type="nonexistent")
        assert result["success"] is False
        assert "Unknown component type" in result["message"]

    def test_include_guides_false(self) -> None:
        result = self.mod.list_shifter_components(include_guides=False)
        assert result["success"] is True
        assert "guides" not in result["context"]
