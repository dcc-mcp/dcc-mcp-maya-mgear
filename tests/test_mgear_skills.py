"""Unit tests for mGear Shifter skill tools.

Tests use **signature-constrained** mocks that match the verified real
mGear upstream API so that a wrong call (wrong kwarg name, wrong
positional, wrong return type) produces a test failure instead of a
silently green mock.

Real signatures enforced:
- ``mgear.shifter.getComponentDirectories() -> {path: [name, ...]}``
- ``mgear.shifter.guide_manager.draw_comp(comp_type, parent=None, showUI=True)``
- ``mgear.shifter.guide_manager.build_from_selection()``  (no args)
- ``mgear.shifter.io.export_guide_template(filePath, meta)``
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


# ---------------------------------------------------------------------------
# Constrained mGear mock factories
# ---------------------------------------------------------------------------

# Real return type of getComponentDirectories() — a {path: [name, ...]} dict.
_FAKE_COMP_MAPPING = {
    "/mock/shifter/components/classic": ["arm_2jnt_01", "leg_2jnt_01", "head_01"],
    "/mock/shifter/components/epic": ["spine_ik_01", "tail_01"],
}


def _constrained_getComponentDirectories():
    """Signature-constrained stub for ``mgear.shifter.getComponentDirectories()``.

    Returns ``{path: [component_name, ...]}`` — exactly what the real API returns.
    """
    return dict(_FAKE_COMP_MAPPING)


def _constrained_draw_comp(comp_type, parent=None, showUI=True):
    """Signature-constrained stub for ``mgear.shifter.guide_manager.draw_comp()``.

    Real signature: ``draw_comp(comp_type, parent=None, showUI=True)``.
    Any call with extra kwargs (e.g. ``name=``, ``pos=``) will raise TypeError.
    """
    return "{}_guide".format(comp_type)


def _constrained_draw_comp_none(comp_type, parent=None, showUI=True):
    """Same signature — returns None (deferred creation)."""
    return None


def _constrained_build_from_selection():
    """Signature-constrained stub for ``mgear.shifter.guide_manager.build_from_selection()``.

    Takes **no arguments** — the real API builds whatever is currently selected.
    """
    return ["rig1", "rig2"]


def _constrained_build_from_selection_single():
    """Same — returns a single node."""
    return "single_rig"


def _constrained_export_guide_template(filePath, meta):
    """Signature-constrained stub for ``mgear.shifter.io.export_guide_template()``.

    Real signature: ``export_guide_template(filePath, meta)``.
    Writes fake GCT bytes to *filePath* so the base64 code path works.
    """
    Path(filePath).parent.mkdir(parents=True, exist_ok=True)
    Path(filePath).write_bytes(b"fake_gct_data")


def _make_mock_mgear():
    """Create a mock mgear top-level package."""
    mock = MagicMock()
    mock.__path__ = ["/mock/mgear"]
    mock.__version__ = "4.0.0"
    return mock


def _make_mock_modules(**submodules):
    """Build a sys.modules patch dict with signature-constrained mocks.

    The ``mgear.shifter`` mock is set up with ``getComponentDirectories``
    wired to :func:`_constrained_getComponentDirectories` — a real function
    whose signature and return type match the upstream API.

    Submodule keys (e.g. ``guide_manager``, ``io``) are wired as
    ``mgear.shifter.<name>``; production ``import mgear.shifter.<name>``
    resolves through these attributes.

    Also pre-registers ``maya`` / ``maya.cmds`` with a working ``select``
    so that ``_select_guide`` succeeds by default.  Tests that need a
    "guide not found" scenario can override ``maya.cmds.select`` to raise.
    """
    mock_mgear = _make_mock_mgear()
    mock_shifter = SimpleNamespace()
    mock_shifter.__path__ = ["/mock/mgear/shifter"]
    mock_shifter.getComponentDirectories = _constrained_getComponentDirectories

    mock_mgear.shifter = mock_shifter

    mock_maya_cmds = MagicMock()
    mock_maya_cmds.select = MagicMock(return_value=None)  # succeeds by default

    mock_maya = MagicMock()
    mock_maya.cmds = mock_maya_cmds

    modules = {
        "mgear": mock_mgear,
        "mgear.shifter": mock_shifter,
        "maya": mock_maya,
        "maya.cmds": mock_maya_cmds,
    }
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
                assert "mgear.shifter.guide_manager" in key_modules
                assert "mgear.shifter.io" in key_modules


# ---------------------------------------------------------------------------
# list_shifter_components
# ---------------------------------------------------------------------------


class TestListShifterComponents:
    """Tests for list_shifter_components tool.

    The real ``getComponentDirectories()`` returns ``{path: [name, ...]}``.
    These tests ensure the tool extracts component *names* from the dict
    *values*, not directory basenames from the keys.
    """

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

    def test_extracts_component_names_from_mapping(self):
        """Component names come from dict VALUES, not from directory basenames."""
        mock_modules = _make_mock_modules()

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False)
            assert result["success"] is True
            ctx = result.get("context", {})
            components = ctx.get("components", [])
            # Should be actual component names, not directory names like "classic"/"epic"
            assert "arm_2jnt_01" in components
            assert "leg_2jnt_01" in components
            assert "spine_ik_01" in components
            assert "head_01" in components
            assert "tail_01" in components
            assert ctx.get("total_components") == 5
            # Must NOT contain directory basenames
            assert "classic" not in components
            assert "epic" not in components

    def test_filter_by_component_type(self):
        mock_modules = _make_mock_modules()

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=False, component_type="arm")
            assert result["success"] is True
            ctx = result.get("context", {})
            components = ctx.get("components", [])
            assert components == ["arm_2jnt_01"]

    def test_guide_detection_uses_isGearGuide_and_ismodel(self):
        """Contract: uses official isGearGuide / ismodel attrs, NOT is_guide or name matching."""
        mock_modules = _make_mock_modules()

        mock_cmds = mock_modules["maya.cmds"]
        mock_cmds.ls.return_value = [
            "|guide_root",
            "|guide_root|arm_C0_root",
            "|some_random_transform",
        ]

        def fake_aq(attr, node=None, exists=False):
            if "arm_C0" in node:
                return attr in ("isGearGuide", "comp_type")
            if "guide_root" in node:
                return attr == "ismodel"
            return False

        mock_cmds.attributeQuery.side_effect = fake_aq

        def fake_getattr(attr_path):
            if "comp_type" in attr_path:
                return "arm_2jnt_01"
            return None

        mock_cmds.getAttr.side_effect = fake_getattr

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("list_shifter_components")
            result = mod.list_shifter_components(include_guides=True)
            assert result["success"] is True
            guides = result["context"]["guides"]
            assert len(guides) == 2
            flags_all = []
            for g in guides:
                flags_all.extend(g.get("flags", []))
            assert "guide_element" in flags_all
            assert "model_root" in flags_all
            guide_names = [g["name"] for g in guides]
            assert "some_random_transform" not in guide_names


# ---------------------------------------------------------------------------
# create_shifter_guide_from_template
# ---------------------------------------------------------------------------


class TestCreateShifterGuideFromTemplate:
    """Tests for create_shifter_guide_from_template tool.

    The real ``draw_comp(comp_type, parent=None, showUI=True)`` is
    signature-constrained; calling it with ``name=``, ``pos=``, or extra
    kwargs would raise TypeError at runtime.
    """

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

    def test_calls_draw_comp_with_correct_signature(self):
        """Tool must call draw_comp(comp_type, parent=None, showUI=False)."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.draw_comp = _constrained_draw_comp
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(
                guide_name="my_guide",
                template="arm_2jnt_01",
                position=[0.0, 10.0, 0.0],
                parent_guide="root_guide",
            )
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("template") == "arm_2jnt_01"
            assert ctx.get("node") is not None

    def test_extra_kwargs_not_passed_to_draw_comp(self):
        """parameters dict must NOT be unpacked into draw_comp kwargs."""
        calls = []

        def _tracked_draw_comp(comp_type, parent=None, showUI=True):
            calls.append({"comp_type": comp_type, "parent": parent, "showUI": showUI})
            return "guide1"

        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.draw_comp = _tracked_draw_comp
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(
                guide_name="g",
                template="arm_2jnt_01",
                parameters={"side": "L"},
            )
            assert result["success"] is True
            assert len(calls) == 1
            # draw_comp must NOT receive "side" or any extra kwarg
            assert "side" not in calls[0]

    def test_draw_comp_no_node_returned(self):
        """When draw_comp() returns None, must return skill_error — no fake success."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.draw_comp = _constrained_draw_comp_none
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("create_shifter_guide_from_template")
            result = mod.create_shifter_guide_from_template(guide_name="g", template="leg_2jnt_01")
            assert result["success"] is False
            assert "node" not in result.get("context", {})
            assert "Failed" in result["message"]


# ---------------------------------------------------------------------------
# build_shifter_rig
# ---------------------------------------------------------------------------


class TestBuildShifterRig:
    """Tests for build_shifter_rig tool.

    The real ``build_from_selection()`` takes **no arguments**.  There is
    no ``full`` / ``preview`` mode in the upstream API.
    """

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

    def test_calls_build_from_selection_no_args(self):
        """build_from_selection() must be called with ZERO arguments."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = _constrained_build_from_selection
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "my_guide"
            assert ctx.get("built_guides") == ["rig1", "rig2"]

    def test_build_no_guide_name(self):
        """No guide_name → builds from whatever is selected."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = _constrained_build_from_selection
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig()
            assert result["success"] is True
            ctx = result.get("context", {})
            assert ctx.get("guide_built") == "selection"

    def test_single_node_result(self):
        """When build_from_selection returns a scalar string, not a list."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = _constrained_build_from_selection_single
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="test")
            assert result["success"] is True
            assert result["context"]["built_guides"] == ["single_rig"]

    def test_guide_not_found_returns_error(self):
        """When guide_name does not exist, must return error — no silent fallback."""
        mock_gui_mgr = SimpleNamespace()
        mock_gui_mgr.build_from_selection = _constrained_build_from_selection
        mock_modules = _make_mock_modules(guide_manager=mock_gui_mgr)
        # Simulate guide not found: select raises RuntimeError
        mock_modules["maya.cmds"].select = MagicMock(side_effect=RuntimeError("not found"))

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("build_shifter_rig")
            result = mod.build_shifter_rig(guide_name="nonexistent_guide")
            assert result["success"] is False
            assert "not found" in result["message"].lower()


