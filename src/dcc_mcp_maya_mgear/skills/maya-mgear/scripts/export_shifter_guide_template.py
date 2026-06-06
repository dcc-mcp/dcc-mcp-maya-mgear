"""Export a Shifter guide or component as a reusable template file."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _export_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Export a Shifter guide template using the mGear API."""
    import mgear.shifter.template as tmpl_mod

    result: Dict[str, Any] = {"guide_name": guide_name, "include_metadata": include_metadata}

    # Preferred: TemplateManager class
    manager_class = getattr(tmpl_mod, "TemplateManager", None)
    if manager_class is not None:
        manager = manager_class()
        if hasattr(manager, "exportTemplate"):
            data = manager.exportTemplate(guide_name, include_metadata=include_metadata)
            if output_path:
                _write_template_file(output_path, data)
                result["output_path"] = output_path
            else:
                result["template_base64"] = _to_base64(data) if isinstance(data, (str, bytes)) else None
            return result

    # Fallback: module-level function
    if output_path:
        if hasattr(tmpl_mod, "exportGuideTemplate"):
            tmpl_mod.exportGuideTemplate(guide_name, output_path, metadata=include_metadata)
            result["output_path"] = output_path
        elif hasattr(tmpl_mod, "exportToFile"):
            tmpl_mod.exportToFile(guide_name, output_path)
            result["output_path"] = output_path
        else:
            result["output_path"] = None
            result["error"] = "No known export function available"
    else:
        if hasattr(tmpl_mod, "getTemplateData"):
            data = tmpl_mod.getTemplateData(guide_name)
            result["template_base64"] = _to_base64(data) if data else None
        elif hasattr(tmpl_mod, "exportToString"):
            data = tmpl_mod.exportToString(guide_name)
            result["template_base64"] = _to_base64(data) if data else None
        else:
            result["template_base64"] = None
            result["error"] = "No known base64 export function available"

    return result


def _write_template_file(path: str, data: Any) -> None:
    """Write template data to a file."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    if isinstance(data, str):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data)
    elif isinstance(data, bytes):
        with open(path, "wb") as fh:
            fh.write(data)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(data))


def _to_base64(data: Any) -> str:
    """Encode data as base64."""
    if isinstance(data, bytes):
        return base64.b64encode(data).decode("ascii")
    if isinstance(data, str):
        return base64.b64encode(data.encode("utf-8")).decode("ascii")
    return base64.b64encode(str(data).encode("utf-8")).decode("ascii")


def export_shifter_guide_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Export a Shifter guide or component as a reusable template.

    Args:
        guide_name: Name of the guide or component to export.
        output_path: File path for the exported template. Omit to return as base64.
        include_metadata: Include metadata and annotations in the export.
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

        result = _export_template(guide_name, output_path, include_metadata)

        if output_path:
            msg = "Exported '{}' template to {}".format(guide_name, output_path)
            return skill_success(msg, **result)
        else:
            has_base64 = "template_base64" in result and result["template_base64"] is not None
            if has_base64:
                # Truncate base64 in message to keep it readable
                b64_len = len(result["template_base64"])
                msg = "Exported '{}' template as base64 ({} chars)".format(guide_name, b64_len)
            else:
                msg = "Export attempted for '{}', but no base64 data produced".format(guide_name)
            return skill_success(msg, **result)
    except Exception as exc:
        return skill_exception(exc, message="Failed to export Shifter guide template")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`export_shifter_guide_template`."""
    return export_shifter_guide_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
