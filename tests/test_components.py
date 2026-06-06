"""Tests for list_shifter_components tool."""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest


class TestGetComponentTypes:
    """Test _get_component_types helper."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        list_shifter_components_module: ModuleType,
        mock_mgear_modules: dict,
    ) -> None:
        self.mod = list_shifter_components_module
        self.mock_mgear = mock_mgear_modules

    def test_no_mgear(self) -> None:
        with patch("builtins.__import__", side_effect=ImportError("mgear not found")):
            result = self.mod._get_component_types()
        assert result["count"] == 0
        assert result["types"] == []

    def test_with_mgear(self, install_mgear: dict) -> None:
        result = self.mod._get_component_types()
        assert result["count"] == 5
        assert "spine" in result["types"]
        assert "arm" in result["types"]
        assert "leg" in result["types"]


class TestGetSceneGuides:
    """Test _get_scene_guides helper."""

    @pytest.fixture(autouse=True)
    def _setup(self, list_shifter_components_module: ModuleType) -> None:
        self.mod = list_shifter_components_module

    def test_no_maya(self) -> None:
        with patch("builtins.__import__", side_effect=ImportError("maya.cmds not found")):
            result = self.mod._get_scene_guides()
        assert result == []


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
        with patch("builtins.__import__", side_effect=ImportError("not found")):
            result = self.mod.list_shifter_components()
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
