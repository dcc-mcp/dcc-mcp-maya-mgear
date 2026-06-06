"""Build a rig from an existing Shifter guide in the Maya scene."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _get_guide_nodes(guide_name: Optional[str] = None) -> List[str]:
    """Find Shifter guide nodes in the current Maya scene.

    Args:
        guide_name: Optional guide name to filter by. Returns all guides if None.

    Returns:
        List of guide node names (short names).
    """
    import maya.cmds as cmds  # noqa: PLC0415

    candidates: List[str] = []

    # Search for nodes with the mGear guide attribute
    all_transforms = cmds.ls(type="transform", long=True) or []
    for node in all_transforms:
        short = node.split("|")[-1]
        try:
            if cmds.attributeQuery("isGearGuide", node=node, exists=True):
                if guide_name is None or short == guide_name:
                    candidates.append(short)
        except Exception:  # noqa: BLE001
            # Also check naming convention
            if short.endswith("_guide") or short.endswith("_Guide"):
                if guide_name is None or short == guide_name:
                    candidates.append(short)

    return candidates


def _build_guides_via_mgear(
    guide_names: List[str],
    build_type: str = "full",
) -> Dict[str, Any]:
    """Execute the Shifter build process for the specified guides.

    Args:
        guide_names: List of guide node names to build.
        build_type: "full" or "preview" build mode.

    Returns:
        Dict with build results.
    """
    import mgear.shifter.rig as shifter_rig  # noqa: PLC0415

    build_fn = getattr(shifter_rig, "build", None)
    if build_fn is None:
        raise RuntimeError("mGear Shifter build function is not available")

    # mGear build is typically per-guide
    built = []
    errors = []
    for guide_name in guide_names:
        try:
            result = build_fn(guide_name, build_type=build_type)
            built.append({"guide": guide_name, "result": str(result)})
        except Exception as exc:
            errors.append({"guide": guide_name, "error": str(exc)})

    return {
        "build_type": build_type,
        "total": len(guide_names),
        "built": len(built),
        "failed": len(errors),
        "built_guides": built,
        "errors": errors,
    }


def build_shifter_rig(
    guide_name: Optional[str] = None,
    build_type: str = "full",
) -> dict:
    """Build a rig from an existing Shifter guide in the scene.

    Invokes mGear Shifter's build process to generate the final rig from one or
    all guides.  The built rig includes joints, controls, IK handles, and other
    rigging elements as determined by the guide definition.

    Args:
        guide_name: Name of the guide to build. Builds all guides if None.
        build_type: ``"full"`` (complete build) or ``"preview"`` (lightweight
            preview build). Defaults to ``"full"``.

    Returns:
        ToolResult dict with build results per guide.
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

    # Find guide nodes
    guide_nodes = _get_guide_nodes(guide_name)

    if not guide_nodes:
        if guide_name:
            return skill_error(
                f"Guide not found: '{guide_name}'",
                f"No Shifter guide named '{guide_name}' exists in the scene",
                prompt="Use list_shifter_components to see available guides.",
            )
        return skill_error(
            "No guides found",
            "No Shifter guides exist in the current scene",
            prompt="Use create_shifter_guide_from_template to create a guide first.",
        )

    try:
        result = _build_guides_via_mgear(guide_nodes, build_type)
        failed = result.get("failed", 0)

        if failed:
            return skill_success(
                f"Built {result['built']}/{result['total']} guide(s) with {failed} error(s)",
                prompt="Check the errors list for details on failed guides.",
                **result,
            )
        return skill_success(
            f"Built {result['built']} guide(s) ({build_type} mode)",
            prompt="Inspect the viewport to verify the built rig.",
            **result,
        )
    except Exception as exc:
        return skill_exception(
            exc,
            message="Failed to build Shifter rig",
            possible_solutions=[
                "Check that all guides have valid component types",
                "Verify mGear Shifter plugin is properly loaded",
                "Try a preview build first to isolate issues",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`build_shifter_rig`."""
    return build_shifter_rig(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
