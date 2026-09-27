"""Export a built mGear Shifter rig (and its animation) to FBX or Alembic.

``build_shifter_rig`` creates the rig but nothing in the tool surface could
write the result to disk and prove it landed there.  This tool closes that
gap: it resolves the rig root, exports the requested frame range, reads the
file back, and returns verifiable metrics (byte size plus joint / control /
mesh / keyframe counts) so an agent can assert on the export instead of
trusting the exporter's return code.

Real Maya APIs used:

- ``maya.cmds.playbackOptions(query=True, minTime=True|maxTime=True)``
- ``maya.cmds.pluginInfo(plugin, query=True, loaded=True)`` / ``loadPlugin``
- ``maya.mel.eval("FBXExportBakeComplexStart -v <frame>")`` then
  ``FBXExport -f "<path>" -s`` (``-s`` exports the current selection)
- ``maya.cmds.AbcExport(j="-frameRange <sf> <ef> -root <node> -file <path>")``
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

FORMAT_FBX = "fbx"
FORMAT_ABC = "abc"

_FORMAT_EXTENSIONS: Dict[str, str] = {FORMAT_FBX: ".fbx", FORMAT_ABC: ".abc"}

_FORMAT_PLUGINS: Dict[str, Tuple[str, ...]] = {
    FORMAT_FBX: ("fbxmaya",),
    FORMAT_ABC: ("AbcExport", "AbcImport"),
}

# Attributes mGear writes on a built rig root.  Releases differ on the exact
# spelling, so every known name is probed in order before falling back to the
# selection and finally to a naming heuristic.
_RIG_ROOT_ATTRIBUTES: Tuple[str, ...] = (
    "is_rig",
    "gear_rig",
    "isGearRig",
    "mgear_rig",
    "rig_root",
)

_RIG_NAME_SUFFIXES: Tuple[str, ...] = ("_rig", "_rig_grp")


def _normalize_path(path: str) -> str:
    """Expand env vars / user home and normalise separators for Maya."""
    return os.path.expandvars(os.path.expanduser(path)).replace("\\", "/")


def _human_size(num_bytes: int) -> str:
    """Render a byte count for human-facing messages."""
    size = float(num_bytes)
    unit = "B"
    for candidate in ("B", "KB", "MB", "GB"):
        unit = candidate
        if size < 1024.0 or candidate == "GB":
            break
        size /= 1024.0
    if unit == "B":
        return "{:.0f} {}".format(size, unit)
    return "{:.1f} {}".format(size, unit)


def _resolve_format(file_path: str, file_format: Optional[str]) -> Optional[str]:
    """Return the effective export format, or None when it is unsupported.

    ``file_format`` wins when it names a known format; otherwise the format is
    inferred from the file extension, falling back to FBX.
    """
    if file_format:
        fmt = str(file_format).lower().lstrip(".")
        if fmt in _FORMAT_EXTENSIONS:
            return fmt
        if fmt in ("alembic",):
            return FORMAT_ABC
        return None

    ext = os.path.splitext(file_path)[1].lower()
    for known_fmt, known_ext in _FORMAT_EXTENSIONS.items():
        if ext == known_ext:
            return known_fmt
    return FORMAT_FBX


def _with_extension(file_path: str, fmt: str) -> str:
    """Give *file_path* the canonical extension for *fmt*.

    An extension belonging to another supported format is replaced
    (``rig.abc`` + ``fbx`` -> ``rig.fbx``); anything else is kept and the
    canonical extension is appended.
    """
    ext = _FORMAT_EXTENSIONS[fmt]
    root, current = os.path.splitext(file_path)
    if current.lower() == ext:
        return file_path
    if current.lower() in set(_FORMAT_EXTENSIONS.values()):
        return root + ext
    return file_path + ext


def _ensure_plugins(cmds: Any, fmt: str) -> List[str]:
    """Load the Maya plug-ins required by *fmt*; returns the ones loaded."""
    loaded: List[str] = []
    for plugin in _FORMAT_PLUGINS.get(fmt, ()):
        try:
            if not cmds.pluginInfo(plugin, query=True, loaded=True):
                cmds.loadPlugin(plugin)
                loaded.append(plugin)
        except Exception:  # noqa: BLE001 - plug-in already loaded / unavailable
            continue
    return loaded


def _find_rig_roots(cmds: Any) -> Tuple[List[str], str]:
    """Auto-detect built rig roots.  Returns (roots, detection_method)."""
    for attr in _RIG_ROOT_ATTRIBUTES:
        try:
            found = cmds.ls("*.{}".format(attr), type="transform", long=True) or []
        except Exception:  # noqa: BLE001 - malformed pattern, keep probing
            continue
        if found:
            return [str(n) for n in found], "attribute:{}".format(attr)

    try:
        selection = cmds.ls(selection=True, long=True, type="transform") or []
    except Exception:  # noqa: BLE001 - selection query can fail on odd scenes
        selection = []
    if selection:
        return [str(n) for n in selection], "selection"

    try:
        assemblies = cmds.ls(assemblies=True, long=True) or []
    except Exception:  # noqa: BLE001
        assemblies = []
    heuristic: List[str] = []
    for node in assemblies:
        name = str(node).rsplit("|", 1)[-1]
        if not name.lower().endswith(_RIG_NAME_SUFFIXES):
            continue
        try:
            owns_joints = cmds.ls(node, dag=True, type="joint") or []
        except Exception:  # noqa: BLE001
            owns_joints = []
        if owns_joints:
            heuristic.append(str(node))
    if heuristic:
        return heuristic, "name_heuristic"

    return [], "none"


def _resolve_roots(
    cmds: Any,
    rig_root: Optional[str],
    objects: Optional[List[str]],
) -> Tuple[Optional[List[str]], str, str]:
    """Resolve what to export.

    Returns ``(roots, detection_method, error)`` — exactly one of *roots* and
    *error* is set.
    """
    if objects:
        missing = [str(o) for o in objects if not cmds.objExists(o)]
        if missing:
            return (
                None,
                "explicit_objects",
                "Node(s) not found: {}".format(", ".join(missing)),
            )
        return [str(o) for o in objects], "explicit_objects", ""

    if rig_root:
        if not cmds.objExists(rig_root):
            return None, "explicit_rig_root", "Rig root '{}' not found".format(rig_root)
        return [str(rig_root)], "explicit_rig_root", ""

    roots, method = _find_rig_roots(cmds)
    if not roots:
        return None, method, "No rig root found in the scene"
    return roots, method, ""


def _collect_metrics(cmds: Any, roots: List[str]) -> Dict[str, int]:
    """Count the scene contents that make an export verifiable.

    Controls are counted as the distinct transforms owning a ``nurbsCurve``
    shape, which is how mGear builds its animatable controls.
    """
    metrics = {
        "joint_count": 0,
        "control_count": 0,
        "mesh_count": 0,
        "transform_count": 0,
        "keyframe_count": 0,
    }
    if not roots:
        return metrics

    try:
        metrics["joint_count"] = len(
            cmds.ls(*roots, dag=True, type="joint", long=True) or []
        )
        metrics["transform_count"] = len(
            cmds.ls(*roots, dag=True, type="transform", long=True) or []
        )
        metrics["mesh_count"] = len(
            cmds.ls(*roots, dag=True, type="mesh", long=True) or []
        )
        curves = cmds.ls(*roots, dag=True, type="nurbsCurve", long=True) or []
        metrics["control_count"] = len(
            {c.rsplit("|", 1)[0] for c in curves if "|" in c}
        )
    except Exception:  # noqa: BLE001 - metrics are advisory, never fatal
        return metrics

    try:
        metrics["keyframe_count"] = _coerce_keyframe_count(
            cmds.keyframe(*roots, query=True, keyframeCount=True, hierarchy="below")
        )
    except Exception:  # noqa: BLE001 - unanimated rigs have no keyframes
        metrics["keyframe_count"] = 0

    return metrics


def _coerce_keyframe_count(raw: Any) -> int:
    """Normalise ``cmds.keyframe(keyframeCount=True)`` to a single integer.

    Maya returns a scalar for one target and a list of per-target counts for
    several, so ``int(raw)`` alone would raise ``TypeError`` on the list form
    and silently report zero keyframes for an animated rig.
    """
    if raw is None:
        return 0
    if isinstance(raw, (list, tuple)):
        total = 0
        for item in raw:
            try:
                total += int(item)
            except (TypeError, ValueError):
                continue
        return total
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _resolve_frame_range(
    cmds: Any,
    start_frame: Optional[float],
    end_frame: Optional[float],
) -> Tuple[float, float, str]:
    """Return ``(start, end, source)`` for the export range."""
    if start_frame is not None and end_frame is not None:
        return float(start_frame), float(end_frame), "explicit"

    try:
        timeline_start = cmds.playbackOptions(query=True, minTime=True)
        timeline_end = cmds.playbackOptions(query=True, maxTime=True)
    except Exception:  # noqa: BLE001 - no UI/timeline (batch mode)
        timeline_start, timeline_end = 1.0, 1.0

    sf = float(start_frame) if start_frame is not None else float(timeline_start)
    ef = float(end_frame) if end_frame is not None else float(timeline_end)
    return sf, ef, "timeline"


def _current_selection(cmds: Any) -> List[str]:
    """Snapshot the current Maya selection (best effort)."""
    try:
        return list(cmds.ls(selection=True, long=True) or [])
    except Exception:  # noqa: BLE001 - selection is cosmetic, never fatal
        return []


def _restore_selection(cmds: Any, selection: List[str]) -> None:
    """Put back what :func:`_current_selection` captured.

    Exporting must not silently drop the artist's selection.
    """
    try:
        if selection:
            existing = [n for n in selection if cmds.objExists(n)]
            cmds.select(existing, replace=True)
        else:
            cmds.select(clear=True)
    except Exception:  # noqa: BLE001 - never fail an export over this
        pass


def _discard_previous_export(file_path: str) -> Optional[float]:
    """Delete a stale file at *file_path* so the read-back cannot hit it.

    Returns the previous mtime when the file existed, so a file that could
    not be deleted can still be detected as unchanged after the export.
    """
    try:
        if not os.path.isfile(file_path):
            return None
        prior_mtime = os.path.getmtime(file_path)
    except OSError:
        return None
    try:
        os.remove(file_path)
    except OSError:
        # Locked / read-only: keep the mtime and compare after the export.
        pass
    return prior_mtime


def _export_fbx(
    mel: Any,
    file_path: str,
    start_frame: float,
    end_frame: float,
    bake_animation: bool,
) -> None:
    """Run the FBX export MEL sequence for the current selection."""
    mel.eval("FBXExportBakeComplexAnimation -v {};".format(1 if bake_animation else 0))
    mel.eval("FBXExportBakeComplexStart -v {};".format(int(start_frame)))
    mel.eval("FBXExportBakeComplexEnd -v {};".format(int(end_frame)))
    mel.eval('FBXExport -f "{}" -s;'.format(file_path))


def _quote_job_value(value: str) -> str:
    """Quote a value for the AbcExport job string.

    The job string is split on whitespace, so an unquoted path or DAG name
    containing a space (a Windows profile directory, for example) silently
    becomes two arguments.
    """
    return '"{}"'.format(str(value).replace('"', ""))


def _export_abc(
    cmds: Any,
    file_path: str,
    roots: List[str],
    start_frame: float,
    end_frame: float,
) -> None:
    """Run the Alembic export job for *roots* over the frame range."""
    job_parts = ["-frameRange", str(int(start_frame)), str(int(end_frame))]
    for root in roots:
        job_parts.extend(["-root", _quote_job_value(root)])
    job_parts.extend(["-worldSpace", "-writeVisibility", "-uvWrite"])
    job_parts.extend(["-file", _quote_job_value(file_path)])
    cmds.AbcExport(j=" ".join(job_parts))


def _probe_mgear() -> Dict[str, Any]:
    """Report mGear availability — advisory context for the export result."""
    context: Dict[str, Any] = {"available": False}
    try:
        import mgear  # noqa: PLC0415
    except ImportError:
        return context

    context["available"] = True
    for attr in ("__version__", "version", "VERSION"):
        version = getattr(mgear, attr, None)
        if version is not None:
            context["version"] = str(version)
            break
    try:
        import mgear.shifter  # noqa: F401, PLC0415

        context["shifter_available"] = True
    except ImportError:
        context["shifter_available"] = False
    return context


def export_shifter_rig(
    file_path: str,
    rig_root: Optional[str] = None,
    objects: Optional[List[str]] = None,
    file_format: Optional[str] = None,
    start_frame: Optional[float] = None,
    end_frame: Optional[float] = None,
    bake_animation: bool = True,
) -> Dict[str, Any]:
    """Export a built Shifter rig (with animation) to FBX or Alembic.

    Args:
        file_path: Destination file path.  Parent directories are created;
            the canonical extension is appended when it is missing.
        rig_root: Name of the built rig root to export.  Auto-detected when
            omitted.
        objects: Explicit nodes to export.  Takes precedence over
            ``rig_root`` when both are supplied.
        file_format: ``"fbx"`` or ``"abc"``.  Omit to infer it from the
            file extension, defaulting to FBX when the extension is silent.
        start_frame: Export start frame; defaults to the timeline start.
        end_frame: Export end frame; defaults to the timeline end.
        bake_animation: Bake complex animation into the FBX range (FBX only).

    Returns:
        ToolResult dict.  On success the context carries ``file_size_bytes``
        plus the joint / control / mesh / keyframe counts read back from the
        scene, so the export can be asserted on instead of trusted.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
        from maya import mel  # noqa: PLC0415
    except ImportError:
        return skill_error(
            "Maya not available",
            "maya.cmds could not be imported",
            possible_solutions=["Run this skill inside Maya or mayapy"],
        )

    try:
        if not file_path or not str(file_path).strip():
            return skill_error(
                "Missing file_path",
                "missing_file_path",
                possible_solutions=[
                    "Pass an absolute destination path such as /tmp/rig.fbx"
                ],
            )

        fmt = _resolve_format(str(file_path), file_format)
        if fmt is None:
            return skill_error(
                "Unsupported export format: {}".format(file_format or "unknown"),
                "unsupported_format",
                prompt="Use 'fbx' or 'abc'.",
                file_path=str(file_path),
                file_format=str(file_format),
                supported_formats=sorted(_FORMAT_EXTENSIONS),
            )

        target_path = _with_extension(_normalize_path(str(file_path)), fmt)

        roots, detection_method, error = _resolve_roots(cmds, rig_root, objects)
        if error:
            return skill_error(
                error,
                "rig_root_not_resolved",
                prompt=(
                    "Build a rig with build_shifter_rig, or pass rig_root / "
                    "objects explicitly."
                ),
                file_path=target_path,
                detection_method=detection_method,
            )

        parent_dir = os.path.dirname(os.path.abspath(target_path))
        try:
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        except OSError as exc:
            return skill_error(
                "Output directory is not writable: {}".format(parent_dir),
                "output_directory_error",
                prompt="Choose a path under an existing writable directory.",
                file_path=target_path,
                detail=str(exc),
            )

        sf, ef, range_source = _resolve_frame_range(cmds, start_frame, end_frame)
        # Both exporters are handed whole frames (the FBX bake MEL commands
        # take integers), so report exactly what was sent instead of the
        # unrounded input.
        export_start, export_end = int(round(sf)), int(round(ef))
        plugins_loaded = _ensure_plugins(cmds, fmt)

        # A previous export at this path would otherwise satisfy the read-back
        # even if this run's exporter silently failed (MEL reports errors
        # without raising).  Remove it first; if it cannot be removed (locked
        # file on Windows) fall back to comparing mtimes.
        prior_mtime = _discard_previous_export(target_path)

        metrics = _collect_metrics(cmds, roots)

        # Selection drives the FBX exporter; ABC is told the roots explicitly.
        previous_selection = _current_selection(cmds)
        try:
            cmds.select(roots, replace=True)
            if fmt == FORMAT_FBX:
                _export_fbx(mel, target_path, export_start, export_end, bake_animation)
            else:
                _export_abc(cmds, target_path, roots, export_start, export_end)
        finally:
            _restore_selection(cmds, previous_selection)

        # Read the export back — a zero-byte, missing, or untouched file is a
        # failure even when the exporter reported no error.
        file_exists = os.path.isfile(target_path)
        file_size = os.path.getsize(target_path) if file_exists else 0
        reused_existing = (
            file_exists
            and prior_mtime is not None
            and os.path.getmtime(target_path) == prior_mtime
        )
        if not file_exists or file_size == 0 or reused_existing:
            return skill_error(
                "Export produced no file: {}".format(target_path),
                "empty_export",
                prompt=(
                    "Check the Maya script editor for exporter errors and verify "
                    "the rig root still exists."
                ),
                file_path=target_path,
                file_format=fmt,
                file_exists=file_exists,
                file_size_bytes=file_size,
                reused_existing_file=reused_existing,
                rig_roots=roots,
                detection_method=detection_method,
                start_frame=export_start,
                end_frame=export_end,
            )

        return skill_success(
            "Exported {} root(s) to {} ({} — {} joints, {} controls, frames "
            "{}-{})".format(
                len(roots),
                os.path.basename(target_path),
                _human_size(file_size),
                metrics["joint_count"],
                metrics["control_count"],
                export_start,
                export_end,
            ),
            file_path=target_path,
            file_format=fmt,
            file_size_bytes=file_size,
            file_size_human=_human_size(file_size),
            rig_roots=roots,
            detection_method=detection_method,
            frame_range_source=range_source,
            start_frame=export_start,
            end_frame=export_end,
            selection_restored=True,
            plugins_loaded=plugins_loaded,
            mgear=_probe_mgear(),
            **metrics,
            prompt=(
                "Re-import with mgear_import_to_scene to round-trip check the "
                "export, or compare joint/control counts against build_shifter_rig."
            ),
        )
    except Exception as exc:
        return skill_exception(exc, message="Failed to export Shifter rig")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`export_shifter_rig`."""
    return export_shifter_rig(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
