"""List available Shifter component types and existing guides in the scene."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _get_component_list() -> List[Any]:
    """Try to get the Shifter component list via the preferred API path."""
    import mgear.shifter.component as comp

    # mGear Shifter component registry
    # Preferred: getComponentList()
    if hasattr(comp, "getComponentList"):
        return list(comp.getComponentList())

    # Fallback: iterate over component registry mapping
    if hasattr(comp, "componentMapping"):
        return list(comp.componentMapping.keys())

    # Fallback: try ComponentManager
    manager = getattr(comp, "ComponentManager", None)
    if manager is not None and hasattr(manager, "getAvailableComponents"):
        return list(manager.getAvailableComponents())

    return []


def _get_scene_guides(include_guides: bool = True) -> List[Dict[str, Any]]:
    """Query existing Shifter guides from the Maya scene."""
    if not include_guides:
        return []

    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return []

    guides: List[Dict[str, Any]] = []
    try:
        # mGear guides are typically stored in a namespace or have a specific attribute
        all_transforms = cmds.ls(type="transform", long=True) or []
        for node in all_transforms:
            try:
                if cmds.attributeQuery("is_guide", node=node, exists=True):
                    guide_val = cmds.getAttr("{}.is_guide".format(node))
                    if guide_val:
                        guides.append(
                            {
                                "name": node.split("|")[-1],
                                "full_path": node,
                            }
                        )
            except Exception:  # noqa: PERF203
                continue

        # Also try the mgear guide rig top node convention
        if not guides:
            for node in all_transforms:
                if "guide" in node.lower() or "Guide" in node:
                    guides.append(
                        {
                            "name": node.split("|")[-1],
                            "full_path": node,
                        }
                    )

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
