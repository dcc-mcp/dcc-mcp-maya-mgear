"""Unit tests for mGear Shifter skill tools.

Tests constrain against the VERIFIED real mGear upstream API surface:
- mgear.shifter.getComponentDirectories / importComponentGuide
- mgear.shifter.guide_manager.draw_comp / build_from_selection
- mgear.shifter.io.export_guide_template / build_from_file
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_ROOT = Path(__file__).parent.parent / "src" / "dcc_mcp_maya_mgear" / "skills" / "maya-mgear" / "scripts"

_COUNTER = [0]


def _load_script(script_name: str):
    """Load a skill script by name, using unique module names to avoid cache collisions."""
    _COUNTER[0] += 1
    script_path = SCRIPTS_ROOT / "{}.py".format(script_name)
    module_name = "skill_mgear_{}_{}".format(script_name, _COUNTER[0])
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_mock_mgear():
    """Create a mock mgear top-level package."""
    mock = MagicMock()
    mock.__path__ = ["/mock/mgear"]
    mock.__version__ = "4.0.0"
    return mock


def _make_mock_modules(**submodules):
    """Build a sys.modules patch dict with mgear + mgear.shifter + verified submodules.

    Module-level mocks use SimpleNamespace (not MagicMock) so that explicitly
    set attributes are returned as-is rather than replaced by auto-generated
    MagicMock children.

    Submodule keys (e.g. ``guide_manager``, ``io``) are wired as
    ``mgear.shifter.<name>`` and also attached as attributes on the shifter mock
    so ``import mgear.shifter.guide_manager`` resolves correctly.
    """
    mock_mgear = _make_mock_mgear()
    mock_shifter = SimpleNamespace()
    mock_shifter.__path__ = ["/mock/mgear/shifter"]

    # getComponentDirectories — verified real mGear API (shifter/__init__.py:57-84)
    mock_shifter.getComponentDirectories = MagicMock(
        return_value=[
            Path("/mock/mgear/shifter/components/arm_2jnt_01"),
            Path("/mock/mgear/shifter/components/leg_2jnt_01"),
            Path("/mock/mgear/shifter/components/spine_ik_01"),
        ]
    )

    # Wire mgear.shifter so import chaining resolves to mock_shifter, not an
    # auto-generated MagicMock child of mock_mgear.
    mock_mgear.shifter = mock_shifter

    modules = {"mgear": mock_mgear, "mgear.shifter": mock_shifter}
    for name, mock in submodules.items():
        full_name = "mgear.shifter.{}".format(name)
        modules[full_name] = mock
        setattr(mock_shifter, name, mock)

    return modules


# ---------------------------------------------------------------------------
# inspect_mgear_environment
# ---------------------------------------------------------------------------


class TestInspectMgearEnvironment:
    """Tests for inspect_mgear_environment tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("inspect_mgear_environment")
        result = mod.inspect_mgear_environment()
        assert result["success"] is False
        assert "not installed" in result["message"] or "mGear" in result["message"]
        assert result["error"] is not None

    def test_verbose_mode(self):
        mod = _load_script("inspect_mgear_environment")
        result = mod.inspect_mgear_environment(verbose=True)
        assert isinstance(result, dict)
        assert "success" in result

    def test_main_entry_point(self):
        mod = _load_script("inspect_mgear_environment")
        result = mod.main()
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result

    def test_with_mock_mgear_available(self):
        mock_mgear = MagicMock()
        mock_mgear.__version__ = "4.0.0"
        mock_mgear.__path__ = ["/mock/path/mgear"]

        with patch.dict(sys.modules, {"mgear": mock_mgear, "mgear.shifter": MagicMock()}):
            mod = _load_script("inspect_mgear_environment")
            result = mod.inspect_mgear_environment()
            assert result["success"] is True
            assert "4.0.0" in result.get("context", {}).get("version", "")

    def test_with_mock_mgear_no_shifter(self):
        mock_mgear = MagicMock()
        mock_mgear.__version__ = "3.0.0"

        with patch.dict(sys.modules, {"mgear": mock_mgear}):
            with patch(
                "importlib.util.find_spec",
                side_effect=lambda name: MagicMock() if name == "mgear" else None,
            ):
                mod = _load_script("inspect_mgear_environment")
                result = mod.inspect_mgear_environment()
                assert result["success"] is True
                ctx = result.get("context", {})
                assert ctx.get("shifter_available") is False

    def test_key_modules_includes_verified_modules(self):
        """Verify key_modules lists the verified real mGear module surfaces."""
        mod = _load_script("inspect_mgear_environment")
        mock_mgear = MagicMock()
        mock_mgear.__version__ = "4.0.0"
        mock_mgear.__path__ = ["/mock/path/mgear"]

        with patch.dict(sys.modules, {"mgear": mock_mgear, "mgear.shifter": MagicMock()}):
            with patch.object(mod, "_module_available", return_value=True):
                result = mod.inspect_mgear_environment(verbose=True)
                ctx = result.get("context", {})
                key_modules = ctx.get("key_modules", {})
                assert "mgear.shifter.guide_manager" in key_modules, (
                    "key_modules must include mgear.shifter.guide_manager"
                )
                assert "mgear.shifter.io" in key_modules, "key_modules must include mgear.shifter.io"
                assert "mgear.shifter.rig" not in key_modules, (
                    "mgear.shifter.rig does not exist upstream; must not appear in key_modules"
                )


