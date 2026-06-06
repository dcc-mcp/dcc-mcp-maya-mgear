"""Inspect mGear availability, version, key modules, and environment diagnostics."""

from __future__ import annotations

import importlib.util
import sys
from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_success


def _module_available(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:  # noqa: BLE001
        return False


def _get_module_version(module_name: str) -> Optional[str]:
    """Attempt to retrieve the version of a module."""
    try:
        mod = importlib.import_module(module_name)
        for attr in ("__version__", "version", "VERSION"):
            if hasattr(mod, attr):
                return str(getattr(mod, attr))
    except Exception:  # noqa: BLE001
        pass
    return None


def _get_module_path(module_name: str) -> Optional[str]:
    """Get the file path of an installed module."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return spec.origin
    except Exception:  # noqa: BLE001
        pass
    return None


def _get_mgear_components() -> Dict[str, Any]:
    """Attempt to introspect mgear.shifter components."""
    result: Dict[str, Any] = {
        "mgear_available": False,
        "shifter_available": False,
        "version": None,
        "components_count": 0,
    }

    if not _module_available("mgear"):
        return result

    result["mgear_available"] = True
    result["version"] = _get_module_version("mgear")

    if not _module_available("mgear.shifter"):
        return result

    result["shifter_available"] = True

    try:
        import mgear.shifter.component as comp  # noqa: PLC0415

        guide_manager = getattr(comp, "guide_manager", None)
        if guide_manager is not None and hasattr(guide_manager, "componentTypes"):
            component_types = guide_manager.componentTypes
            if isinstance(component_types, dict):
                result["components_count"] = len(component_types)
                result["component_types"] = sorted(component_types.keys())
    except Exception:  # noqa: BLE001
        pass

    return result


def inspect_mgear_environment(
    verbose: bool = False,
) -> dict:
    """Inspect mGear availability, version, key modules, and environment diagnostics.

    Checks whether mGear and mGear Shifter are importable in the current Maya
    Python environment and reports version, component type counts, and optional
    module path details.

    Args:
        verbose: When True, include detailed module paths and diagnostic info.

    Returns:
        ToolResult dict with mGear environment details.
    """
    try:
        # Collect core diagnostics
        mgear_info = _get_mgear_components()

        context: Dict[str, Any] = {
            "python_version": sys.version,
            "maya_available": _module_available("maya.cmds"),
        }

        # Maya version if available
        if context["maya_available"]:
            try:
                import maya.cmds as cmds  # noqa: PLC0415

                context["maya_version"] = cmds.about(version=True)
            except Exception:  # noqa: BLE001
                context["maya_version"] = None

        context.update(mgear_info)

        # Verbose diagnostics
        if verbose:
            module_paths = {}
            for mod_name in ("mgear", "mgear.shifter", "mgear.shifter.component"):
                path = _get_module_path(mod_name)
                if path:
                    module_paths[mod_name] = path
            if module_paths:
                context["module_paths"] = module_paths

            # Python path context
            context["python_path"] = sys.path[:10]  # first 10 entries only

        if mgear_info["mgear_available"]:
            comp_count = mgear_info.get("components_count", 0)
            msg = (
                f"mGear {mgear_info.get('version', '(unknown version)')} detected "
                f"with {comp_count} Shifter component type(s)"
            )
            prompt = "Use list_shifter_components to enumerate available component types."
        else:
            msg = "mGear is not available in this environment"
            prompt = "Install mGear from https://github.com/mgear-dev/mgear to use Shifter tools."
            context["possible_solutions"] = [
                "Install mGear: pip install mgear",
                "Verify Maya's Python environment includes the mGear module path",
                "Check that mGear is loaded in Maya's script editor",
            ]

        return skill_success(msg, prompt=prompt, **context)

    except Exception as exc:
        from dcc_mcp_core.skill import skill_exception

        return skill_exception(exc, message="Failed to inspect mGear environment")


@skill_entry
def main(**kwargs) -> dict:
    """Entry point; delegates to :func:`inspect_mgear_environment`."""
    return inspect_mgear_environment(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
