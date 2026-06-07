"""Package-level tests — ensure the package is importable and coverage tracks it."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_ROOT = Path(__file__).parent.parent / "skill" / "maya-mgear" / "scripts"

_COUNTER = [0]


def _load_tool(script_name: str):
    """Load a skill script by name from the scripts directory."""
    _COUNTER[0] += 1
    script_path = SCRIPTS_ROOT / "{}.py".format(script_name)
    module_name = "pkg_test_mgear_{}_{}".format(script_name, _COUNTER[0])
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _clear_mgear():
    for key in list(sys.modules.keys()):
        if key.startswith("mgear"):
            del sys.modules[key]


# ---------------------------------------------------------------------------
# Package-level tests (coverage-gated — these import the real package)
# ---------------------------------------------------------------------------


class TestPackageImport:
    """Verify the dcc_mcp_maya_mgear package top-level."""

    def test_package_import(self):
        import dcc_mcp_maya_mgear

        assert dcc_mcp_maya_mgear is not None

    def test_package_init_defines_package(self):
        import dcc_mcp_maya_mgear

        assert dcc_mcp_maya_mgear.__name__ == "dcc_mcp_maya_mgear"

    def test_scripts_directory_exists(self):
        assert SCRIPTS_ROOT.is_dir()

    def test_all_five_tool_scripts_exist(self):
        for name in (
            "inspect_mgear_environment",
            "list_shifter_components",
            "create_shifter_guide_from_template",
            "build_shifter_rig",
            "export_shifter_guide_template",
        ):
            assert (SCRIPTS_ROOT / "{}.py".format(name)).is_file()


# ---------------------------------------------------------------------------
# mGear unavailable — all 5 tools
# ---------------------------------------------------------------------------


class TestMgearUnavailablePath:
    """Verify all 5 tools degrade gracefully when mgear is completely absent."""

    TOOLS = [
        ("inspect_mgear_environment", "inspect_mgear_environment", {}),
        ("list_shifter_components", "list_shifter_components", {}),
        (
            "create_shifter_guide_from_template",
            "create_shifter_guide_from_template",
            {"guide_name": "t", "template": "arm_2jnt_01"},
        ),
        ("build_shifter_rig", "build_shifter_rig", {}),
        ("export_shifter_guide_template", "export_shifter_guide_template", {"guide_name": "t"}),
    ]

    @pytest.mark.parametrize("tool_module,entry_point,kwargs", TOOLS)
    def test_tool_returns_error_when_mgear_completely_missing(self, tool_module, entry_point, kwargs):
        """Every tool returns success=False when mgear cannot be imported."""
        _clear_mgear()
        mod = _load_tool(tool_module)
        result = getattr(mod, entry_point)(**kwargs)
        assert result["success"] is False
        assert "message" in result
        assert result["error"] is not None

    @pytest.mark.parametrize("tool_module,entry_point,kwargs", TOOLS)
    def test_tool_result_has_required_keys_when_unavailable(self, tool_module, entry_point, kwargs):
        """Every tool returns all 5 required keys even when mgear is missing."""
        _clear_mgear()
        mod = _load_tool(tool_module)
        result = getattr(mod, entry_point)(**kwargs)
        required = {"success", "message", "prompt", "error", "context"}
        for key in required:
            assert key in result, "Tool {} missing key '{}'".format(tool_module, key)
        assert isinstance(result["context"], dict)


# ---------------------------------------------------------------------------
# Partial mGear availability edge cases
# ---------------------------------------------------------------------------


class TestPartialMgearAvailability:
    """Tools must handle partial mgear states safely.

    These tests inject mocks into sys.modules BEFORE loading the tool module
    so the tool's top-level imports resolve against our mocks.  The tool's
    own try/except blocks then decide the outcome.
    """

    def test_list_components_handles_broken_getComponentDirectories(self):
        """list_shifter_components must catch RuntimeError from getComponentDirectories()."""
        _clear_mgear()

        mock_mgear = MagicMock()
        mock_mgear.__path__ = ["/mock/mgear"]
        mock_shifter = SimpleNamespace()
        mock_shifter.getComponentDirectories = MagicMock(side_effect=RuntimeError("broken API"))
        mock_mgear.shifter = mock_shifter

        with patch.dict(sys.modules, {"mgear": mock_mgear, "mgear.shifter": mock_shifter}):
            mod = _load_tool("list_shifter_components")
            result = mod.list_shifter_components()
            assert isinstance(result, dict)
            assert result["success"] is False

    def test_create_guide_handles_draw_comp_exception(self):
        """create_shifter_guide_from_template must catch exception from draw_comp()."""
        _clear_mgear()

        mock_mgear = MagicMock()
        mock_mgear.__path__ = ["/mock/mgear"]
        mock_shifter = SimpleNamespace()
        mock_guide_mgr = SimpleNamespace()
        mock_guide_mgr.draw_comp = MagicMock(side_effect=RuntimeError("draw failed"))
        mock_shifter.guide_manager = mock_guide_mgr
        mock_mgear.shifter = mock_shifter

        with patch.dict(sys.modules, {"mgear": mock_mgear, "mgear.shifter": mock_shifter}):
            mod = _load_tool("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(guide_name="t", template="arm_2jnt_01")
            assert isinstance(result, dict)
            assert result["success"] is False

    def test_build_rig_handles_build_from_selection_exception(self):
        """build_shifter_rig must catch exception from build_from_selection()."""
        _clear_mgear()

        mock_mgear = MagicMock()
        mock_mgear.__path__ = ["/mock/mgear"]
        mock_shifter = SimpleNamespace()
        mock_guide_mgr = SimpleNamespace()
        mock_guide_mgr.build_from_selection = MagicMock(side_effect=RuntimeError("build failed"))
        mock_shifter.guide_manager = mock_guide_mgr
        mock_mgear.shifter = mock_shifter

        # Also mock maya.cmds.select for the pre-selection step
        mock_maya_cmds = MagicMock()
        mock_maya_cmds.select = MagicMock(return_value=None)
        mock_maya = MagicMock()
        mock_maya.cmds = mock_maya_cmds

        modules = {
            "mgear": mock_mgear,
            "mgear.shifter": mock_shifter,
            "maya": mock_maya,
            "maya.cmds": mock_maya_cmds,
        }
        with patch.dict(sys.modules, modules):
            mod = _load_tool("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="test_guide")
            assert isinstance(result, dict)
            assert result["success"] is False

    def test_export_template_handles_io_exception(self):
        """export_shifter_guide_template must catch exception from export_guide_template()."""
        _clear_mgear()

        mock_mgear = MagicMock()
        mock_mgear.__path__ = ["/mock/mgear"]
        mock_shifter = SimpleNamespace()
        mock_io = SimpleNamespace()
        mock_io.export_guide_template = MagicMock(side_effect=RuntimeError("export failed"))
        mock_shifter.io = mock_io
        mock_mgear.shifter = mock_shifter

        # Also mock maya.cmds.select for the pre-selection step
        mock_maya_cmds = MagicMock()
        mock_maya_cmds.select = MagicMock(return_value=None)
        mock_maya = MagicMock()
        mock_maya.cmds = mock_maya_cmds

        modules = {
            "mgear": mock_mgear,
            "mgear.shifter": mock_shifter,
            "maya": mock_maya,
            "maya.cmds": mock_maya_cmds,
        }
        with patch.dict(sys.modules, modules):
            mod = _load_tool("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="t")
            assert isinstance(result, dict)
            assert result["success"] is False


# ---------------------------------------------------------------------------
# main() entry point exact signature contract
# ---------------------------------------------------------------------------


class TestMainEntryPoints:
    """Every tool's main() must accept **kwargs and return a dict."""

    TOOL_NAMES = [
        "inspect_mgear_environment",
        "list_shifter_components",
        "create_shifter_guide_from_template",
        "build_shifter_rig",
        "export_shifter_guide_template",
    ]

    @pytest.mark.parametrize("tool_name", TOOL_NAMES)
    def test_main_is_callable_with_no_args(self, tool_name):
        mod = _load_tool(tool_name)
        # main() wraps the real function with **kwargs — no-arg call should work.
        # Tools that require args will return skill_error, not raise TypeError.
        result = mod.main()
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.parametrize("tool_name", TOOL_NAMES)
    def test_main_accepts_extra_kwargs(self, tool_name):
        mod = _load_tool(tool_name)
        result = mod.main(extra_unexpected_kwarg="value")
        assert isinstance(result, dict)
        assert "success" in result
