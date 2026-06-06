"""Inspect mGear availability, version, key modules, and environment diagnostics."""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def _get_mgear_version(mgear: Any) -> str:
    for attr in ("__version__", "version", "VERSION"):
        v = getattr(mgear, attr, None)
        if v is not None:
            return str(v)
    return "unknown"


def inspect_mgear_environment(verbose: bool = False) -> Dict[str, Any]:
    """Inspect the mGear environment — availability, version, and diagnostics.

    Args:
        verbose: Include detailed module paths and extra diagnostic information.
    """
    try:
        try:
            import mgear
        except ImportError:
            mgear = None

        try:
            import mgear.shifter  # noqa: F401

            shifter_available = True
        except ImportError:
            shifter_available = False

        mgear_available = mgear is not None

        context: Dict[str, Any] = {
            "mgear_available": mgear_available,
            "shifter_available": shifter_available,
            "python_version": sys.version,
        }

        if mgear_available:
            version = _get_mgear_version(mgear)
            context["version"] = version

            mgear_path = (
                getattr(mgear, "__path__", [getattr(mgear, "__file__", "")])
                if hasattr(mgear, "__path__")
                else [getattr(mgear, "__file__", "")]
            )
            context["mgear_path"] = list(mgear_path) if isinstance(mgear_path, (list, tuple)) else str(mgear_path)

            if verbose:
                key_modules: Dict[str, bool] = {}
                for mod in (
                    "mgear.core",
                    "mgear.shifter",
                    "mgear.shifter.component",
                    "mgear.shifter.guide",
                    "mgear.shifter.rig",
                    "mgear.anim_picker",
                ):
                    key_modules[mod] = _module_available(mod)
                context["key_modules"] = key_modules
                context["maya_available"] = _module_available("maya.cmds")
                context["maya_version"] = os.environ.get("MAYA_VERSION", "unknown")
        else:
            context["maya_available"] = _module_available("maya.cmds")

        # Check for mgear via env vars
        mgear_root = os.environ.get("MGEAR_ROOT") or os.environ.get("MGEAR_PATH")
        if mgear_root:
            context["mgear_root"] = mgear_root

        if mgear_available and shifter_available:
            return skill_success(
                "mGear {} available with Shifter".format(context.get("version", "")),
                **context,
            )
        elif mgear_available:
            return skill_success(
                "mGear {} found but Shifter module is not available".format(context.get("version", "")),
                **context,
                prompt="Verify mgear.shifter is installed or check your mGear installation.",
            )
        else:
            return skill_error(
                "mGear is not installed in this environment",
                "ImportError: No module named 'mgear'",
                prompt="Install mGear (https://github.com/mgear-dev/mgear) or ensure it is on PYTHONPATH.",
                possible_solutions=[
                    "pip install mgear",
                    "Set MGEAR_ROOT environment variable",
                    "Add mGear to your Maya PYTHONPATH",
                ],
                **context,
            )
    except Exception as exc:
        return skill_exception(exc, message="Failed to inspect mGear environment")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`inspect_mgear_environment`."""
    return inspect_mgear_environment(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
