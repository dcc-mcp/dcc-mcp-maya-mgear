"""Create a Shifter guide from a named template at a specified location."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _create_guide(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Shifter guide via draw_comp() — the real mGear guide creation API."""
    import mgear.shifter.guide_manager as gui_mgr

    pos = position if position else [0.0, 0.0, 0.0]
    params = parameters if parameters else {}

    # draw_comp() — verified real mGear API (guide_manager.py:24-42)
    # Underlying call chain: draw_comp → Rig.drawNewComponent (guide.py:1204+)
    guide = gui_mgr.draw_comp(
        comp_type=template,
        name=guide_name,
        parent=parent_guide,
        pos=pos,
        **params,
    )

    result: Dict[str, Any] = {"guide_name": guide_name, "template": template, "position": pos}
    if guide:
        result["node"] = str(guide)
    return result


def create_shifter_guide_from_template(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Shifter guide from a named template.

    Args:
        guide_name: Name for the new guide.
        template: Component template name (e.g. "arm_2jnt_01", "leg_2jnt_01").
        position: World-space position [x, y, z]. Defaults to origin.
        parent_guide: Optional parent guide name for hierarchy.
        parameters: Additional template-specific parameters.
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

        result = _create_guide(
            guide_name=guide_name,
            template=template,
            position=position,
            parent_guide=parent_guide,
            parameters=parameters,
        )

        if result.get("node"):
            return skill_success(
                "Created guide '{}' from template '{}'".format(guide_name, template),
                **result,
                prompt="Use build_shifter_rig to generate the rig from this guide.",
            )
        else:
            return skill_success(
                "Created guide '{}' from template '{}' (deferred)".format(guide_name, template),
                **result,
                prompt="Guide node was not returned synchronously; it may be pending creation.",
            )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create Shifter guide from template")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`create_shifter_guide_from_template`."""
    return create_shifter_guide_from_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
