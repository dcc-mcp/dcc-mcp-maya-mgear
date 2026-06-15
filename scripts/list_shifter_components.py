"""List available Shifter component types and existing guides in the scene.

Real mGear API: ``mgear.shifter.getComponentDirectories()`` returns a
``{path: [component_name, ...]}`` dict (shifter/__init__.py:57-72).
The component NAMES are the dict *values*, not the keys' basenames.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _get_component_list() -> List[str]:
    """Enumerate component names from the real ``getComponentDirectories()`` dict.

    Non-component files such as ``__init__.py`` are filtered out — only
    valid mGear component type names are included.
    """
    import mgear.shifter

    # Returns {path: [component_name, ...]} — verified real mGear API
    mapping = mgear.shifter.getComponentDirectories()
    names: List[str] = []
    for component_list in mapping.values():
        for c in component_list:
            c_str = str(c)
            # Filter out Python module files (e.g. __init__.py) that may
            # appear alongside valid component names in the directory listing.
            if c_str.endswith(".py"):
                continue
            names.append(c_str)
    return sorted(set(names))


def _get_scene_guides(include_guides: bool = True) -> List[Dict[str, Any]]:
    """Query existing Shifter guides using official ``isGearGuide`` / ``ismodel`` attrs.

    Real mGear detection (guide_manager.py:35-40) uses ``node.hasAttr("isGearGuide")``
    and ``node.hasAttr("ismodel")`` — NOT a generic ``is_guide`` attribute or name
    heuristics.  We replicate the same logic via ``maya.cmds.attributeQuery``.
    """
    if not include_guides:
        return []

    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return []

    guides: List[Dict[str, Any]] = []
    try:
        all_transforms = cmds.ls(type="transform", long=True) or []
        for node in all_transforms:
            try:
                is_gear_guide = cmds.attributeQuery("isGearGuide", node=node, exists=True)
                is_model = cmds.attributeQuery("ismodel", node=node, exists=True)
                has_comp_type = cmds.attributeQuery("comp_type", node=node, exists=True)

                if is_gear_guide or is_model:
                    entry: Dict[str, Any] = {
                        "name": node.split("|")[-1],
                        "full_path": node,
                        "flags": [],
                    }
                    if is_gear_guide:
                        entry["flags"].append("guide_element")
                    if is_model:
                        entry["flags"].append("model_root")
                    if has_comp_type:
                        ctype = cmds.getAttr("{}.comp_type".format(node))
                        entry["component_type"] = str(ctype)
                    guides.append(entry)
            except Exception:  # noqa: PERF203
                continue
        return guides
    except Exception:
        return []


def list_shifter_components(
    include_guides: bool = True,
    component_type: Optional[str] = None,
) -> Dict[str, Any]:
    """List available Shifter component types and existing guides in the scene.

    Args:
        include_guides: Include existing guides from the current scene.
        component_type: Optional filter for specific component type name.
    """
    try:
        try:
            import mgear.shifter  # noqa: F401
        except ImportError:
            return skill_error(
                "mGear Shifter is not available",
                "ImportError: cannot import mgear.shifter",
                prompt="Install mGear (https://github.com/mgear-dev/mgear) and reload Maya.",
                mgear_available=False,
                shifter_available=False,
            )

        components = _get_component_list()
        component_names = [str(c) for c in components]

        if component_type:
            component_names = [c for c in component_names if component_type.lower() in c.lower()]

        guides = _get_scene_guides(include_guides)

        return skill_success(
            "Found {} component type(s){}".format(
                len(component_names),
                " and {} guide(s)".format(len(guides)) if include_guides else "",
            ),
            components=component_names,
            total_components=len(component_names),
            guides=guides if include_guides else [],
            total_guides=len(guides),
            prompt="Use create_shifter_guide_from_template to create a new guide from one of these component types.",
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to list Shifter components")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`list_shifter_components`."""
    return list_shifter_components(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
