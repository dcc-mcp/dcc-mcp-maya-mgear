"""Export a Shifter guide or component as a reusable template file.

Real mGear API: ``mgear.shifter.io.export_guide_template(filePath, meta)``
(io.py:149-215).  The exported guide is determined by the current Maya
selection, not a name argument — the caller must select the guide first.
"""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _select_guide(guide_name: str) -> bool:
    """Select the named guide node in Maya.  Returns True on success."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return False
    try:
        cmds.select(guide_name, replace=True)
        return True
    except Exception:
        return False


def _export_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Export via the real ``mgear.shifter.io.export_guide_template(filePath, meta)`` API.

    *guide_name* is used to pre-select the target.  *output_path* maps to
    *filePath*.  *include_metadata* is passed as a ``meta`` dict key.
    """
    import mgear.shifter.io as shifter_io

    ok = _select_guide(guide_name)
    if not ok:
        return {
            "guide_name": guide_name,
            "error": "Guide '{}' not found in scene".format(guide_name),
        }

    meta = {"include_metadata": include_metadata}
    result: Dict[str, Any] = {
        "guide_name": guide_name,
        "include_metadata": include_metadata,
    }

    if output_path:
        shifter_io.export_guide_template(filePath=output_path, meta=meta)
        result["output_path"] = output_path
    else:
        fd, tmp_path = tempfile.mkstemp(suffix=".gct", prefix="mgear_export_")
        os.close(fd)
        try:
            shifter_io.export_guide_template(filePath=tmp_path, meta=meta)
            with open(tmp_path, "rb") as fh:
                result["template_base64"] = base64.b64encode(fh.read()).decode("ascii")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return result


def export_shifter_guide_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Export a Shifter guide or component as a reusable template.

    Args:
        guide_name: Name of the guide to export.  The tool selects this node
            in Maya before calling ``export_guide_template``.
        output_path: File path for the exported ``.gct`` template.  Omit to
            return a base64-encoded string.
        include_metadata: Passed through to the ``meta`` dict of the mGear
            export function.
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

        if result.get("error"):
            return skill_error(
                result["error"],
                "Guide '{}' selection failed".format(guide_name),
                prompt="Verify the guide name. Use list_shifter_components to see available guides.",
            )

        if output_path:
            msg = "Exported template to {}".format(output_path)
            return skill_success(msg, **result)
        else:
            has_base64 = (
                "template_base64" in result and result["template_base64"] is not None
            )
            if has_base64:
                b64_len = len(result["template_base64"])
                msg = "Exported template as base64 ({} chars)".format(b64_len)
            else:
                msg = "Export attempted but no data produced"
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