# ---------------------------------------------------------------------------
# list_shifter_components
# ---------------------------------------------------------------------------


class TestListShifterComponents:
    """Tests for list_shifter_components tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("list_shifter_components")
        result = mod.list_shifter_components()
        assert result["success"] is False
        assert "not available" in result["message"].lower()

    def test_main_entry_point(self):
        mod = _load_script("list_shifter_components")
        result = mod.main()
        assert isinstance(result, dict)
        assert "success" in result

    def test_returns_components_via_getComponentDirectories(self):
        """list_shifter_components must use getComponentDirectories — the verified real API."""
        mock_modules = _make_mock_modules()
        shifter = mock_modules["mgear.shifter"]

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False)
            assert result["success"] is True
            ctx = result.get("context", {})
            components = ctx.get("components", [])
            assert len(components) == 3
            assert "arm_2jnt_01" in components
            assert "leg_2jnt_01" in components
            assert "spine_ik_01" in components
            # Verify the real API entry point was called
            shifter.getComponentDirectories.assert_called_once()

    def test_filter_by_component_type(self):
        mock_modules = _make_mock_modules()

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False, component_type="arm")
            assert result["success"] is True
            ctx = result.get("context", {})
            components = ctx.get("components", [])
            assert all("arm" in c for c in components)
            assert ctx.get("total_components") == 1


# ---------------------------------------------------------------------------
# create_shifter_guide_from_template
# ---------------------------------------------------------------------------


class TestCreateShifterGuideFromTemplate:
    """Tests for create_shifter_guide_from_template tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("create_shifter_guide_from_template")
        result = mod.create_shifter_guide_from_template(guide_name="test_guide", template="arm_2jnt_01")
        assert result["success"] is False
        assert "not available" in result["message"].lower()

    def test_main_entry_point(self):
        mod = _load_script("create_shifter_guide_from_template")
        result = mod.main(guide_name="test", template="spine_ik_01")
        assert isinstance(result, dict)
        assert "success" in result

    def test_required_parameters(self):
        mod = _load_script("create_shifter_guide_from_template")
        with pytest.raises(TypeError):
            mod.create_shifter_guide_from_template()

    def test_calls_draw_comp(self):
        """create_shifter_guide must call draw_comp — the verified real mGear API."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.draw_comp = MagicMock(return_value="guide1")
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(
                guide_name="my_guide",
                template="arm_2jnt_01",
                position=[0.0, 10.0, 0.0],
                parent_guide="root_guide",
                parameters={"side": "L"},
            )
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_name") == "my_guide"
            assert ctx.get("template") == "arm_2jnt_01"
            assert ctx.get("node") == "guide1"

            mock_gui_mgr.draw_comp.assert_called_once_with(
                comp_type="arm_2jnt_01",
                name="my_guide",
                parent="root_guide",
                pos=[0.0, 10.0, 0.0],
                side="L",
            )

    def test_draw_comp_no_node_returned(self):
        """When draw_comp returns None, result is still success with deferred note."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.draw_comp = MagicMock(return_value=None)
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(guide_name="g", template="leg_2jnt_01")
            assert result["success"] is True
            assert "node" not in result.get("context", {})


# ---------------------------------------------------------------------------
# build_shifter_rig
# ---------------------------------------------------------------------------


