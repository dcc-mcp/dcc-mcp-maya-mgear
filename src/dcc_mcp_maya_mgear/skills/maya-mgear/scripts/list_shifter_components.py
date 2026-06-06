"""List available Shifter component types and existing guides in the current Maya scene."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_success


def _get_component_types() -> Dict[str, Any]:
    """Retrieve registered Shifter component types from mGear."""
    result: Dict[str, Any] = {"count": 0, "types": [], "details": {}}

    try:
        import mgear.shifter.component as comp  # noqa: PLC0415
    except ImportError:
        return result

    guide_manager = getattr(comp, "guide_manager", None)
    if guide_manager is None or not hasattr(guide_manager, "componentTypes"):
        return result

    component_types = guide_manager.componentTypes
    if not isinstance(component_types, dict):
        return result

    result["count"] = len(component_types)
    result["types"] = sorted(component_types.keys())

    # Collect per-component metadata
    for name, ctype in component_types.items():
        info: Dict[str, Any] = {"name": name}
        if hasattr(ctype, "__doc__") and ctype.__doc__:
            info["description"] = ctype.__doc__.strip().split("\n")[0]
        result["details"][name] = info

    return result


def _get_scene_guides() -> List[Dict[str, Any]]:
    """List existing Shifter guide objects in the current Maya scene."""
    guides: List[Dict[str, Any]] = []

    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return guides

    try:
        # mGear guides typically carry a custom attribute or naming convention
        # Search by known mGear guide attribute
        all_transforms = cmds.ls(type="transform", long=True) or []

        for node in all_transforms:
            short = node.split("|")[-1]
            # mGear guide nodes typically have specific attributes
            if cmds.attributeQuery("isGearGuide", node=node, exists=True):
                attrs: Dict[str, Any] = {}
                for attr_name in ("componentType", "mgearVersion", "guideName"):
                    try:
                        if cmds.attributeQuery(attr_name, node=node, exists=True):
                            val = cmds.getAttr(f"{node}.{attr_name}")
                            attrs[attr_name] = val
                    except Exception:  # noqa: BLE001
                        pass
                guides.append(
                    {
                        "name": short,
                        "full_path": node,
                        "attributes": attrs,
                    }
                )
            # Also check by naming convention: *_guide or *_Guide
            elif short.endswith("_guide") or short.endswith("_Guide"):
                guides.append(
                    {
                        "name": short,
                        "full_path": node,
                        "attributes": {},
                    }
                )
    except Exception:  # noqa: BLE001
        pass

    return guides


def list_shifter_components(
    include_guides: bool = True,
    component_type: Optional[str] = None,
) -> dict:
    """List available Shifter component types and guides in the current scene.

    Enumerates registered mGear Shifter component classes and, when requested,
    existing guide objects in the scene.  Both parts are optional — return what
    is available and report clearly when mGear or Maya aren't loaded.

    Args:
        include_guides: When True, include existing guides from the current scene.
        component_type: Optional filter to return only details for a specific
            component type name.

    Returns:
        ToolResult dict with component types and/or scene guides.
    """
    try:
        context: Dict[str, Any] = {}

        # Component type enumeration (always)
        comp_types = _get_component_types()
        context["component_types"] = comp_types

        if component_type:
            if component_type in comp_types.get("details", {}):
                context["filtered_component"] = comp_types["details"][component_type]
                context["component_types"] = None  # reduce noise when filtering
            else:
                available = comp_types.get("types", [])
                return skill_error(
                    f"Unknown component type: '{component_type}'",
                    f"'{component_type}' is not a registered Shifter component",
                    prompt="Call without component_type to see all available types.",
                    possible_solutions=[
                        f"Use one of: {', '.join(available)}" if available else "No component types registered",
                    ],
                    available_types=available,
                )

        # Scene guides
        if include_guides:
            guides = _get_scene_guides()
            context["guides"] = guides
            context["guides_count"] = len(guides)

        # Build summary
        type_count = comp_types.get("count", 0)
        parts = [f"{type_count} component type(s)"]
        if include_guides:
            parts.append(f"{context.get('guides_count', 0)} scene guide(s)")

        return skill_success(
            f"Listed {', '.join(parts)}",
            prompt="Use create_shifter_guide_from_template to create a new guide from a component type.",
            **context,
        )

    except Exception as exc:
        from dcc_mcp_core.skill import skill_exception

        return skill_exception(exc, message="Failed to list Shifter components")


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`list_shifter_components`."""
    return list_shifter_components(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
