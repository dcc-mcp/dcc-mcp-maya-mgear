"""Shared test fixtures for the mGear skill scripts.

The scripts are loaded by path with ``importlib`` (the same way the dcc-mcp
loader imports them), and ``maya.cmds`` / ``maya.mel`` are replaced by a
signature-aware fake so a wrong Maya call fails the test instead of being
swallowed by a permissive mock.
"""

from __future__ import annotations

import importlib.util
import shlex as _shlex
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

import pytest

SCRIPTS_ROOT = (
    Path(__file__).resolve().parent.parent / "skill" / "maya-mgear" / "scripts"
)

_COUNTER = [0]


def load_script(script_name: str) -> ModuleType:
    """Load ``skill/maya-mgear/scripts/<script_name>.py`` under a unique name."""
    _COUNTER[0] += 1
    script_path = SCRIPTS_ROOT / "{}.py".format(script_name)
    module_name = "skill_mgear_{}_{}".format(script_name, _COUNTER[0])
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FakeScene:
    """A tiny Maya DAG stand-in: long node name -> node type."""

    def __init__(
        self,
        nodes: Dict[str, str],
        attrs: Optional[Dict[str, Tuple[str, ...]]] = None,
        selection: Optional[List[str]] = None,
        keyframe_count: float = 0.0,
    ) -> None:
        self.nodes = dict(nodes)
        self.attrs = dict(attrs or {})
        self.selection = list(selection or [])
        self.keyframe_count = keyframe_count
        self.select_calls: List[Any] = []
        self.keyframe_calls: List[Dict[str, Any]] = []

    # -- maya.cmds API surface used by the scripts -------------------------
    def objExists(self, name: str) -> bool:
        return str(name) in self.nodes or "|{}".format(name) in self.nodes

    def _expand(self, name: str) -> str:
        """Resolve a short DAG name the way Maya does (``rig`` -> ``|rig``)."""
        if name in self.nodes:
            return name
        alt = "|" + str(name).lstrip("|")
        return alt if alt in self.nodes else str(name)

    def ls(self, *args: Any, **kwargs: Any) -> List[str]:
        if kwargs.get("selection"):
            return list(self.selection)

        if kwargs.get("assemblies"):
            return [n for n in self.nodes if n.count("|") == 1]

        attr_patterns = [a for a in args if isinstance(a, str) and a.startswith("*.")]
        if attr_patterns:
            matched: List[str] = []
            for pattern in attr_patterns:
                attr = pattern.split(".", 1)[1]
                for node, node_attrs in self.attrs.items():
                    if attr in node_attrs and node in self.nodes:
                        matched.append(node)
            return matched

        # Maya accepts both ``ls("a", "b")`` and ``ls(["a", "b"])".
        flat: List[str] = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                flat.extend(str(a) for a in arg)
            elif isinstance(arg, str):
                flat.append(arg)
        roots = [self._expand(a) for a in flat]
        if roots:
            if not kwargs.get("dag"):
                return [r for r in roots if r in self.nodes]
            pool: List[str] = []
            for root in roots:
                prefix = root if root.endswith("|") else root + "|"
                pool.extend(n for n in self.nodes if n == root or n.startswith(prefix))
        else:
            pool = list(self.nodes)

        node_type = kwargs.get("type")
        if node_type:
            pool = [n for n in pool if self.nodes.get(n) == node_type]
        return pool

    def playbackOptions(self, **kwargs: Any) -> float:
        if kwargs.get("minTime"):
            return 1.0
        return 120.0

    def pluginInfo(self, _plugin: str, **kwargs: Any) -> bool:
        return bool(kwargs.get("query"))  # already loaded

    def loadPlugin(self, _plugin: str) -> None:
        return None

    def keyframe(self, *_args: Any, **kwargs: Any) -> Any:
        # Maya returns a scalar for one target and a list of per-target counts
        # for several; the list form is the one that breaks naive int().
        self.keyframe_calls.append(dict(kwargs))
        if kwargs.get("hierarchy"):
            return [self.keyframe_count]
        return self.keyframe_count

    def select(self, *args: Any, **kwargs: Any) -> None:
        self.select_calls.append((args, kwargs))
        if kwargs.get("clear"):
            self.selection = []
            return
        if args and isinstance(args[0], (list, tuple)):
            self.selection = list(args[0])
        elif args and isinstance(args[0], str):
            self.selection = [args[0]]
        if args and isinstance(args[0], str) and not self.objExists(args[0]):
            # Real maya.cmds.select raises when nothing matches the name.
            raise RuntimeError("No object matches name: {}".format(args[0]))


