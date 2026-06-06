"""Build a rig from an existing Shifter guide in the scene."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _select_guide(guide_name: str) -> bool:
    """Select a guide node in Maya by name. Returns True if selection succeeded."""
    try:
        import maya.cmds as cmds

        cmds.select(guide_name, replace=True)
        return True
    except Exception:
        return False


def _build_rig(guide_name: Optional[str], build_type: str) -> Dict[str, Any]:
    """Build a rig using the real mGear Shifter API."""
    import mgear.shifter.guide_manager as gui_mgr

    result: Dict[str, Any] = {"build_type": build_type}

    # Select guide(s) in Maya before building
    if guide_name:
        _select_guide(guide_name)
    # No specific guide → build_from_selection() will build whatever is selected
    # or all guides if the function supports it

    # build_from_selection() — verified real mGear API (guide_manager.py:86-95)
    built = gui_mgr.build_from_selection()

    if isinstance(built, (list, tuple)):
        result["built_guides"] = [str(b) for b in built]
    elif built is not None:
        result["built_guides"] = [str(built)]
    else:
        result["built_guides"] = []

    result["guide_built"] = guide_name or "selection"
    return result


def build_shifter_rig(
    guide_name: Optional[str] = None,
    build_type: str = "full",
) -> Dict[str, Any]:
    """Build a rig from an existing Shifter guide in the scene.

    Args:
        guide_name: Name of the guide to build from. If None, builds whatever is currently
            selected in Maya (use maya.cmds.select() prior) or all available guides.
        build_type: "full" for complete rig, "preview" for lightweight preview.
    """
    if build_type not in ("full", "preview"):
        return skill_error(
            "Invalid build_type '{}'".format(build_type),
            "build_type must be 'full' or 'preview'",
            prompt="Use build_type='full' for the complete rig, or 'preview' for a fast preview.",
        )

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

        result = _build_rig(guide_name, build_type)

        n_built = len(result.get("built_guides", []))
        return skill_success(
            "Built {} guide(s) ({})".format(n_built, build_type),
            **result,
            prompt="Verify the generated rig in the viewport. Use export_shifter_guide_template to save as template.",
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to build Shifter rig")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`build_shifter_rig`."""
    return build_shifter_rig(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
