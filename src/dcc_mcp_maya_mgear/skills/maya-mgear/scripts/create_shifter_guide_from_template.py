"""Create a Shifter guide from a named template at a specified location."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_success


def _validate_template(template: str) -> Optional[str]:
    """Check that *template* references a known Shifter component type.

    Returns None on success, or an error string.
    """
    try:
        import mgear.shifter.component as comp  # noqa: PLC0415
    except ImportError:
        return None  # Let runtime handle — can't validate without mGear

    guide_manager = getattr(comp, "guide_manager", None)
    if guide_manager is None or not hasattr(guide_manager, "componentTypes"):
        return None

    component_types = guide_manager.componentTypes
    if isinstance(component_types, dict) and template not in component_types:
        available = sorted(component_types.keys())
        return f"Unknown template '{template}'. Available: {', '.join(available)}"
    return None


def _create_guide_via_mgear(
    guide_name: str,
    template: str,
    position: List[float],
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Shifter guide using mGear's native API.

    This is called from within Maya where both maya.cmds and mgear are available.
    """
    import maya.cmds as cmds  # noqa: PLC0415
    import mgear.shifter.component as comp  # noqa: PLC0415

    guide_manager = getattr(comp, "guide_manager", None)
    if guide_manager is None:
        raise RuntimeError("mGear Shifter guide_manager is not available")

    # Position validation
    if len(position) != 3:
        raise ValueError(f"position must be a list of 3 floats, got {position}")

    # Resolve parent if specified
    parent_node: Optional[str] = None
    if parent_guide:
        if not cmds.objExists(parent_guide):
            raise ValueError(f"Parent guide '{parent_guide}' does not exist in the scene")
        parent_node = parent_guide

    # Create the guide using the mGear guide_manager
    create_kwargs: Dict[str, Any] = {
        "name": guide_name,
        "componentType": template,
    }
    if parameters:
        create_kwargs.update(parameters)

    # Use the guide_manager's addGuide method
    if hasattr(guide_manager, "addGuide"):
        guide_node = guide_manager.addGuide(**create_kwargs)
    elif hasattr(guide_manager, "createGuide"):
        guide_node = guide_manager.createGuide(**create_kwargs)
    else:
        raise RuntimeError("Unable to create guide: guide_manager has no addGuide/createGuide method")

    # Position the guide
    if guide_node and cmds.objExists(guide_node):
        cmds.setAttr(f"{guide_node}.translate", *position, type="double3")
        if parent_node:
            cmds.parent(guide_node, parent_node)

    # If a single object was returned, wrap it
    guide_nodes = guide_node if isinstance(guide_node, list) else [guide_node]

    return {
        "guide_name": guide_name,
        "template": template,
        "position": position,
        "parent": parent_guide,
        "created_nodes": guide_nodes,
        "parameters": parameters or {},
    }


def create_shifter_guide_from_template(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> dict:
    """Create a Shifter guide from a named template at a specified location.

    Uses mGear Shifter's component system to instantiate a rigging guide from a
    template (e.g. "spine", "arm", "leg").  The guide serves as the blueprint for
    the final rig built by ``build_shifter_rig``.

    Args:
        guide_name: Unique name for the new guide.
        template: Component template name (e.g. "spine", "arm", "leg", "finger").
        position: World-space ``[x, y, z]``. Defaults to origin ``[0, 0, 0]``.
        parent_guide: Optional parent guide name for hierarchy organization.
        parameters: Additional template-specific parameters as key-value pairs.

    Returns:
        ToolResult dict with created guide info.
    """
    pos = position or [0.0, 0.0, 0.0]

    # Validate position
    if len(pos) != 3:
        return skill_error(
            "Invalid position",
            f"position must be a list of 3 floats, got {pos}",
            prompt="Provide a valid [x, y, z] position.",
        )

    # Check mGear availability
    try:
        import mgear  # noqa: PLC0415, F401
    except ImportError:
        return skill_error(
            "mGear is not available",
            "ImportError: mgear could not be imported",
            prompt="Ensure mGear is installed in Maya's Python environment.",
            possible_solutions=[
                "Install mGear from https://github.com/mgear-dev/mgear",
                "Verify Maya's Python environment includes the mGear module path",
            ],
        )

    # Check Maya availability
    try:
        import maya.cmds  # noqa: PLC0415, F401
    except ImportError:
        return skill_error(
            "Maya is not available",
            "ImportError: maya.cmds could not be imported",
            prompt="This tool must run inside Maya's Python environment.",
        )

    # Optional template validation (non-fatal — lets mGear report errors)
    validation_error = _validate_template(template)
    if validation_error:
        return skill_error(
            "Invalid template",
            validation_error,
            prompt="Use list_shifter_components to see available component types.",
        )

    try:
        result = _create_guide_via_mgear(
            guide_name=guide_name,
            template=template,
            position=pos,
            parent_guide=parent_guide,
            parameters=parameters,
        )
        return skill_success(
            f"Created Shifter guide '{guide_name}' from template '{template}'",
            prompt="Use build_shifter_rig to build the rig from this guide.",
            **result,
        )
    except Exception as exc:
        from dcc_mcp_core.skill import skill_exception

        return skill_exception(
            exc,
            message=f"Failed to create guide '{guide_name}'",
            possible_solutions=[
                "Check that the template name is correct",
                "Verify the mGear Shifter plugin is loaded",
                "Ensure no other guide has the same name",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`create_shifter_guide_from_template`."""
    return create_shifter_guide_from_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
