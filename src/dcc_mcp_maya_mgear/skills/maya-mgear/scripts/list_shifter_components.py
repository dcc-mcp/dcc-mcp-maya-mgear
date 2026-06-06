"""List available Shifter component types and existing guides in the current Maya scene."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_success


def _get_component_types() -> Dict[str, Any]:
    """Retrieve registered Shifter component types from mGear's component directories.

    Uses the real mGear API:
    ``mgear.shifter.getComponentDirectories()`` → dict of dirs
    ``mgear.shifter.importComponent(comp_type)`` → load component module for metadata
    """
    result: Dict[str, Any] = {"count": 0, "types": [], "details": {}}

    try:
        import mgear.shifter as shifter  # noqa: PLC0415
    except ImportError:
        return result

    try:
        dirs = shifter.getComponentDirectories()
        all_types: set = set()
        for base, types in dirs.items():
            all_types.update(types)

        result["count"] = len(all_types)
        result["types"] = sorted(all_types)

        # Collect per-component metadata by importing each component
        for comp_type in sorted(all_types):
            info: Dict[str, Any] = {"name": comp_type}
            try:
                comp_mod = shifter.importComponent(comp_type)
                if comp_mod and hasattr(comp_mod, "__doc__") and comp_mod.__doc__:
                    info["description"] = comp_mod.__doc__.strip().split("\n")[0]
            except Exception:  # noqa: BLE001
                pass
            result["details"][comp_type] = info
    except Exception:  # noqa: BLE001
        pass

    return result


def _get_scene_guides() -> List[Dict[str, Any]]:
    """List existing Shifter guide objects in the current Maya scene.

    Detects guides by checking for real mGear guide attributes:
    ``isGearGuide``, ``ismodel``, ``comp_type``.
    """
    guides: List[Dict[str, Any]] = []

    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return guides

    try:
        all_transforms = cmds.ls(type="transform", long=True) or []

        for node in all_transforms:
            short = node.split("|")[-1]
            attrs: Dict[str, Any] = {}

            # Check for real mGear guide attributes
            is_guide = False
            for attr_name in ("isGearGuide", "ismodel", "comp_type"):
                try:
                    if cmds.attributeQuery(attr_name, node=node, exists=True):
                        is_guide = True
                        val = cmds.getAttr(f"{node}.{attr_name}")
                        attrs[attr_name] = val
                except Exception:  # noqa: BLE001
                    pass

            if is_guide:
                # Collect additional metadata if available
                for attr_name in ("mgearVersion", "guideName", "side", "mirror"):
                    try:
                        if attr_name not in attrs and cmds.attributeQuery(attr_name, node=node, exists=True):
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
    except Exception:  # noqa: BLE001
        pass

    return guides


def list_shifter_components(
    include_guides: bool = True,
    component_type: Optional[str] = None,
) -> dict:
    """List available Shifter component types and guides in the scene.

    Enumerates registered mGear Shifter component types using
    ``mgear.shifter.getComponentDirectories()`` and, when requested, existing
    guide objects in the scene detected via ``isGearGuide`` / ``ismodel`` /
    ``comp_type`` attributes.

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
                    f"'{component_type}' is not a registered Shifter component type",
                    prompt="Call without component_type to see all available types.",
                    possible_solutions=[
                        f"Use one of: {', '.join(available[:20])}" if available else "No component types registered",
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
