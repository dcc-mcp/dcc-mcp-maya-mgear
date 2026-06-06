"""Create a Shifter guide from a named component type at a specified location."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _validate_component_type(comp_type: str) -> Optional[str]:
    """Check that *comp_type* is a known Shifter component type.

    Returns None on success, or an error string.
    """
    try:
        import mgear.shifter as shifter  # noqa: PLC0415
    except ImportError:
        return None  # Let runtime handle — can't validate without mGear

    try:
        dirs = shifter.getComponentDirectories()
        all_types: set = set()
        for base, types in dirs.items():
            all_types.update(types)
        if comp_type not in all_types:
            available = sorted(all_types)
            return f"Unknown component type '{comp_type}'. Available types: {', '.join(available[:20])}{'...' if len(available) > 20 else ''}"
    except Exception:  # noqa: BLE001
        return None  # Non-fatal — let mGear report the error at draw time

    return None


def create_shifter_guide_from_template(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> dict:
    """Create a Shifter guide from a named component type at a specified location.

    Uses mGear Shifter's ``draw_comp`` mechanism to instantiate a rigging guide
    component (e.g. "arm", "leg", "spine") in the Maya scene.  The guide serves
    as the blueprint for the final rig built by ``build_shifter_rig``.

    Args:
        guide_name: Descriptive name for the new guide (stored as note/comment).
        template: Component type name (e.g. "arm", "leg", "spine", "finger").
        position: World-space ``[x, y, z]`` for the guide root. Defaults to origin.
        parent_guide: Optional existing guide or transform to parent under.
        parameters: Additional template-specific parameters passed through to
            the component's ``drawNewComponent`` call.

    Returns:
        ToolResult dict with created guide info.

    Note:
        The mGear draw API does not accept a ``guide_name`` keyword — the name
        is set by the component itself.  *parameters* are forwarded to the
        component's settings UI (suppressed when running from MCP) so they
        become the initial values for the guide.
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
        import maya.cmds as cmds  # noqa: PLC0415, F401
    except ImportError:
        return skill_error(
            "Maya is not available",
            "ImportError: maya.cmds could not be imported",
            prompt="This tool must run inside Maya's Python environment.",
        )

    # Optional component type validation (non-fatal)
    validation_error = _validate_component_type(template)
    if validation_error:
        return skill_error(
            "Invalid component type",
            validation_error,
            prompt="Use list_shifter_components to see available component types.",
        )

    try:
        # Resolve parent if specified
        import mgear.pymaya as pm  # noqa: PLC0415

        parent_node = None
        if parent_guide:
            if not cmds.objExists(parent_guide):
                return skill_error(
                    f"Parent not found: '{parent_guide}'",
                    f"'{parent_guide}' does not exist in the scene",
                    prompt="Specify an existing transform or guide node as parent.",
                )
            parent_node = pm.PyNode(parent_guide)

        # Select the parent before drawing (mgear uses selection for placement)
        if parent_node:
            cmds.select(str(parent_node), replace=True)
        else:
            cmds.select(clear=True)

        # Draw the component using the real mGear API
        # mgear.shifter.guide_manager.draw_comp(comp_type, parent, showUI)
        # showUI=False to suppress the settings dialog when called from MCP
        import mgear.shifter.guide_manager as gm  # noqa: PLC0415

        gm.draw_comp(template, parent=parent_node, showUI=False)

        # Position the guide root if it was created at the origin
        if pos != [0.0, 0.0, 0.0]:
            selection_after = cmds.ls(selection=True, type="transform") or []
            if selection_after:
                guide_root = selection_after[-1]
                cmds.setAttr(f"{guide_root}.translate", *pos, type="double3")

        # Apply additional parameters if provided
        if parameters:
            selection_after = cmds.ls(selection=True, type="transform") or []
            for sel in selection_after:
                try:
                    for key, val in parameters.items():
                        attr_path = f"{sel}.{key}"
                        if cmds.attributeQuery(key, node=sel, exists=True):
                            cmds.setAttr(attr_path, val)
                except Exception:  # noqa: BLE001
                    pass

        # Get the created guide info
        selection_after = cmds.ls(selection=True, type="transform") or []
        created_nodes = [str(s) for s in selection_after]

        return skill_success(
            f"Created Shifter guide component '{template}'",
            prompt="Use build_shifter_rig to build the rig from this guide.",
            template=template,
            created_nodes=created_nodes,
            position=pos,
            parent=parent_guide,
            parameters=parameters or {},
        )

    except Exception as exc:
        return skill_exception(
            exc,
            message=f"Failed to create guide component '{template}'",
            possible_solutions=[
                f"Check that '{template}' is a valid component type",
                "Verify the mGear Shifter plugin is loaded",
                "Ensure no other guide has a conflicting name",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`create_shifter_guide_from_template`."""
    return create_shifter_guide_from_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
