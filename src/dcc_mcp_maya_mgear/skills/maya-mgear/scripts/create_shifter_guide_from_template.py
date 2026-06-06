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
    """Create a Shifter guide using the mGear API."""
    import mgear.shifter.guide as guide_mod

    pos = position if position else [0.0, 0.0, 0.0]

    # Preferred: GuideManager.createGuideFromTemplate
    manager_class = getattr(guide_mod, "GuideManager", None)
    if manager_class is not None:
        manager = manager_class()
        if hasattr(manager, "createGuide"):
            guide = manager.createGuide(
                guideName=guide_name,
                template=template,
                position=pos,
                parent=parent_guide,
                **parameters if parameters else {},
            )
            result = {"guide_name": guide_name, "template": template, "position": pos}
            if guide:
                result["node"] = str(guide)
            return result

    # Fallback: direct module-level function
    if hasattr(guide_mod, "createGuideFromTemplate"):
        guide = guide_mod.createGuideFromTemplate(
            guideName=guide_name,
            templateName=template,
            pos=pos,
            parent=parent_guide,
            **parameters if parameters else {},
        )
        result = {"guide_name": guide_name, "template": template, "position": pos}
        if guide:
            result["node"] = str(guide)
        return result

    # Fallback: legacy API
    if hasattr(guide_mod, "addGuide"):
        guide = guide_mod.addGuide(name=guide_name, template=template, pos=pos)
        return {"guide_name": guide_name, "template": template, "position": pos, "node": str(guide) if guide else None}

    return {"guide_name": guide_name, "template": template, "position": pos, "node": None}


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
        template: Component template name (e.g. "spine", "arm", "leg").
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

        return skill_success(
            "Created guide '{}' from template '{}'".format(guide_name, template),
            **result,
            prompt="Use build_shifter_rig to generate the rig from this guide.",
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
