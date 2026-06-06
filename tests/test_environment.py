"""Tests for inspect_mgear_environment tool."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


class TestModuleAvailability:
    """Test module detection helpers."""

    @pytest.fixture(autouse=True)
    def _setup(self, inspect_mgear_environment_module: ModuleType) -> None:
        self.mod = inspect_mgear_environment_module

    def test_module_available_true(self) -> None:
        assert self.mod._module_available("os") is True
        assert self.mod._module_available("sys") is True

    def test_module_available_false(self) -> None:
        assert self.mod._module_available("nonexistent_module_xyz123") is False

    def test_module_available_handles_exception(self) -> None:
        assert self.mod._module_available("") is False

    def test_get_module_version_known(self) -> None:
        version = self.mod._get_module_version("sys")
        assert version is not None
        assert isinstance(version, str)

    def test_get_module_version_none(self) -> None:
        assert self.mod._get_module_version("nonexistent_module_xyz123") is None

    def test_get_module_path_known(self) -> None:
        path = self.mod._get_module_path("os")
        assert path is not None
        assert isinstance(path, str)

    def test_get_module_path_none(self) -> None:
        assert self.mod._get_module_path("nonexistent_module_xyz123") is None


class TestInspectEnvironmentWithoutMGear:
    """Test inspect_mgear_environment when mGear is NOT installed."""

    @pytest.fixture(autouse=True)
    def _setup(self, inspect_mgear_environment_module: ModuleType) -> None:
        self.mod = inspect_mgear_environment_module

    def test_returns_success_when_mgear_missing(self, install_maya: MagicMock) -> None:
        """Should return success=True even when mGear is not available."""
        with patch("importlib.util.find_spec", return_value=None):
            result = self.mod.inspect_mgear_environment()
        assert result["success"] is True
        assert "not available" in result["message"].lower()
        assert result["context"]["mgear_available"] is False
        assert result["context"]["shifter_available"] is False

    def test_context_contains_python_version(self, install_maya: MagicMock) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            result = self.mod.inspect_mgear_environment()
        assert "python_version" in result["context"]

    def test_context_contains_maya_flag(self, install_maya: MagicMock) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            result = self.mod.inspect_mgear_environment()
        assert "maya_available" in result["context"]

    def test_verbose_mode_extra_info(self, install_maya: MagicMock) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            result = self.mod.inspect_mgear_environment(verbose=True)
        assert result["success"] is True


class TestInspectEnvironmentWithMockMGear:
    """Test inspect_mgear_environment with mocked mGear available."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        inspect_mgear_environment_module: ModuleType,
        install_maya_and_mgear: dict,
    ) -> None:
        self.mod = inspect_mgear_environment_module
        self.mods = install_maya_and_mgear

    def test_detects_mgear(self) -> None:
        def _find_spec(name, *args, **kwargs):
            if name and "mgear" in name:
                return MagicMock()
            return None

        with patch("importlib.util.find_spec", side_effect=_find_spec):
            result = self.mod.inspect_mgear_environment()
        assert result["success"] is True
        assert result["context"]["mgear_available"] is True
        assert result["context"]["shifter_available"] is True
        assert result["context"]["version"] == "4.2.0"

    def test_verbose_with_mgear(self) -> None:
        def _find_spec(name, *args, **kwargs):
            if name and "mgear" in name:
                return MagicMock()
            return None

        with patch("importlib.util.find_spec", side_effect=_find_spec):
            result = self.mod.inspect_mgear_environment(verbose=True)
        assert result["success"] is True

    def test_component_count(self) -> None:
        def _find_spec(name, *args, **kwargs):
            if name and "mgear" in name:
                return MagicMock()
            return None

        with patch("importlib.util.find_spec", side_effect=_find_spec):
            result = self.mod.inspect_mgear_environment()
        assert result["context"]["components_count"] == 26  # mock has 26 known types
        assert "component_types" in result["context"]
        assert "spine" in result["context"]["component_types"]


class TestGetMGearComponents:
    """Test _get_mgear_components helper directly."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        inspect_mgear_environment_module: ModuleType,
        install_maya_and_mgear: dict,
    ) -> None:
        self.mod = inspect_mgear_environment_module
        self.mods = install_maya_and_mgear

    def test_no_mgear(self) -> None:
        # Remove mgear from sys.modules to simulate missing
        saved = {}
        for name in ("mgear", "mgear.shifter", "mgear.shifter.component", "mgear.shifter.rig"):
            if name in sys.modules:
                saved[name] = sys.modules.pop(name)

        try:
            with patch("importlib.util.find_spec", return_value=None):
                result = self.mod._get_mgear_components()
        finally:
            for name, mod in saved.items():
                sys.modules[name] = mod

        assert result["mgear_available"] is False
        assert result["shifter_available"] is False
        assert result["components_count"] == 0

    def test_with_mgear(self) -> None:
        def _find_spec(name, *args, **kwargs):
            if name and "mgear" in name:
                return MagicMock()
            return None

        with patch("importlib.util.find_spec", side_effect=_find_spec):
            result = self.mod._get_mgear_components()
        assert result["mgear_available"] is True
        assert result["shifter_available"] is True
        assert result["components_count"] == 26  # mock has 26 known types
