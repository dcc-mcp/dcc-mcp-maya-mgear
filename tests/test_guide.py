"""Tests for create_shifter_guide_from_template tool."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


class TestValidateTemplate:
    """Test _validate_template helper."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        create_shifter_guide_from_template_module: ModuleType,
        install_mgear: dict,
    ) -> None:
        self.mod = create_shifter_guide_from_template_module

    def test_no_mgear(self) -> None:
        # Remove mgear from sys.modules
        saved = {}
        for name in ("mgear", "mgear.shifter", "mgear.shifter.component", "mgear.shifter.rig"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)
        try:
            result = self.mod._validate_template("spine")
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod
        assert result is None

    def test_valid_template(self) -> None:
        result = self.mod._validate_template("spine")
        assert result is None

    def test_invalid_template(self) -> None:
        result = self.mod._validate_template("invalid_template")
        assert result is not None
        assert "Unknown template" in result


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
        for name in ("mgear", "mgear.shifter", "mgear.shifter.component", "mgear.shifter.rig"):
            if name in sys.modules:
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

    def test_no_maya_returns_error(self) -> None:
        # Remove maya but keep mgear
        saved_maya = {}
        for name in ("maya", "maya.cmds"):
            if name in sys.modules:
                saved_maya[name] = sys.modules.pop(name)
        try:
            result = self.mod.create_shifter_guide_from_template(
                guide_name="test_guide",
                template="spine",
            )
        finally:
            for name, mod in saved_maya.items():
                sys.modules[name] = mod
        assert result["success"] is False
        assert "Maya is not available" in result["message"]

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
        assert "test_guide" in result["message"]

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
