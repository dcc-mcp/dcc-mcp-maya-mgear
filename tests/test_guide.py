"""Tests for create_shifter_guide_from_template tool (real mGear API)."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


class TestValidateComponentType:
    """Test _validate_component_type helper."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        create_shifter_guide_from_template_module: ModuleType,
        install_mgear: dict,
    ) -> None:
        self.mod = create_shifter_guide_from_template_module

    def test_no_mgear(self) -> None:
        saved = {}
        for name in ("mgear", "mgear.shifter"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod._validate_component_type("spine")
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result is None

    def test_valid_component_type(self) -> None:
        result = self.mod._validate_component_type("arm")
        assert result is None

    def test_invalid_component_type(self) -> None:
        result = self.mod._validate_component_type("nonexistent_type")
        assert result is not None
        assert "Unknown component type" in result


class TestCreateShifterGuide:
    """Test create_shifter_guide_from_template entry point."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        create_shifter_guide_from_template_module: ModuleType,
        install_maya_and_mgear: dict,
    ) -> None:
        self.mod = create_shifter_guide_from_template_module

    def test_no_mgear_returns_error(self) -> None:
        saved = {}
        for name in list(sys.modules.keys()):
            if "mgear" in name:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod.create_shifter_guide_from_template(
                guide_name="test_guide",
                template="spine",
            )
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "mGear is not available" in result["message"]

    def test_invalid_position(self) -> None:
        result = self.mod.create_shifter_guide_from_template(
            guide_name="test_guide",
            template="spine",
            position=[1.0, 2.0],
        )
        assert result["success"] is False
        assert "Invalid position" in result["message"]

    def test_default_position(self) -> None:
        result = self.mod.create_shifter_guide_from_template(
            guide_name="test_guide",
            template="spine",
        )
        assert result["success"] is True
        assert "spine" in result["message"]

    def test_with_parent_guide(self) -> None:
        result = self.mod.create_shifter_guide_from_template(
            guide_name="test_guide",
            template="arm",
            position=[0.0, 10.0, 0.0],
            parent_guide="root_guide",
            parameters={"side": "left", "joints": 3},
        )
        assert result["success"] is True
        assert result["context"]["parent"] == "root_guide"

    def test_parent_not_found(self) -> None:
        """When parent doesn't exist, should return error with 'not found'."""
        # Get the mock maya.cmds from sys.modules (injected by install_maya_and_mgear)
        mock_cmds = sys.modules["maya.cmds"]
        mock_cmds.objExists.return_value = False
        result = self.mod.create_shifter_guide_from_template(
            guide_name="test_guide",
            template="spine",
            parent_guide="bad_parent",
        )
        assert result["success"] is False
        assert "not found" in str(result.get("message", "")).lower()

    def test_invalid_component_type(self) -> None:
        result = self.mod.create_shifter_guide_from_template(
            guide_name="test_guide",
            template="invalid_comp_type_123",
        )
        assert result["success"] is False
        assert "Invalid component type" in result["message"]