def make_maya(
    monkeypatch: pytest.MonkeyPatch,
    scene: FakeScene,
    *,
    write_on_fbx: bool = True,
    write_on_abc: bool = True,
    fbx_bytes: bytes = b"FAKEFBX" * 256,
    abc_bytes: bytes = b"FAKEABC" * 256,
) -> Tuple[MagicMock, MagicMock]:
    """Install *scene* as ``maya.cmds`` and a file-writing ``maya.mel``.

    Both exporters write real bytes so the tools can read the export back —
    that read-back is the behaviour under test.
    """
    cmds = MagicMock()
    for name in (
        "objExists",
        "ls",
        "playbackOptions",
        "pluginInfo",
        "loadPlugin",
        "keyframe",
        "select",
    ):
        setattr(cmds, name, getattr(scene, name))

    def _write_abc(**kwargs: Any) -> None:
        job = str(kwargs.get("j", ""))
        # Split the job the way a shell would, so quoted values containing
        # spaces stay whole — that is the contract under test.
        parts = [p.strip('"') for p in _shlex.split(job, posix=False)]
        path = parts[parts.index("-file") + 1] if "-file" in parts else ""
        if write_on_abc and path:
            Path(path).write_bytes(abc_bytes)

    cmds.AbcExport.side_effect = _write_abc

    def _mel_eval(command: str) -> str:
        if command.startswith("FBXExport -f"):
            path = command.split('"')[1]
            if write_on_fbx:
                Path(path).write_bytes(fbx_bytes)
        return ""

    mel = MagicMock()
    mel.eval.side_effect = _mel_eval

    maya_module = MagicMock()
    maya_module.cmds = cmds
    maya_module.mel = mel
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", cmds)
    monkeypatch.setitem(sys.modules, "maya.mel", mel)
    return cmds, mel


def make_mgear(monkeypatch: pytest.MonkeyPatch, version: str = "5.2.1") -> MagicMock:
    """Install a fake ``mgear`` package exposing ``shifter.guide_manager``."""
    mgear = MagicMock()
    mgear.__version__ = version
    shifter = MagicMock()
    guide_manager = MagicMock()
    shifter.guide_manager = guide_manager
    monkeypatch.setitem(sys.modules, "mgear", mgear)
    monkeypatch.setitem(sys.modules, "mgear.shifter", shifter)
    monkeypatch.setitem(sys.modules, "mgear.shifter.guide_manager", guide_manager)
    return mgear


def hide_maya(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import maya.cmds`` raise ImportError."""
    monkeypatch.setitem(sys.modules, "maya", None)
    monkeypatch.setitem(sys.modules, "maya.cmds", None)


def hide_mgear(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import mgear`` raise ImportError."""
    monkeypatch.setitem(sys.modules, "mgear", None)
    monkeypatch.setitem(sys.modules, "mgear.shifter", None)


@pytest.fixture
def biped_scene() -> FakeScene:
    """A small built-rig scene: 2 joints, 2 controls, 1 mesh, 240 keyframes."""
    return FakeScene(
        nodes={
            "|biped_rig": "transform",
            "|biped_rig|root_Jnt": "joint",
            "|biped_rig|spine_Jnt": "joint",
            "|biped_rig|body_geo": "mesh",
            "|biped_rig|body_ctl": "transform",
            "|biped_rig|body_ctl|body_ctlShape": "nurbsCurve",
            "|biped_rig|global_ctl": "transform",
            "|biped_rig|global_ctl|global_ctlShape": "nurbsCurve",
            "|persp": "transform",
        },
        attrs={"|biped_rig": ("is_rig",)},
        keyframe_count=240.0,
    )
