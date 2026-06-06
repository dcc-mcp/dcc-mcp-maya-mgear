"""Export a Shifter guide or component as a reusable template file."""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def export_shifter_guide_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> dict:
    """Export a Shifter guide as a reusable template.

    Extracts the guide template dictionary from a guide node in the scene using
    mGear's ``get_guide_template_dict`` and writes it to a ``.sgt`` file or
    returns it as a base64-encoded JSON string.

    Args:
        guide_name: Name of the guide root node to export.
        output_path: File path for the exported template (``.sgt`` or ``.json``).
            Omit to return as base64-encoded JSON in the result context.
        include_metadata: Include scene metadata and annotations in the export.

    Returns:
        ToolResult dict with exported template data (file path or base64 content).
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
        import maya.cmds as cmds  # noqa: PLC0415
        import mgear.shifter.io as sio  # noqa: PLC0415

        # Validate guide exists
        if not cmds.objExists(guide_name):
            return skill_error(
                f"Guide not found: '{guide_name}'",
                f"'{guide_name}' does not exist in the scene",
                prompt="Use list_shifter_components to find available guides.",
            )

        # Check that the node is a valid guide element
        is_valid_guide = False
        for attr_name in ("isGearGuide", "ismodel", "comp_type"):
            try:
                if cmds.attributeQuery(attr_name, node=guide_name, exists=True):
                    is_valid_guide = True
                    break
            except Exception:  # noqa: BLE001
                pass

        if not is_valid_guide:
            return skill_error(
                f"Not a valid guide: '{guide_name}'",
                f"'{guide_name}' does not have mGear guide attributes (isGearGuide, ismodel, comp_type)",
                prompt="Select a valid Shifter guide node and try again.",
            )

        # Select the guide node (mgear io functions work with selection)
        cmds.select(guide_name, replace=True)

        # Get the guide template dict using real mGear API
        import mgear.pymaya as pm  # noqa: PLC0415

        meta: Optional[Dict[str, Any]] = None
        if include_metadata:
            meta = {
                "maya_version": cmds.about(version=True),
                "scene_name": cmds.file(query=True, sceneName=True) or "unsaved",
                "exported_guide": guide_name,
            }

        # mgear.shifter.io.get_guide_template_dict(guide_node, meta)
        guide_pynode = pm.PyNode(guide_name)
        template_dict = sio.get_guide_template_dict(guide_pynode, meta=meta)

        if template_dict is None:
            return skill_error(
                "Failed to export guide template",
                "get_guide_template_dict returned None",
                prompt="Verify the selected node is a valid guide root.",
            )

        # Serialize to JSON
        json_str = json.dumps(template_dict, indent=4, sort_keys=True, default=str)

        # Export to file or base64
        if output_path:
            output_path = os.path.expandvars(os.path.expanduser(output_path))
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # If the path ends with .sgt, use mGear's native export
            if output_path.endswith(".sgt"):
                sio.export_guide_template(filePath=output_path, conf=template_dict)
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(json_str)

            return skill_success(
                f"Exported guide '{guide_name}' template to {output_path}",
                prompt="The template file can be imported with mgear.shifter.io.import_guide_template.",
                guide_name=guide_name,
                output_path=output_path,
                file_size_bytes=len(json_str),
                format="sgt" if output_path.endswith(".sgt") else "json",
            )

        # Return as base64
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
        return skill_success(
            f"Exported guide '{guide_name}' template as base64",
            prompt="Decode the base64 content to get the JSON template dict.",
            guide_name=guide_name,
            base64_content=encoded,
            content_length=len(json_str),
            encoding="base64",
            format="json",
        )

    except Exception as exc:
        return skill_exception(
            exc,
            message=f"Failed to export guide '{guide_name}'",
            possible_solutions=[
                "Verify the node is a valid Shifter guide root",
                "Check write permissions for the output path",
                "Ensure the guide has not been partially deleted",
            ],
        )


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`export_shifter_guide_template`."""
    return export_shifter_guide_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
