"""Build a rig from an existing Shifter guide in the scene.

Real mGear API: ``mgear.shifter.guide_manager.build_from_selection()``
(guide_manager.py:86-95).  This function takes no arguments — it builds
whatever guide(s) are currently selected in Maya.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _select_guide(guide_name: str) -> bool:
    """Select a guide node in Maya by name.  Returns True on success."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return False
    try:
        cmds.select(guide_name, replace=True)
        return True
    except Exception:
        return False


def _build_rig(guide_name: Optional[str]) -> Dict[str, Any]:
    """Build a rig via ``build_from_selection()`` — the real mGear API.

    The function takes **no arguments**.  The caller must pre-select the
    target guide(s) in Maya before invoking.
    """
    import mgear.shifter.guide_manager as gui_mgr

    if guide_name:
        ok = _select_guide(guide_name)
        if not ok:
            return {
                "built_guides": [],
                "guide_built": guide_name,
                "error": "Guide '{}' not found in the scene".format(guide_name),
            }

    # build_from_selection() — real mGear API (guide_manager.py:86-95)
    # Takes 0 args; builds whatever is currently selected.
    built = gui_mgr.build_from_selection()

    result: Dict[str, Any] = {}
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
) -> Dict[str, Any]:
    """Build a rig from an existing Shifter guide in the scene.

    Args:
        guide_name: Name of the guide to build from.  If ``None``, builds
            whatever guide(s) are currently selected in Maya.  Pre-select a
            guide with ``maya.cmds.select()`` before calling without a name.

    The underlying mGear ``build_from_selection()`` takes no arguments and
    does not expose a preview/full mode — build type is determined by the
    component's own configuration.
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

        result = _build_rig(guide_name)

        if result.get("error"):
            return skill_error(
                result["error"],
                "Guide '{}' not found".format(result.get("guide_built", "unknown")),
                prompt="Verify the guide name. Use list_shifter_components to see available guides.",
            )

        n_built = len(result.get("built_guides", []))
        return skill_success(
            "Built {} guide(s)".format(n_built),
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
