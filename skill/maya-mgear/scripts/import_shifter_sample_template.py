"""Import an official mGear Shifter sample template (e.g. quadruped.sgt) into the scene.

Real mGear API: ``mgear.shifter.io.import_guide_template(filePath)``
(io.py:~180).  Sample templates are shipped with mGear under
``<mgear>/shifter/guide_templates/``.

The import creates guide hierarchy nodes in the Maya scene.  The tool
returns structured metadata suitable for follow-up ``build_shifter_rig``
calls.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

_SAMPLE_TEMPLATE_EXT = ".sgt"


def _find_template_path(template_name: str) -> Optional[str]:
    """Resolve *template_name* to an absolute .sgt file path in mGear's sample templates.

    Accepts ``"quadruped"`` or ``"quadruped.sgt"``.  Returns ``None`` when
    the template is not found.
    """
    name = template_name
    if not name.endswith(_SAMPLE_TEMPLATE_EXT):
        name += _SAMPLE_TEMPLATE_EXT

    try:
        import mgear.shifter  # noqa: PLC0415
    except ImportError:
        return None

    shifter_paths = getattr(mgear.shifter, "__path__", None)
    if not shifter_paths:
        return None

    # Layout shipped by mGear (verified against 5.2.1):
    # ``mgear/shifter/component/_templates/<name>`` — the same path upstream
    # ``io.import_sample_template()`` builds.
    for base in shifter_paths:
        for subdir in (
            os.path.join("component", "_templates"),
            "guide_templates",
        ):
            candidate = os.path.join(base, subdir, name)
            if os.path.isfile(candidate):
                return candidate

    # Fallback: search broader mgear install tree
    try:
        import mgear  # noqa: PLC0415
    except ImportError:
        return None

    mgear_paths = getattr(mgear, "__path__", [])
    for base in mgear_paths:
        for subdir in (
            os.path.join("shifter", "component", "_templates"),
            os.path.join("shifter", "guide_templates"),
            "guide_templates",
        ):
            candidate = os.path.join(base, subdir, name)
            if os.path.isfile(candidate):
                return candidate

    return None


def _find_guide_root() -> Optional[str]:
    """Find the guide root the import just created, as a long DAG name.

    ``mgear.shifter.io.import_guide_template()`` returns ``None`` (verified on
    mGear 5.2.1), and ``mgear.shifter.utils.get_guide()`` returns an
    *attribute* name such as ``"guide.ismodel"`` rather than a node — the same
    ``ls("*.attr")`` trap the rig-root lookups hit.  Scanning transforms for
    the ``ismodel`` attribute mGear stamps on the guide root is reliable.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return None

    try:
        nodes = cmds.ls(type="transform", long=True) or []
    except Exception:  # noqa: BLE001
        return None

    for node in nodes:
        try:
            if cmds.attributeQuery("ismodel", node=node, exists=True):
                return str(node)
        except Exception:  # noqa: BLE001, PERF203
            continue
    return None


def _import_template(file_path: str) -> str:
    """Import a .sgt template and return the root guide node.

    Delegates to ``mgear.shifter.io.import_guide_template(filePath)`` for the
    import itself, then resolves the guide root from the scene because that
    API returns ``None``.
    """
    import mgear.shifter.io as shifter_io  # noqa: PLC0415

    shifter_io.import_guide_template(filePath=file_path)

    root = _find_guide_root()
    if root:
        return root

    # The import still populated the scene; only the root lookup failed.
    raise RuntimeError(
        "import_guide_template() populated the scene but no guide root "
        "carrying the 'ismodel' attribute was found"
    )


def _inspect_imported_guide(root_node: str) -> Dict[str, Any]:
    """Inspect the scene to gather metadata about the imported guide.

    Returns *component_count*, *component_names*, *top_level_nodes*, and
    *warnings*.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return {
            "component_count": 0,
            "component_names": [],
            "top_level_nodes": [root_node],
            "warnings": ["Maya API not available — limited inspection"],
        }

    warnings: List[str] = []
    top_nodes: List[str] = []
    comp_names: List[str] = []
    comp_count = 0

    try:
        all_nodes = cmds.ls(root_node, dag=True, long=True) or []
    except Exception:
        all_nodes = [root_node]

    seen_roots: set = set()
    for node in all_nodes:
        if not isinstance(node, str):
            continue
        short = node.rsplit("|", 1)[-1] if "|" in node else node
        top_nodes.append(short)
        # Detect components via mGear attrs
        try:
            if cmds.attributeQuery("comp_type", node=node, exists=True):
                comp_type = cmds.getAttr(node + ".comp_type")
                if comp_type:
                    comp_names.append(str(comp_type))
                    comp_count += 1
        except Exception:
            pass
        # Track unique top-level roots
        parts = node.split("|")
        for p in parts:
            if p:
                seen_roots.add(p)
                break

    return {
        "component_count": comp_count,
        "component_names": sorted(set(comp_names)),
        "top_level_nodes": list(dict.fromkeys(top_nodes)),  # ordered dedup
        "warnings": warnings,
    }


def _select_guide(node: str) -> None:
    """Select *node* in Maya if available."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return
    try:
        cmds.select(node)
    except Exception:
        pass


def import_shifter_sample_template(
    template_name: str,
    select_guide: bool = True,
) -> Dict[str, Any]:
    """Import an official mGear Shifter sample template into the current scene.

    Resolves *template_name* against mGear's installed sample templates
    (e.g. ``quadruped.sgt``), imports it, and returns structured metadata
    about the imported guide.

    Args:
        template_name: Name of the sample template to import
            (e.g. ``"quadruped.sgt"`` or just ``"quadruped"``).
        select_guide: Whether to select the imported guide root in the
            Maya viewport after import (default ``True``).
    """
    try:
        try:
            import mgear.shifter  # noqa: F401
        except ImportError:
            return skill_error(
                "mGear Shifter is not available",
                "ImportError: cannot import mgear.shifter",
                prompt="Install mGear and ensure the Shifter module is on PYTHONPATH.",
                mgear_available=False,
            )

        file_path = _find_template_path(template_name)
        if file_path is None:
            return skill_error(
                "Sample template '{}' not found in mGear installation".format(
                    template_name
                ),
                "File not found: {}".format(template_name),
                prompt=(
                    "Verify the template name. Common samples include: "
                    "'quadruped', 'biped', 'cat'. Use list_shifter_components "
                    "to see available component types."
                ),
                template_name=template_name,
            )

        root_node = _import_template(file_path)
        metadata = _inspect_imported_guide(root_node)

        if select_guide:
            _select_guide(root_node)

        return skill_success(
            "Imported sample template '{}' -> root guide '{}' ({} components)".format(
                template_name, root_node, metadata.get("component_count", 0)
            ),
            template_name=template_name,
            file_path=file_path,
            imported_guide_root=root_node,
            component_count=metadata.get("component_count", 0),
            component_names=metadata.get("component_names", []),
            top_level_nodes=metadata.get("top_level_nodes", [root_node]),
            warnings=metadata.get("warnings", []),
            select_guide=select_guide,
            prompt=(
                "Use build_shifter_rig to generate the rig from this guide, "
                "or create_shifter_guide_from_template to add individual components."
            ),
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to import Shifter sample template")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`import_shifter_sample_template`."""
    return import_shifter_sample_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
