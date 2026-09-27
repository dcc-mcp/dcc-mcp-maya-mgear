"""Build a rig from an existing Shifter guide in the scene.

Real mGear API: ``mgear.shifter.guide_manager.build_from_selection()``
(guide_manager.py:86-95).  This function takes no arguments — it builds
whatever guide(s) are currently selected in Maya.  The build result is
read back afterwards (joint / control / transform counts) so callers get
verifiable numbers instead of only the returned node names.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _select_guide(guide_name: str) -> bool:
    """Select a guide node in Maya by name.  Returns True on success.

    Existence is checked explicitly: ``cmds.select`` silently ignores unknown
    names in some Maya versions, which would build whatever happened to be
    selected instead of failing loudly.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return False
    try:
        if hasattr(cmds, "objExists") and not cmds.objExists(guide_name):
            return False
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


def _collect_rig_metrics(cmds: Any, roots: List[str]) -> Dict[str, Any]:
    """Count joints, controls and transforms under the built rig *roots*.

    Controls are the distinct transforms owning a ``nurbsCurve`` shape — the
    shape mGear builds for every animatable control.  When *roots* is empty
    (mGear returned nothing) the counts fall back to the whole scene and
    ``metrics_scope`` says so.
    """
    scope = "rig" if roots else "scene"
    metrics: Dict[str, Any] = {
        "metrics_scope": scope,
        "joint_count": 0,
        "control_count": 0,
        "transform_count": 0,
    }
    try:
        if roots:
            joints = cmds.ls(*roots, dag=True, type="joint", long=True) or []
            transforms = cmds.ls(*roots, dag=True, type="transform", long=True) or []
            curves = cmds.ls(*roots, dag=True, type="nurbsCurve", long=True) or []
        else:
            joints = cmds.ls(type="joint", long=True) or []
            transforms = cmds.ls(type="transform", long=True) or []
            curves = cmds.ls(type="nurbsCurve", long=True) or []
    except Exception:  # noqa: BLE001 - metrics are advisory, never fatal
        return metrics

    metrics["joint_count"] = len(joints)
    metrics["transform_count"] = len(transforms)
    metrics["control_count"] = len({c.rsplit("|", 1)[0] for c in curves if "|" in c})
    return metrics


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

        metrics: Dict[str, Any] = {
            "metrics_scope": "unavailable",
            "joint_count": 0,
            "control_count": 0,
            "transform_count": 0,
        }
        try:
            import maya.cmds as cmds  # noqa: PLC0415

            metrics = _collect_rig_metrics(cmds, result.get("built_guides", []))
        except ImportError:
            pass

        joint_count = metrics["joint_count"]
        control_count = metrics["control_count"]
        summary = "Built {} guide(s)".format(n_built)
        if metrics["metrics_scope"] != "unavailable":
            summary = "{}: {} joint(s), {} control(s)".format(
                summary, joint_count, control_count
            )

        return skill_success(
            summary,
            **result,
            **metrics,
            prompt=(
                "Verify the generated rig in the viewport. Use export_shifter_rig "
                "to write it to FBX/ABC, or export_shifter_guide_template to save "
                "the guide as a template."
            ),
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
