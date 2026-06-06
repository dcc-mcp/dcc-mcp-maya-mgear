"""Export a Shifter guide or component as a reusable template file."""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _get_guide_export_data(guide_name: str) -> Dict[str, Any]:
    """Extract guide data for export from the current Maya scene.

    Args:
        guide_name: Name of the guide node to export.

    Returns:
        Dict with guide export data (attributes, children, connections).
    """
    import maya.cmds as cmds  # noqa: PLC0415

    if not cmds.objExists(guide_name):
        raise ValueError(f"Guide '{guide_name}' does not exist in the scene")

    export_data: Dict[str, Any] = {
        "guide_name": guide_name,
        "type": cmds.objectType(guide_name),
    }

    # Collect attributes
    attrs: Dict[str, Any] = {}
    for attr_name in cmds.listAttr(guide_name, keyable=True, scalar=True) or []:
        try:
            attrs[attr_name] = cmds.getAttr(f"{guide_name}.{attr_name}")
        except Exception:  # noqa: BLE001
            pass
    export_data["attributes"] = attrs

    # Collect children (guides often have nested transforms)
    children = cmds.listRelatives(guide_name, children=True, fullPath=False) or []
    export_data["children"] = children

    return export_data


def _export_via_mgear(guide_name: str) -> Dict[str, Any]:
    """Use mGear's native export mechanism if available, with fallback.

    Args:
        guide_name: Name of the guide or component to export.

    Returns:
        Dict with export data from mGear or scene extraction.

    Raises:
        ValueError: If the guide does not exist in the scene.
    """
    # Always validate existence first regardless of export method
    _get_guide_export_data(guide_name)

    import mgear.shifter.component as comp  # noqa: PLC0415

    guide_manager = getattr(comp, "guide_manager", None)
    if guide_manager is not None and hasattr(guide_manager, "exportGuideTemplate"):
        result = guide_manager.exportGuideTemplate(guide_name)
        # Merge mGear result with basic guide info
        merged = {
            "guide_name": guide_name,
            "mgear_export_result": str(result),
        }
        return merged

    # Fallback: extract data from scene (guide existence already validated)
    return _get_guide_export_data(guide_name)


def export_shifter_guide_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> dict:
    """Export a Shifter guide or component as a reusable template.

    Extracts guide data from the current Maya scene and writes it to a file
    or returns it as a base64-encoded string.  The exported template can be
    re-imported with ``create_shifter_guide_from_template`` on another scene.

    Args:
        guide_name: Name of the guide or component to export.
        output_path: File path for the exported template. Omit to return as
            base64-encoded JSON string in the result context.
        include_metadata: Include metadata and annotations in the export.

    Returns:
        ToolResult dict with exported template data.
    """
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
        export_data = _export_via_mgear(guide_name)

        if include_metadata:
            import maya.cmds as cmds  # noqa: PLC0415

            export_data["metadata"] = {
                "maya_version": cmds.about(version=True),
                "exported_from": cmds.file(query=True, sceneName=True) or "unsaved",
            }

        # Serialize to JSON
        json_str = json.dumps(export_data, indent=2, default=str)

        # Export to file or base64
        if output_path:
            output_path = os.path.expandvars(os.path.expanduser(output_path))
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            return skill_success(
                f"Exported guide '{guide_name}' template to {output_path}",
                prompt="The template file can be re-imported with create_shifter_guide_from_template.",
                guide_name=guide_name,
                output_path=output_path,
                file_size=len(json_str),
            )

        # Return as base64
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
        return skill_success(
            f"Exported guide '{guide_name}' template as base64",
            prompt="Decode the base64 content to get the JSON template.",
            guide_name=guide_name,
            base64_content=encoded,
            content_length=len(json_str),
            encoding="base64",
        )

    except ValueError as exc:
        return skill_error(
            str(exc),
            str(exc),
            prompt="Use list_shifter_components to find available guides.",
        )
    except Exception as exc:
        return skill_exception(
            exc,
            message=f"Failed to export guide '{guide_name}'",
            possible_solutions=[
                "Verify the guide exists in the scene",
                "Check write permissions for the output path",
                "Ensure the guide has valid mGear attributes",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`export_shifter_guide_template`."""
    return export_shifter_guide_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
