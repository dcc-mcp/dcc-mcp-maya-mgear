"""Build a rig from an existing Shifter guide in the scene.

Real mGear API: ``mgear.shifter.Rig().buildFromSelection()`` — the same call
``mgear.shifter.guide_manager.build_from_selection()`` wraps
(guide_manager.py:86-95).  It takes no arguments and builds whatever guide(s)
are currently selected in Maya; upstream it **returns nothing** (it only
returns ``build_data`` when the ``data_collector`` option is on).

So the rig root is not taken from the return value — it is read back from
the built rig: ``Rig.model`` (mGear stamps ``is_rig`` on it in
``shifter/__init__.py``) with an ``mgear.shifter.utils.get_rig()``-style
attribute query as the fallback.  Joint / control / transform counts are then
read back from that root, so the numbers describe the rig that was just
built rather than the whole scene.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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


def _run_build() -> Tuple[Any, str]:
    """Run the mGear build for the current selection.

    Returns ``(rig, build_method)``.  *rig* is the ``mgear.shifter.Rig``
    instance when that class is importable, otherwise ``None`` — the legacy
    ``guide_manager.build_from_selection()`` entry point keeps no reference to
    the rig it builds.
    """
    import mgear.shifter as shifter

    rig_class = getattr(shifter, "Rig", None)
    if rig_class is not None:
        rig = rig_class()
        # Returns build_data only when the data_collector option is enabled;
        # the normal build returns None.  The return value is not the rig.
        rig.buildFromSelection()
        return rig, "shifter.Rig.buildFromSelection"

    import mgear.shifter.guide_manager as gui_mgr

    # Older mGear: identical work, but the Rig object is discarded upstream.
    gui_mgr.build_from_selection()
    return None, "shifter.guide_manager.build_from_selection"


def _resolve_rig_roots(cmds: Any, rig: Any) -> Tuple[List[str], str]:
    """Resolve the built rig root(s) as long DAG names.

    Order: ``rig.model`` (the root mGear creates and stamps with ``is_rig``)
    and, when that is unavailable, the same ``ls("*.is_rig")`` query
    ``mgear.shifter.utils.get_rig()`` uses.  Returns ``(roots, source)``.
    """
    candidates: List[str] = []

    model = getattr(rig, "model", None)
    if model:
        candidates.append(str(model))

    source = "rig.model"
    if not candidates:
        try:
            found = cmds.ls("*.is_rig", type="transform", long=True) or []
        except Exception:  # noqa: BLE001 - keep trying the wider query
            found = []
        candidates = [str(n) for n in found]
        source = "attribute:is_rig"

    if not candidates:
        return [], "unresolved"

    try:
        long_names = cmds.ls(candidates, long=True) or []
    except Exception:  # noqa: BLE001
        return candidates, source
    return ([str(n) for n in long_names] or candidates), source


def _build_rig(guide_name: Optional[str]) -> Dict[str, Any]:
    """Build the selected guide and locate the rig it produced.

    The build itself takes **no arguments** — the caller must pre-select the
    target guide(s) in Maya before invoking.
    """
    if guide_name:
        ok = _select_guide(guide_name)
        if not ok:
            return {
                "error": "Guide '{}' not found in the scene".format(guide_name),
                "guide_built": guide_name,
            }

    rig, build_method = _run_build()

    roots: List[str] = []
    root_source = "unresolved"
    try:
        import maya.cmds as cmds  # noqa: PLC0415

        roots, root_source = _resolve_rig_roots(cmds, rig)
    except ImportError:
        root_source = "maya_unavailable"

    return {
        "rig_roots": roots,
        "rig_root_source": root_source,
        "build_method": build_method,
        "guide_built": guide_name or "selection",
    }


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
                "mgear_shifter_unavailable",
                prompt="Install mGear and ensure the Shifter module is on PYTHONPATH.",
                mgear_available=False,
            )

        result = _build_rig(guide_name)

        if result.get("error"):
            return skill_error(
                result["error"],
                "guide_not_found",
                prompt="Verify the guide name. Use list_shifter_components to see available guides.",
                detail=result["error"],
                guide_name=result.get("guide_built", "unknown"),
            )

        roots = result.get("rig_roots", [])

        metrics: Dict[str, Any] = {
            "metrics_scope": "unavailable",
            "joint_count": 0,
            "control_count": 0,
            "transform_count": 0,
        }
        try:
            import maya.cmds as cmds  # noqa: PLC0415

            metrics = _collect_rig_metrics(cmds, roots)
        except ImportError:
            pass

        scope = metrics["metrics_scope"]
        counts = ": {} joint(s), {} control(s)".format(
            metrics["joint_count"], metrics["control_count"]
        )
        if scope == "rig":
            summary = "Built rig '{}' from guide '{}'{}".format(
                roots[0], result["guide_built"], counts
            )
        elif scope == "scene":
            summary = (
                "Built guide '{}' but the rig root could not be resolved "
                "(source: {}); counts below are scene-wide{}".format(
                    result["guide_built"], result["rig_root_source"], counts
                )
            )
        else:
            summary = "Built guide '{}'; counts unavailable outside Maya".format(
                result["guide_built"]
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
