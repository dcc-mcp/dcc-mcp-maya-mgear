"""Shared fixtures and mocks for dcc-mcp-maya-mgear tests.

Mocks match the real mGear Shifter API structure from mgear-dev/mgear:
  https://github.com/mgear-dev/mgear/blob/master/release/scripts/mgear/shifter/
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module loaders
# ---------------------------------------------------------------------------

SCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "src",
    "dcc_mcp_maya_mgear",
    "skills",
    "maya-mgear",
    "scripts",
)


def _load_skill_module(name: str) -> ModuleType:
    """Load a skill script module by filename (without .py extension)."""
    path = os.path.join(SCRIPTS_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"dcc_mcp_maya_mgear.skills.maya_mgear.scripts.{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Mock mGear modules — matching real mgear-dev/mgear API structure
# ---------------------------------------------------------------------------

# Standard component type names from mgear's classic/epic components
_KNOWN_COMPONENT_TYPES = {
    "arm",
    "leg",
    "spine",
    "neck",
    "finger",
    "chain",
    "chain_bezier",
    "biped",
    "clavicle",
    "foot",
    "hand",
    "head",
    "hip",
    "ik_foot",
    "ik_hand",
    "leaf_bone",
    "leg_3jnt",
    "spring",
    "squash",
    "stretchy_spline",
    "tail",
    "wing",
    "eye",
    "mouth_grill",
    "tongue",
    "unrealEngineSkeleton",
}


def _make_module(name: str, **attrs: Any) -> MagicMock:
    """Create a mock module with the given name and attributes."""
    mod = MagicMock(spec=ModuleType)
    mod.__name__ = name
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


def create_mock_mgear_modules() -> Dict[str, Any]:
    """Build a complete mock mgear package matching the real API.

    Returns a dict suitable for injecting into sys.modules.
    The structure mirrors:
      release/scripts/mgear/shifter/  (from mgear-dev/mgear)

    Key modules and their real-world APIs:
      - mgear.shifter.Rig()          — main rig class
      - mgear.shifter.Rig.build()    — build the rig, returns model PyNode
      - mgear.shifter.Rig.buildFromDict(conf_dict) — build from template dict
      - mgear.shifter.guide_manager.draw_comp(comp_type, parent, showUI)
      - mgear.shifter.io.export_guide_template(filePath, meta, conf)
      - mgear.shifter.io.get_guide_template_dict(guide_node, meta)
      - mgear.shifter.getComponentDirectories()
      - mgear.shifter.importComponent(comp_type)
      - mgear.shifter.importComponentGuide(comp_type)
      - guide node attrs: isGearGuide, ismodel, comp_type
    """
    # ---- mgear top-level ----
    mgear = _make_module("mgear", __version__="4.2.0")
    mgear.log = MagicMock()

    # ---- mgear.pymaya (used internally by mgear) ----
    pymaya = _make_module("mgear.pymaya")
    pymaya.PyNode = lambda name, **kw: MagicMock(name=f"PyNode({name})")

    # ---- mgear.core.utils (provides gatherCustomModuleDirectories etc.) ----
    core_utils = _make_module("mgear.core.utils")

    def _fake_gatherCustomModuleDirectories(env_key, default_dirs):
        return {"classic": sorted(_KNOWN_COMPONENT_TYPES)}

    core_utils.gatherCustomModuleDirectories = _fake_gatherCustomModuleDirectories
    mgear.core = _make_module("mgear.core", utils=core_utils)

    # ---- mgear.shifter.guide — Guide Rig class ----
    guide = _make_module("mgear.shifter.guide")

    # Nested guide.Rig class (the guide representation)
    guide_rig_instance = MagicMock()
    guide_rig_instance.componentsIndex = []
    guide_rig_instance.components = {}
    guide_rig_instance.getMergedOptions = MagicMock(return_value={"mode": "full"})
    guide_rig_instance.setFromHierarchy = MagicMock()
    guide_rig_instance.set_from_dict = MagicMock()
    guide_rig_instance.drawNewComponent = MagicMock()
    guide_rig_instance.draw_guide = MagicMock()
    guide_rig_instance.get_guide_template_dict = MagicMock(
        return_value={
            "elements": {},
            "meta": {},
        }
    )
    guide_rig_instance.refresh_user_metadata = MagicMock()

    def _create_guide_rig():
        return MagicMock(
            componentsIndex=[],
            components={},
            getMergedOptions=MagicMock(return_value={"mode": "full"}),
            setFromHierarchy=MagicMock(),
            set_from_dict=MagicMock(),
            drawNewComponent=MagicMock(),
            draw_guide=MagicMock(),
            get_guide_template_dict=MagicMock(return_value={"elements": {}, "meta": {}}),
            refresh_user_metadata=MagicMock(),
        )

    guide.Rig = _create_guide_rig

    # ---- mgear.shifter — main Shifter module ----
    shifter = _make_module("mgear.shifter")

    # Build result model
    _model = MagicMock()
    _model.name.return_value = "rig"

    # Rig class (the main rig builder)
    rig_instance = MagicMock()
    rig_instance.guide = _create_guide_rig()
    rig_instance.build = MagicMock(return_value=_model)
    rig_instance.buildFromDict = MagicMock(return_value={"build_data": {}})
    rig_instance.buildFromSelection = MagicMock(return_value=_model)
    rig_instance.log_window = MagicMock()
    rig_instance.stopBuild = False
    rig_instance.model = _model
    rig_instance.options = {"mode": "full"}

    def _create_rig():
        g = _create_guide_rig()
        instance = MagicMock()
        instance.guide = g
        instance.build = MagicMock(return_value=_model)
        instance.buildFromDict = MagicMock(return_value={"build_data": {}})
        instance.buildFromSelection = MagicMock(return_value=_model)
        instance.log_window = MagicMock()
        instance.stopBuild = False
        instance.model = _model
        instance.options = {"mode": "full"}
        return instance

    shifter.Rig = _create_rig

    # Module-level functions
    shifter.getComponentDirectories = MagicMock(
        return_value={
            "classic": sorted(_KNOWN_COMPONENT_TYPES),
        }
    )
    shifter.importComponent = MagicMock(return_value=_make_module("component", __doc__="A mGear Shifter component."))
    shifter.importComponentGuide = MagicMock(return_value=_make_module("component.guide", __doc__="Component guide."))
    shifter.clearComponentCache = MagicMock()

    # ---- mgear.shifter.guide_manager ----
    guide_mgr = _make_module("mgear.shifter.guide_manager")

    def _fake_draw_comp(comp_type, parent=None, showUI=True):
        """Simulate drawing a component. Returns Nothing (side effect only)."""
        pass

    guide_mgr.draw_comp = _fake_draw_comp
    shifter.guide_manager = guide_mgr

    # ---- mgear.shifter.io ----
    io_mod = _make_module("mgear.shifter.io")

    def _fake_get_guide_template_dict(guide_node, meta=None):
        # guide_node is a PyNode mock (MagicMock from pm.PyNode)
        node_name = str(guide_node) if guide_node else "unknown_guide"
        return {
            "elements": {
                node_name: {
                    "comp_type": "arm",
                    "params": {},
                }
            },
            "meta": meta or {},
        }

    def _fake_export_guide_template(filePath=None, meta=None, conf=None, *args):
        pass

    io_mod.get_guide_template_dict = _fake_get_guide_template_dict
    io_mod.export_guide_template = _fake_export_guide_template
    io_mod.import_guide_template = MagicMock()
    shifter.io = io_mod

    # ---- mgear.shifter component sub-modules ----
    shifter.component = _make_module("mgear.shifter.component")
    shifter_classic = _make_module("mgear.shifter_classic_components")
    shifter_epic = _make_module("mgear.shifter_epic_components")

    # Wire up mgear sub-attributes
    mgear.shifter = shifter
    mgear.pymaya = pymaya
    mgear.shifter_classic_components = shifter_classic
    mgear.shifter_epic_components = shifter_epic

    return {
        "mgear": mgear,
        "mgear.pymaya": pymaya,
        "mgear.core": mgear.core,
        "mgear.core.utils": core_utils,
        "mgear.shifter": shifter,
        "mgear.shifter.guide": guide,
        "mgear.shifter.guide_manager": guide_mgr,
        "mgear.shifter.io": io_mod,
        "mgear.shifter.component": shifter.component,
        "mgear.shifter_classic_components": shifter_classic,
        "mgear.shifter_epic_components": shifter_epic,
    }


def create_mock_maya_module() -> MagicMock:
    """Build a mock maya package with maya.cmds submodule."""
    mock_cmds = MagicMock()
    mock_cmds.ls.return_value = ["spine_guide", "arm_guide"]
    mock_cmds.objExists.return_value = True
    mock_cmds.attributeQuery.return_value = True
    mock_cmds.about.return_value = "2024.1"
    mock_cmds.listAttr.return_value = ["translate", "rotate", "scale", "visibility"]
    mock_cmds.getAttr.return_value = 0.0
    mock_cmds.listRelatives.return_value = ["child_ctrl"]
    mock_cmds.objectType.return_value = "transform"
    mock_cmds.file.return_value = "/tmp/test_scene.ma"
    mock_cmds.parent.return_value = ["parent1"]
    mock_cmds.setAttr = MagicMock()
    mock_cmds.select = MagicMock()
    mock_cmds.joint = MagicMock(return_value="joint1")

    mock_maya = MagicMock()
    mock_maya.cmds = mock_cmds

    return mock_maya


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mgear_modules() -> Dict[str, Any]:
    """Return mock mgear package modules for injection into sys.modules."""
    return create_mock_mgear_modules()


@pytest.fixture
def mock_maya_module() -> MagicMock:
    """Return a mock maya package with maya.cmds submodule."""
    return create_mock_maya_module()


@pytest.fixture
def install_maya(mock_maya_module: MagicMock) -> MagicMock:
    """Inject mock maya into sys.modules and clean up after test."""
    sys.modules["maya"] = mock_maya_module
    sys.modules["maya.cmds"] = mock_maya_module.cmds
    yield mock_maya_module
    sys.modules.pop("maya", None)
    sys.modules.pop("maya.cmds", None)


@pytest.fixture
def install_mgear(mock_mgear_modules: Dict[str, Any]) -> Dict[str, Any]:
    """Inject mock mgear into sys.modules and clean up after test."""
    for name, mod in mock_mgear_modules.items():
        sys.modules[name] = mod
    yield mock_mgear_modules
    for name in mock_mgear_modules:
        sys.modules.pop(name, None)


@pytest.fixture
def install_maya_and_mgear(
    mock_maya_module: MagicMock,
    mock_mgear_modules: Dict[str, Any],
) -> Dict[str, Any]:
    """Inject both mock maya and mock mgear into sys.modules."""
    sys.modules["maya"] = mock_maya_module
    sys.modules["maya.cmds"] = mock_maya_module.cmds
    merged: Dict[str, Any] = {"maya": mock_maya_module, "maya.cmds": mock_maya_module.cmds}
    for name, mod in mock_mgear_modules.items():
        sys.modules[name] = mod
        merged[name] = mod
    yield merged
    for name in merged:
        sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# Skill module fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def inspect_mgear_environment_module() -> ModuleType:
    """Load the inspect_mgear_environment skill module."""
    return _load_skill_module("inspect_mgear_environment")


@pytest.fixture
def list_shifter_components_module() -> ModuleType:
    """Load the list_shifter_components skill module."""
    return _load_skill_module("list_shifter_components")


@pytest.fixture
def create_shifter_guide_from_template_module() -> ModuleType:
    """Load the create_shifter_guide_from_template skill module."""
    return _load_skill_module("create_shifter_guide_from_template")


@pytest.fixture
def build_shifter_rig_module() -> ModuleType:
    """Load the build_shifter_rig skill module."""
    return _load_skill_module("build_shifter_rig")


@pytest.fixture
def export_shifter_guide_template_module() -> ModuleType:
    """Load the export_shifter_guide_template skill module."""
    return _load_skill_module("export_shifter_guide_template")
