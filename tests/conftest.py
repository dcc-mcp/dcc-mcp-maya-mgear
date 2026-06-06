"""Shared fixtures and mocks for dcc-mcp-maya-mgear tests."""

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
# Mock mGear helpers
# ---------------------------------------------------------------------------


class _FakeComponentType:
    """Fake mGear Shifter component type for testing."""

    def __init__(self, name: str, description: str = "") -> None:
        self.__doc__ = description
        self._name = name


class _FakeGuideManager:
    """Fake mGear guide_manager with component type registry."""

    def __init__(self) -> None:
        self.componentTypes: Dict[str, _FakeComponentType] = {
            "spine": _FakeComponentType("spine", "Spine guide component for character rigging"),
            "arm": _FakeComponentType("arm", "Arm guide component with IK/FK setup"),
            "leg": _FakeComponentType("leg", "Leg guide component with IK/FK setup"),
            "finger": _FakeComponentType("finger", "Finger guide component"),
            "neck": _FakeComponentType("neck", "Neck guide component"),
        }

    def addGuide(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "guide1")
        return f"{name}_guide"

    def createGuide(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "guide1")
        return f"{name}_guide"

    def exportGuideTemplate(self, guide_name: str) -> Dict[str, Any]:
        return {"guide": guide_name, "exported": True}


def create_mock_mgear_modules() -> Dict[str, MagicMock]:
    """Build a complete mock mgear package structure.

    Returns a dict suitable for injecting into sys.modules.
    """
    mgear = MagicMock(spec=ModuleType)
    mgear.__version__ = "4.2.0"
    mgear.__name__ = "mgear"

    shifter = MagicMock(spec=ModuleType)
    shifter.__name__ = "mgear.shifter"

    component = MagicMock(spec=ModuleType)
    component.__name__ = "mgear.shifter.component"
    component.guide_manager = _FakeGuideManager()

    rig = MagicMock(spec=ModuleType)
    rig.__name__ = "mgear.shifter.rig"

    def _fake_build(guide_name: str, build_type: str = "full") -> str:
        return f"Built {guide_name} ({build_type})"

    rig.build = _fake_build

    shifter.component = component
    shifter.rig = rig
    mgear.shifter = shifter

    return {
        "mgear": mgear,
        "mgear.shifter": shifter,
        "mgear.shifter.component": component,
        "mgear.shifter.rig": rig,
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

    mock_maya = MagicMock()
    mock_maya.cmds = mock_cmds

    return mock_maya


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mgear_modules() -> Dict[str, MagicMock]:
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
def install_mgear(mock_mgear_modules: Dict[str, MagicMock]) -> Dict[str, MagicMock]:
    """Inject mock mgear into sys.modules and clean up after test."""
    for name, mod in mock_mgear_modules.items():
        sys.modules[name] = mod
    yield mock_mgear_modules
    for name in mock_mgear_modules:
        sys.modules.pop(name, None)


@pytest.fixture
def install_maya_and_mgear(
    mock_maya_module: MagicMock,
    mock_mgear_modules: Dict[str, MagicMock],
) -> Dict[str, MagicMock]:
    """Inject both mock maya and mock mgear into sys.modules."""
    sys.modules["maya"] = mock_maya_module
    sys.modules["maya.cmds"] = mock_maya_module.cmds
    merged = {"maya": mock_maya_module, "maya.cmds": mock_maya_module.cmds}
    for name, mod in mock_mgear_modules.items():
        sys.modules[name] = mod
        merged[name] = mod
    yield merged
    for name in merged:
        sys.modules.pop(name, None)


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
