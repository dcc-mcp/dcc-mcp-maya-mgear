"""Build a rig from an existing Shifter guide in the scene."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _build_rig(guide_name: Optional[str], build_type: str) -> Dict[str, Any]:
    """Build a rig using the mGear Shifter API."""
    import mgear.shifter.rig as rig_mod

    result: Dict[str, Any] = {"build_type": build_type, "built_guides": []}

    # Preferred: Rigger class
    rigger_class = getattr(rig_mod, "Rigger", None)
    if rigger_class is not None:
        rigger = rigger_class()
        if build_type == "preview":
            if hasattr(rigger, "buildPreview"):
                built = rigger.buildPreview(guide_name) if guide_name else rigger.buildPreviewAll()
                result["built_guides"] = [str(b) for b in built] if built else []
            elif hasattr(rigger, "build"):
                built = rigger.build(guide_name, mode="preview") if guide_name else rigger.buildAll(mode="preview")
                result["built_guides"] = [str(b) for b in built] if built else []
            else:
                built = rigger.build(guide_name) if guide_name else rigger.buildAll()
                result["built_guides"] = [str(b) for b in built] if built else []
        else:
            if hasattr(rigger, "build"):
                built = rigger.build(guide_name) if guide_name else rigger.buildAll()
                result["built_guides"] = [str(b) for b in built] if built else []
            elif hasattr(rigger, "buildFull"):
                built = rigger.buildFull(guide_name) if guide_name else rigger.buildFullAll()
                result["built_guides"] = [str(b) for b in built] if built else []

        result["guide_built"] = guide_name or "all"
        return result

    # Fallback: module-level function
    if guide_name:
        if hasattr(rig_mod, "buildRig"):
            built = rig_mod.buildRig(guide_name, mode=build_type)
            result["built_guides"] = [str(built)] if built else []
        elif hasattr(rig_mod, "build"):
            built = rig_mod.build(guide_name)
            result["built_guides"] = [str(built)] if built else []
    else:
        if hasattr(rig_mod, "buildAllRigs"):
            built = rig_mod.buildAllRigs(mode=build_type)
            result["built_guides"] = [str(b) for b in built] if built else []
        elif hasattr(rig_mod, "buildAll"):
            built = rig_mod.buildAll()
            result["built_guides"] = [str(b) for b in built] if built else []

    result["guide_built"] = guide_name or "all"
    return result


def build_shifter_rig(
    guide_name: Optional[str] = None,
    build_type: str = "full",
) -> Dict[str, Any]:
    """Build a rig from an existing Shifter guide in the scene.

    Args:
        guide_name: Name of the guide to build from. Builds all guides if not specified.
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