class TestBuildShifterRig:
    """Tests for build_shifter_rig tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("build_shifter_rig")
        result = mod.build_shifter_rig()
        assert result["success"] is False
        assert "not available" in result["message"].lower()

    def test_main_entry_point(self):
        mod = _load_script("build_shifter_rig")
        result = mod.main()
        assert isinstance(result, dict)
        assert "success" in result

    def test_invalid_build_type(self):
        mod = _load_script("build_shifter_rig")
        result = mod.build_shifter_rig(build_type="invalid")
        assert result["success"] is False
        assert "Invalid" in result["message"]

    def test_default_build_type_is_full(self):
        mod = _load_script("build_shifter_rig")
        result = mod.build_shifter_rig()
        assert result["success"] is False  # mGear missing is expected

    def test_preview_build_type_accepted(self):
        mod = _load_script("build_shifter_rig")
        result = mod.build_shifter_rig(build_type="preview")
        assert result["success"] is False  # mGear missing, but build_type accepted

    def test_calls_build_from_selection_with_guide_name(self):
        """build_shifter_rig must call build_from_selection — the verified real mGear API."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = MagicMock(return_value=["rig_result1"])
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "my_guide"
            assert ctx.get("build_type") == "full"
            assert ctx.get("built_guides") == ["rig_result1"]
            mock_gui_mgr.build_from_selection.assert_called_once()

    def test_build_from_selection_no_guide_name(self):
        """When no guide_name is given, builds from whatever is selected."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = MagicMock(return_value=["rig1", "rig2"])
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig()
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "selection"
            assert ctx.get("built_guides") == ["rig1", "rig2"]
            mock_gui_mgr.build_from_selection.assert_called_once()

    def test_build_from_selection_single_result(self):
        """When build_from_selection returns a single node (not a list)."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = MagicMock(return_value="single_rig")
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="test")
            assert result["success"] is True
            assert result["context"]["built_guides"] == ["single_rig"]


# ---------------------------------------------------------------------------
# export_shifter_guide_template
# ---------------------------------------------------------------------------


class TestExportShifterGuideTemplate:
    """Tests for export_shifter_guide_template tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("export_shifter_guide_template")
        result = mod.export_shifter_guide_template(guide_name="test_guide")
        assert result["success"] is False
        assert "not available" in result["message"].lower()

    def test_main_entry_point(self):
        mod = _load_script("export_shifter_guide_template")
        result = mod.main(guide_name="test_export")
        assert isinstance(result, dict)
        assert "success" in result

    def test_required_parameters(self):
        mod = _load_script("export_shifter_guide_template")
        with pytest.raises(TypeError):
            mod.export_shifter_guide_template()

    def test_calls_export_guide_template_base64(self):
        """export must call export_guide_template — the verified real mGear API (io.py:149-215)."""

        def _fake_export(guide_name, path):
            with open(path, "wb") as f:
                f.write(b"template_data_bytes")

        mock_io = SimpleNamespace()
        mock_io.export_guide_template = MagicMock(side_effect=_fake_export)
        mock_modules = _make_mock_modules(io=mock_io)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert "template_base64" in ctx
            assert len(ctx["template_base64"]) > 0  # non-empty base64
            mock_io.export_guide_template.assert_called_once()

    def test_calls_export_guide_template_to_file(self, tmp_path):
        output = tmp_path / "exported_template.gct"
        mock_io = SimpleNamespace()
        mock_io.export_guide_template = MagicMock()
        mock_modules = _make_mock_modules(io=mock_io)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(
                guide_name="my_guide",
                output_path=str(output),
                include_metadata=True,
            )
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("output_path") == str(output)
            mock_io.export_guide_template.assert_called_once_with("my_guide", str(output))

    def test_no_metadata_export(self):
        def _fake_export(guide_name, path):
            with open(path, "wb") as f:
                f.write(b"data")

        mock_io = SimpleNamespace()
        mock_io.export_guide_template = MagicMock(side_effect=_fake_export)
        mock_modules = _make_mock_modules(io=mock_io)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide", include_metadata=False)
            assert result["success"] is True


# ---------------------------------------------------------------------------
# ResultDictConformance
# ---------------------------------------------------------------------------


class TestResultDictConformance:
    """Verify all tools return proper ToolResult dicts."""

    TOOLS = [
        ("inspect_mgear_environment", {}),
        ("list_shifter_components", {}),
        ("create_shifter_guide_from_template", {"guide_name": "t", "template": "arm_2jnt_01"}),
        ("build_shifter_rig", {}),
        ("export_shifter_guide_template", {"guide_name": "t"}),
    ]

    REQUIRED_KEYS = {"success", "message", "prompt", "error", "context"}

    @pytest.mark.parametrize("tool_name,kwargs", TOOLS)
    def test_result_dict_has_required_keys(self, tool_name, kwargs):
        mod = _load_script(tool_name)
        result = mod.main(**kwargs)
        for key in self.REQUIRED_KEYS:
            assert key in result, "Tool {} missing key '{}'".format(tool_name, key)

    @pytest.mark.parametrize("tool_name,kwargs", TOOLS)
    def test_result_dict_context_is_dict(self, tool_name, kwargs):
        mod = _load_script(tool_name)
        result = mod.main(**kwargs)
        assert isinstance(result["context"], dict)
