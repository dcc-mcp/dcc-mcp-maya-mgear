"""Import an official mGear Shifter sample template (e.g. quadruped.sgt).

Real mGear API: ``mgear.shifter.io.import_guide_template(filePath)``
(io.py:33-55).  The function accepts a single keyword argument *filePath*
pointing to the template file on disk.

This tool wraps the import call, locates the sample template inside the
installed mGear ``shifter/samples/`` directory, and returns structured
diagnostics (guide root, component count, component names, created
top-level nodes, and any warnings).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _resolve_template_path(template_name: str) -> Optional[Path]:
    """Find a sample template file by name inside the installed mGear shifter/samples/ directory.

    Searches for ``template_name`` with extensions ``.sgt``, ``.gct``, ``.template``
    (in that order).  Returns the first matching ``Path`` or ``None``.
    """
    import mgear

    mgear_root = Path(mgear.__path__[0])
    samples_dir = mgear_root / "shifter" / "samples"
    if not samples_dir.is_dir():
        return None

    # Strip any user-supplied extension to normalise the search
    base = Path(template_name)
    if base.suffix:
        template_name = base.stem

    for ext in (".sgt", ".gct", ".template"):
        candidate = samples_dir / "{}{}".format(template_name, ext)
        if candidate.is_file():
            return candidate

    return None


def _collect_import_result() -> Dict[str, Any]:
    """Collect structured diagnostics after a successful template import.

    Returns a dict with ``guide_root``, ``total_components``, ``component_names``,
    ``created_nodes``, and ``warnings``.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return {
            "guide_root": None,
            "total_components": 0,
            "component_names": [],
            "created_nodes": [],
            "warnings": ["Maya is not available — cannot collect scene diagnostics."],
        }

    result: Dict[str, Any] = {
        "guide_root": None,
        "total_components": 0,
        "component_names": [],
        "created_nodes": [],
        "warnings": [],
    }

    try:
        # Find the guide root (ismodel transform)
        all_transforms = cmds.ls(type="transform", long=True) or []
        guide_roots = [t for t in all_transforms if cmds.attributeQuery("ismodel", node=t, exists=True) and cmds.getAttr("{}.ismodel".format(t))]
        if guide_roots:
            result["guide_root"] = guide_roots[0]

        # Collect components (isGearGuide transforms)
        gear_guides = [t for t in all_transforms if cmds.attributeQuery("isGearGuide", node=t, exists=True) and cmds.getAttr("{}.isGearGuide".format(t))]
        result["total_components"] = len(gear_guides)

        component_names: List[str] = []
        for g in gear_guides:
            if cmds.attributeQuery("comp_type", node=g, exists=True):
                ctype = cmds.getAttr("{}.comp_type".format(g))
                component_names.append(ctype)
        result["component_names"] = component_names

        # Top-level created nodes (direct children of world)
        top_level = cmds.ls(assemblies=True, long=True) or []
        result["created_nodes"] = [t for t in top_level if "|" not in t[1:]]

    except Exception as exc:
        result["warnings"].append("Scene diagnostics failed: {}".format(exc))

    return result


def import_shifter_sample_template(
    template_name: str,
    select_guide: bool = True,
) -> Dict[str, Any]:
    """Import an official mGear Shifter sample template (e.g. quadruped).

    Locates the template file inside the installed mGear ``shifter/samples/``
    directory and imports it via ``mgear.shifter.io.import_guide_template(filePath)``.

    Args:
        template_name: Template name (e.g. ``"quadruped"`` or ``"quadruped.sgt"``).
            Extensions ``.sgt``, ``.gct``, and ``.template`` are tried in order.
        select_guide: Whether to select the imported guide root after import
            (default ``True``).  Disable to leave selection unchanged.

    Returns:
        A ``skill_success`` / ``skill_error`` / ``skill_exception`` dict with
        ``guide_root``, ``total_components``, ``component_names``,
        ``created_nodes``, and ``warnings`` in the context.
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

        file_path = _resolve_template_path(template_name)
        if file_path is None:
            return skill_error(
                "Sample template '{}' not found".format(template_name),
                "Template '{}' not found in mgear/shifter/samples/".format(template_name),
                prompt="Verify the template name. Check mgear/shifter/samples/ for available templates.",
                template_name=template_name,
                mgear_available=True,
            )

        import mgear.shifter.io as io_module

        io_module.import_guide_template(filePath=str(file_path))

        if select_guide:
            try:
                import maya.cmds as cmds  # noqa: PLC0415
            except ImportError:
                pass
            else:
                try:
                    # Select the root guide after import
                    all_transforms = cmds.ls(type="transform", long=True) or []
                    for t in all_transforms:
                        if cmds.attributeQuery("ismodel", node=t, exists=True) and cmds.getAttr("{}.ismodel".format(t)):
                            cmds.select(t, replace=True)
                            break
                except Exception:
                    pass

        diagnostics = _collect_import_result()

        return skill_success(
            "Imported sample template '{}'".format(template_name),
            template_name=template_name,
            template_path=str(file_path),
            **diagnostics,
            prompt="Use build_shifter_rig to generate the rig from the imported guide.",
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
