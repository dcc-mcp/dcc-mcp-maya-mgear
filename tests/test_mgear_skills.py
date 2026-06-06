"""Unit tests for mGear Shifter skill tools."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
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


def _make_mock_module():
    """Create a MagicMock with __path__ and __spec__ set for Python import system compatibility."""
    mock = MagicMock()
    mock.__path__ = ["/mock/pkg"]
    mock.__spec__ = None
    return mock


def _make_mock_modules(**submodules):
    """Build a sys.modules patch dict with mgear + mgear.shifter + submodules.

    Submodule keys are mapped to ``mgear.shifter.<name>`` (e.g. ``component``
    becomes ``mgear.shifter.component``) matching the Python import chain
    ``import mgear.shifter.component``.
    """
    mock_mgear = _make_mock_module()
    mock_mgear.__path__ = ["/mock/mgear"]
    mock_mgear.__version__ = "4.0.0"

    mock_shifter = _make_mock_module()
    mock_shifter.__path__ = ["/mock/mgear/shifter"]

    modules = {"mgear": mock_mgear, "mgear.shifter": mock_shifter}
    for name, mock in submodules.items():
        full_name = "mgear.shifter.{}".format(name)
        mock.__path__ = ["/mock/mgear/shifter/{}".format(name)]
        mock.__spec__ = None
        modules[full_name] = mock
        # Wire to parent so attribute access works
        setattr(mock_shifter, name, mock)

    return modules


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
            # Ensure shifter import fails
            with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "mgear" else None):
                mod = _load_script("inspect_mgear_environment")
                result = mod.inspect_mgear_environment()
                # mgear found but shifter not available -> still success
                assert result["success"] is True
                ctx = result.get("context", {})
                assert ctx.get("shifter_available") is False


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

    def test_with_mock_shifter(self):
        mock_comp = MagicMock()
        mock_comp.getComponentList = MagicMock(return_value=["arm_2jnt_01", "leg_2jnt_01", "spine_ik_01"])
        mock_modules = _make_mock_modules(component=mock_comp)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False)
            assert result["success"] is True
            ctx = result.get("context", {})
            assert "components" in ctx
            assert "total_components" in ctx

    def test_filter_by_component_type(self):
        mock_comp = MagicMock()
        mock_comp.getComponentList = MagicMock(return_value=["arm_2jnt_01", "leg_2jnt_01", "spine_ik_01"])
        mock_modules = _make_mock_modules(component=mock_comp)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False, component_type="arm")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert "components" in ctx


class TestCreateShifterGuideFromTemplate:
    """Tests for create_shifter_guide_from_template tool."""

    def test_graceful_degradation_when_mgear_missing(self):
        mod = _load_script("create_shifter_guide_from_template")
        result = mod.create_shifter_guide_from_template(guide_name="test_guide", template="arm")
        assert result["success"] is False
        assert "not available" in result["message"].lower()

    def test_main_entry_point(self):
        mod = _load_script("create_shifter_guide_from_template")
        result = mod.main(guide_name="test", template="spine")
        assert isinstance(result, dict)
        assert "success" in result

    def test_required_parameters(self):
        mod = _load_script("create_shifter_guide_from_template")
        with pytest.raises(TypeError):
            mod.create_shifter_guide_from_template()

    def test_with_mock_guide_creation(self):
        mock_manager = MagicMock()
        mock_manager.return_value.createGuide = MagicMock(return_value="guide1")
        mock_guide = MagicMock()
        mock_guide.GuideManager = mock_manager
        mock_modules = _make_mock_modules(guide=mock_guide)
        mock_modules["mgear.shifter"].guide = mock_guide

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(
                guide_name="my_guide",
                template="arm",
                position=[0.0, 10.0, 0.0],
                parent_guide="root_guide",
                parameters={"side": "L"},
            )
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_name") == "my_guide"
            assert ctx.get("template") == "arm"
            assert "node" in ctx


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
        # Invalid build_type should error before even trying mgear
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

    def test_with_mock_rig_build(self):
        mock_rigger = MagicMock()
        mock_rigger.return_value.build = MagicMock(return_value=["rig_result"])
        mock_rig = MagicMock()
        mock_rig.Rigger = mock_rigger
        mock_modules = _make_mock_modules(rig=mock_rig)
        mock_modules["mgear.shifter"].rig = mock_rig

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "my_guide"

    def test_build_all_guides(self):
        mock_rigger = MagicMock()
        mock_rigger.return_value.buildAll = MagicMock(return_value=["rig1", "rig2"])
        mock_rig = MagicMock()
        mock_rig.Rigger = mock_rigger
        mock_modules = _make_mock_modules(rig=mock_rig)
        mock_modules["mgear.shifter"].rig = mock_rig

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig()
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "all"


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

    def test_with_mock_export_base64(self):
        mock_manager = MagicMock()
        mock_manager.return_value.exportTemplate = MagicMock(return_value=b"template_data")
        mock_template = MagicMock()
        mock_template.TemplateManager = mock_manager
        mock_modules = _make_mock_modules(template=mock_template)
        mock_modules["mgear.shifter"].template = mock_template

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert "template_base64" in ctx

    def test_with_mock_export_to_file(self, tmp_path):
        output = tmp_path / "exported_template.json"
        mock_manager = MagicMock()
        mock_manager.return_value.exportTemplate = MagicMock(return_value='{"template": "data"}')
        mock_template = MagicMock()
        mock_template.TemplateManager = mock_manager
        mock_modules = _make_mock_modules(template=mock_template)
        mock_modules["mgear.shifter"].template = mock_template

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

    def test_no_metadata_export(self):
        mock_manager = MagicMock()
        mock_manager.return_value.exportTemplate = MagicMock(return_value=b"data")
        mock_template = MagicMock()
        mock_template.TemplateManager = mock_manager
        mock_modules = _make_mock_modules(template=mock_template)
        mock_modules["mgear.shifter"].template = mock_template

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide", include_metadata=False)
            assert result["success"] is True


class TestResultDictConformance:
    """Verify all tools return proper ToolResult dicts."""

    TOOLS = [
        ("inspect_mgear_environment", {}),
        ("list_shifter_components", {}),
        ("create_shifter_guide_from_template", {"guide_name": "t", "template": "arm"}),
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
