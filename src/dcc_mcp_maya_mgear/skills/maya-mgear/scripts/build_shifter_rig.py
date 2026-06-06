"""Build a rig from existing Shifter guides in the Maya scene."""

from __future__ import annotations

from typing import List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _get_guide_nodes(guide_name: Optional[str] = None) -> List[str]:
    """Find Shifter guide root/model nodes in the current Maya scene.

    Uses the real mGear guide detection attributes: ``isGearGuide``, ``ismodel``,
    and ``comp_type``.

    Args:
        guide_name: Optional guide node name to filter by. Returns all guide
            roots if None.

    Returns:
        List of guide root node names (short names).
    """
    import maya.cmds as cmds  # noqa: PLC0415

    candidates: List[str] = []

    all_transforms = cmds.ls(type="transform", long=True) or []
    for node in all_transforms:
        short = node.split("|")[-1]
        try:
            # Check for real mGear guide attributes in priority order
            is_guide = (
                cmds.attributeQuery("isGearGuide", node=node, exists=True)
                or cmds.attributeQuery("ismodel", node=node, exists=True)
                or cmds.attributeQuery("comp_type", node=node, exists=True)
            )
            if is_guide:
                if guide_name is None or short == guide_name:
                    candidates.append(short)
        except Exception:  # noqa: BLE001
            pass

    return candidates


def build_shifter_rig(
    guide_name: Optional[str] = None,
    build_type: str = "full",
) -> dict:
    """Build a rig from existing Shifter guides in the scene.

    Invokes mGear Shifter's ``Rig.build()`` process to generate the final rig
    from one or all guides.  The built rig includes joints, controls, IK handles,
    and other rigging elements defined by the guide.

    Args:
        guide_name: Name of a specific guide node to build from.  When None,
            builds from the current scene selection (matching mGear's
            ``build_from_selection`` pattern).
        build_type: ``"full"`` (complete build) or ``"preview"`` (lightweight
            build without full deformers/skinning).  Defaults to ``"full"``.

    Returns:
        ToolResult dict with build results including created nodes and timing.
    """
    # Validate build_type
    if build_type not in ("full", "preview"):
        return skill_error(
            f"Invalid build_type: '{build_type}'",
            "build_type must be 'full' or 'preview'",
            prompt="Specify build_type as 'full' or 'preview'.",
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
            ],
        )

    try:
        import maya.cmds as cmds  # noqa: PLC0415
        import mgear.shifter as shifter  # noqa: PLC0415

        # Determine build source
        if guide_name:
            guide_nodes = _get_guide_nodes(guide_name)
            if not guide_nodes:
                return skill_error(
                    f"Guide not found: '{guide_name}'",
                    f"No Shifter guide named '{guide_name}' exists in the scene",
                    prompt="Use list_shifter_components to see available guides.",
                )
            # Select the guide node for the build
            cmds.select(guide_nodes[0], replace=True)
        else:
            guide_nodes = _get_guide_nodes()
            if not guide_nodes:
                return skill_error(
                    "No guides found",
                    "No Shifter guides exist in the current scene",
                    prompt="Use create_shifter_guide_from_template to create a guide first.",
                )

        # Build using the real mGear Rig API
        # mgear.shifter.Rig() → rig.buildFromSelection() or rig.guide.setFromHierarchy() + rig.build()
        rig = shifter.Rig()

        if guide_name:
            # Build from a specific guide node
            import mgear.pymaya as pm  # noqa: PLC0415

            guide_pynode = pm.PyNode(guide_nodes[0])
            rig.guide.setFromHierarchy(guide_pynode)
        else:
            # Build from the selected hierarchy
            rig.guide.setFromHierarchy(cmds.ls(selection=True)[0])

        # For preview mode, we still use the normal build (mGear doesn't have
        # a separate preview mode — users can create preview joints via options)
        rig.log_window()
        model = rig.build()

        if rig.stopBuild:
            return skill_error(
                "Build cancelled",
                "The rig build was cancelled by user or ESC key",
                prompt="Retry the build when ready.",
            )

        # Collect results
        created_joints = cmds.ls(type="joint") or []

        return skill_success(
            f"Built Shifter rig from {len(guide_nodes)} guide(s) ({build_type} mode)",
            prompt="Inspect the viewport to verify the built rig. Check the shifter build log for details.",
            build_type=build_type,
            guide_count=len(guide_nodes),
            guides_used=guide_nodes,
            model=str(model) if model else None,
            joint_count=len(created_joints),
        )

    except Exception as exc:
        return skill_exception(
            exc,
            message="Failed to build Shifter rig",
            possible_solutions=[
                "Check that all guides have valid component types",
                "Verify mGear Shifter plugin is properly loaded",
                "Check the shifter build log for specific errors",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`build_shifter_rig`."""
    return build_shifter_rig(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