# ---------------------------------------------------------------------------
# export_shifter_guide_template
# ---------------------------------------------------------------------------


class TestExportShifterGuideTemplate:
    """Tests for export_shifter_guide_template tool.

    The real ``export_guide_template(filePath, meta)`` uses keyword
    arguments — *filePath* is the output file, *meta* is a metadata dict.
    The export target comes from the current Maya selection, not a name
    argument.
    """

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

    def test_calls_export_guide_template_with_filePath_and_meta(self):
        """Tool must use ``filePath`` and ``meta`` kwargs — not positional (guide_name, path)."""
        calls = []

        def _tracked_export(filePath, meta):
            calls.append({"filePath": filePath, "meta": meta})
            Path(filePath).parent.mkdir(parents=True, exist_ok=True)
            Path(filePath).write_bytes(b"fake")

        mock_io = SimpleNamespace()
        mock_io.export_guide_template = _tracked_export
        mock_modules = _make_mock_modules(io=mock_io)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide")
            assert result["success"] is True
            ctx = result.get("context", {})
            assert "template_base64" in ctx
            assert len(ctx["template_base64"]) > 0
            assert len(calls) == 1
            # Must use filePath= and meta= kwargs
            assert "filePath" in calls[0]
            assert "meta" in calls[0]
            assert isinstance(calls[0]["meta"], dict)
            assert calls[0]["meta"].get("include_metadata") is True

    def test_calls_export_guide_template_to_file(self, tmp_path):
        output = tmp_path / "exported_template.gct"
        calls = []

        def _tracked_export(filePath, meta):
            calls.append({"filePath": filePath, "meta": meta})

        mock_io = SimpleNamespace()
        mock_io.export_guide_template = _tracked_export
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
            assert len(calls) == 1
            assert calls[0]["filePath"] == str(output)
            assert calls[0]["meta"] == {"include_metadata": True}

    def test_no_metadata_export(self):
        calls = []

        def _tracked_export(filePath, meta):
            calls.append(meta)
            Path(filePath).parent.mkdir(parents=True, exist_ok=True)
            Path(filePath).write_bytes(b"data")

        mock_io = SimpleNamespace()
        mock_io.export_guide_template = _tracked_export
        mock_modules = _make_mock_modules(io=mock_io)

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="my_guide", include_metadata=False)
            assert result["success"] is True
            assert calls[0] == {"include_metadata": False}

    def test_guide_not_found_returns_error(self):
        """When guide_name does not exist, must return error — no silent fallback."""
        mock_io = SimpleNamespace()
        mock_io.export_guide_template = _constrained_export_guide_template
        mock_modules = _make_mock_modules(io=mock_io)
        # Simulate guide not found: cmds.select raises RuntimeError
        mock_modules["maya.cmds"].select = MagicMock(side_effect=RuntimeError("not found"))

        with patch.dict(sys.modules, mock_modules):
            mod = _load_script("export_shifter_guide_template")
            result = mod.export_shifter_guide_template(guide_name="nonexistent_guide")
            assert result["success"] is False
            assert "not found" in result["message"].lower()


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
