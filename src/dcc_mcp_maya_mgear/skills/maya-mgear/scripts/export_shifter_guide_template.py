"""Export a Shifter guide or component as a reusable template file."""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _export_template(
    guide_name: str,
    output_path: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Export a Shifter guide template via the real mGear io API."""
    import mgear.shifter.io as shifter_io

    result: Dict[str, Any] = {"guide_name": guide_name, "include_metadata": include_metadata}

    if output_path:
        # export_guide_template() — verified real mGear API (io.py:149-215)
        shifter_io.export_guide_template(guide_name, output_path)
        result["output_path"] = output_path
    else:
        # Write to a temp file, read back as base64
        fd, tmp_path = tempfile.mkstemp(suffix=".gct", prefix="mgear_export_")
        os.close(fd)
        try:
            shifter_io.export_guide_template(guide_name, tmp_path)
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
