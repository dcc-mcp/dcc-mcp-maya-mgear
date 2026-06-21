"""Import an asset into the current Maya scene with mGear rigging context awareness.

Consumes the shared ``dcc_mcp_core.asset_import`` contract and dispatches to
the appropriate format-specific importer (FBX, OBJ, USD, USDZ, GLTF, GLB,
ABC).  After the import completes, the script probes the mGear environment and
reports any active Shifter rig components so downstream agents understand the
rigging context.

Contract pattern
----------------
Follows the same structure as the ``maya-import-to-scene``, ``blender-import-to-scene``,
and ``houdini-import-to-scene`` implementations in the respective DCC adapter repos.
The only variance is the post-import mGear context probe.
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# Import local modules
from dcc_mcp_core.asset_import import (
    AssetDescriptor,
    AssetFileVariant,
    AssetFormat,
    ImportToSceneRequest,
    ImportToSceneResult,
    ImportWarning,
    ImportWarningCode,
    PlacementHint,
)
from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------

_EXTENSION_TO_FORMAT: Dict[str, str] = {
    ".fbx": AssetFormat.FBX,
    ".obj": AssetFormat.OBJ,
    ".usd": AssetFormat.USD,
    ".usda": AssetFormat.USD,
    ".usdc": AssetFormat.USD,
    ".usdz": AssetFormat.USDZ,
    ".gltf": AssetFormat.GLTF,
    ".glb": AssetFormat.GLB,
    ".abc": AssetFormat.ABC,
}

_FORMAT_PLUGINS: Dict[str, Tuple[str, ...]] = {
    AssetFormat.FBX: ("fbxmaya",),
    AssetFormat.OBJ: ("objExport",),
    AssetFormat.USD: ("mayaUsdPlugin",),
    AssetFormat.USDZ: ("mayaUsdPlugin",),
    AssetFormat.GLTF: ("glTFPlugin",),
    AssetFormat.GLB: ("glTFPlugin",),
    AssetFormat.ABC: ("AbcImport",),
}

_FORMAT_PRIORITY: Dict[str, int] = {
    AssetFormat.FBX: 0,
    AssetFormat.OBJ: 1,
    AssetFormat.USD: 2,
    AssetFormat.USDZ: 3,
    AssetFormat.GLTF: 4,
    AssetFormat.GLB: 5,
    AssetFormat.ABC: 6,
}


def _normalize_path(path: str) -> str:
    """Expand env vars / user home and normalise separators."""
    return os.path.expandvars(os.path.expanduser(path)).replace("\\", "/")


_NAMESPACE_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_]")


def _make_namespace(asset_id: str) -> str:
    """Build a Maya-safe namespace from *asset_id*."""
    ns = _NAMESPACE_CLEAN_RE.sub("_", asset_id)
    if ns and ns[0].isdigit():
        ns = "a_" + ns
    return ns


def _resolve_format(variant: AssetFileVariant) -> str:
    """Resolve the effective format for *variant*.

    ``variant.format`` (if set to a known value) takes precedence over
    extension-based detection so that callers can override when the file
    extension is ambiguous.
    """
    if variant.format and variant.format != AssetFormat.UNKNOWN:
        return variant.format
    ext = os.path.splitext(variant.local_path)[1].lower()
    return _EXTENSION_TO_FORMAT.get(ext, AssetFormat.UNKNOWN)


# ---------------------------------------------------------------------------
# Variant selection
# ---------------------------------------------------------------------------


def _select_best_variant(descriptor: AssetDescriptor) -> AssetFileVariant:
    """Select the best file variant for Maya import.

    Priority: preferred flag > format priority (FBX best) > first match.
    """
    if not descriptor.variants:
        msg = "No variants in AssetDescriptor"
        raise ValueError(msg)

    preferred = [v for v in descriptor.variants if v.preferred]
    if preferred:
        return preferred[0]

    scored = sorted(
        descriptor.variants,
        key=lambda v: _FORMAT_PRIORITY.get(_resolve_format(v), 99),
    )
    return scored[0]


# ---------------------------------------------------------------------------
# Maya plug-in management
# ---------------------------------------------------------------------------


def _ensure_plugins(cmds: Any, format_: str) -> List[str]:
    """Load the required Maya plug-in(s) for *format_*.

    Returns the list of newly-loaded plug-in names.
    """
    plugin_names = _FORMAT_PLUGINS.get(format_, ())
    loaded: List[str] = []
    for plugin_name in plugin_names:
        if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
            cmds.loadPlugin(plugin_name)
            loaded.append(plugin_name)
    return loaded


# ---------------------------------------------------------------------------
# Skip-existing support
# ---------------------------------------------------------------------------


def _check_skip_existing(cmds: Any, asset_id: str) -> Optional[str]:
    """Return the existing root node tagged with *asset_id*, or None."""
    if not asset_id:
        return None
    for node in cmds.ls("*.dcc_mcp_asset_id") or []:
        stored = cmds.getAttr("{}.dcc_mcp_asset_id".format(node))
        if stored == asset_id:
            return node
    return None


def _tag_asset_id(cmds: Any, node: str, asset_id: str) -> None:
    """Tag *node* with *asset_id* for skip-existing dedup."""
    if not asset_id:
        return
    if not cmds.attributeQuery("dcc_mcp_asset_id", node=node, exists=True):
        cmds.addAttr(node, longName="dcc_mcp_asset_id", dataType="string")
    cmds.setAttr("{}.dcc_mcp_asset_id".format(node), asset_id, type="string")


# ---------------------------------------------------------------------------
# Import dispatch
# ---------------------------------------------------------------------------


def _file_import(
    cmds: Any,
    file_path: str,
    format_: str,
    material_mode: str,
    namespace: Optional[str],
) -> None:
    """Dispatch to the format-specific importer."""
    import_kwargs: Dict[str, Any] = {"i": True, "prompt": False}
    if namespace:
        import_kwargs["namespace"] = namespace

    if format_ == AssetFormat.FBX:
        from maya import mel  # noqa: PLC0415

        mel.eval("FBXResetImport")
        mel.eval("FBXImportMode -v add")
        if material_mode == "skip":
            mel.eval("FBXImportMaterials -v false")
        else:
            mel.eval("FBXImportMaterials -v true")
        import_kwargs["type"] = "FBX"
        import_kwargs["ignoreVersion"] = True
        import_kwargs["options"] = "fbx"
        import_kwargs["preserveReferences"] = True
        cmds.file(file_path, **import_kwargs)
    elif format_ in (AssetFormat.USD, AssetFormat.USDZ):
        import_kwargs["type"] = "USD Import"
        import_kwargs["ignoreVersion"] = True
        import_kwargs["preserveReferences"] = True
        cmds.file(file_path, **import_kwargs)
    else:
        # OBJ, GLTF, ABC, UNKNOWN -> generic file import.
        cmds.file(file_path, **import_kwargs)


# ---------------------------------------------------------------------------
# Post-import placement
# ---------------------------------------------------------------------------


def _apply_placement(
    cmds: Any,
    imported_nodes: List[str],
    placement: Optional[PlacementHint],
) -> List[ImportWarning]:
    """Apply placement transform to the imported top-level root(s).

    Returns any non-fatal placement warnings.
    """
    warnings: List[ImportWarning] = []
    if not placement:
        return warnings

    tops = [
        n
        for n in imported_nodes
        if n.count("|") <= 1 and cmds.objectType(n) == "transform"
    ]
    if not tops:
        return warnings

    root = tops[0]

    if placement.parent_name:
        try:
            if cmds.objExists(placement.parent_name):
                cmds.parent(root, placement.parent_name)
            else:
                logger.warning("Placement parent %s not found", placement.parent_name)
                warnings.append(
                    ImportWarning(
                        code=ImportWarningCode.UNSUPPORTED_FEATURE,
                        message="Placement parent not found, skipped",
                        detail="Parent '{}' does not exist in the scene".format(
                            placement.parent_name
                        ),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to parent %s to %s: %s", root, placement.parent_name, exc
            )

    if any(
        v is not None for v in [placement.translate, placement.rotate, placement.scale]
    ):
        tx, ty, tz = placement.translate or [0.0, 0.0, 0.0]
        rx, ry, rz = placement.rotate or [0.0, 0.0, 0.0]
        sx, sy, sz = placement.scale or [1.0, 1.0, 1.0]
        cmds.setAttr("{}.translate".format(root), tx, ty, tz, type="double3")
        cmds.setAttr("{}.rotate".format(root), rx, ry, rz, type="double3")
        cmds.setAttr("{}.scale".format(root), sx, sy, sz, type="double3")

    return warnings


# ---------------------------------------------------------------------------
# Material mode handling
# ---------------------------------------------------------------------------


def _apply_material_mode(cmds: Any, material_mode: str) -> List[ImportWarning]:
    """Apply material mode after import.  Returns warnings."""
    warnings: List[ImportWarning] = []

    if material_mode == "skip":
        try:
            for sg in cmds.ls(type="shadingEngine") or []:
                if sg != "initialShadingGroup":
                    cmds.delete(sg)
            for mat in cmds.ls(mat=True) or []:
                if mat not in ("lambert1", "standardSurface1", "particleCloud1"):
                    cmds.delete(mat)
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                ImportWarning(
                    code=ImportWarningCode.MATERIAL_FALLBACK,
                    message="Failed to strip materials",
                    detail=str(exc),
                )
            )
    elif material_mode == "default_gray":
        try:
            meshes = cmds.ls(type="mesh") or []
            if meshes:
                cmds.hyperShade(assign="lambert1")
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                ImportWarning(
                    code=ImportWarningCode.MATERIAL_FALLBACK,
                    message="Failed to assign default gray",
                    detail=str(exc),
                )
            )

    return warnings


# ---------------------------------------------------------------------------
# Display layer assignment
# ---------------------------------------------------------------------------


def _assign_to_collection(
    cmds: Any,
    imported_nodes: List[str],
    collection_name: str,
) -> None:
    """Assign imported roots to a named display layer."""
    if not collection_name:
        return

    layers = cmds.ls(type="displayLayer") or []
    layer = next((lyr for lyr in layers if lyr == collection_name), None)
    if layer is None:
        layer = cmds.createDisplayLayer(name=collection_name, empty=True)

    tops = [
        n
        for n in imported_nodes
        if n.count("|") <= 1 and cmds.objectType(n) == "transform"
    ]
    if tops:
        cmds.editDisplayLayerMembers(layer, tops, noRecurse=True)


# ---------------------------------------------------------------------------
# mGear context probe
# ---------------------------------------------------------------------------


def _probe_mgear_context() -> Dict[str, Any]:
    """Probe the mGear environment and return a context summary.

    This is the key mGear-specific addition.  After an import, downstream
    agents need to know what rigging context is available so they can decide
    what to do next (connect imported geo to an existing rig, create a new
    guide, build a rig, etc.).
    """
    context: Dict[str, Any] = {"mgear_available": False}

    try:
        import maya.cmds as cmds  # noqa: PLC0415, F811
    except ImportError:
        return context

    try:
        import mgear  # noqa: PLC0415, F401

        mgear_available = True
    except ImportError:
        mgear_available = False

    context["mgear_available"] = mgear_available

    if not mgear_available:
        return context

    # Get mGear version.
    for attr in ("__version__", "version", "VERSION"):
        v = getattr(mgear, attr, None)
        if v is not None:
            context["mgear_version"] = str(v)
            break

    # Check Shifter availability.
    try:
        import mgear.shifter  # noqa: PLC0415, F401

        context["shifter_available"] = True
    except ImportError:
        context["shifter_available"] = False

    if not context.get("shifter_available"):
        return context

    # Probe the scene for existing Shifter guides.
    try:
        mgear_guides = cmds.ls("*.mgear_guide", type="transform") or []
        context["guide_count"] = len(mgear_guides)
        if mgear_guides:
            context["guide_names"] = mgear_guides[:20]  # cap to avoid giant payloads
    except Exception:  # noqa: BLE001
        logger.warning("Failed to probe mGear guides", exc_info=True)

    # Probe for built Shifter rigs (cpm* nodes indicate built rigs).
    try:
        rig_roots = cmds.ls("*.cpm_guide", type="transform") or []
        context["rig_root_count"] = len(rig_roots)
    except Exception:  # noqa: BLE001
        logger.warning("Failed to probe mGear rig roots", exc_info=True)

    return context


# ---------------------------------------------------------------------------
# Core import logic
# ---------------------------------------------------------------------------


def import_to_scene(request: ImportToSceneRequest) -> Dict[str, Any]:
    """Import an asset into the current Maya scene.

    Args:
        request: Fully populated ImportToSceneRequest.

    Returns:
        ToolResult dict containing an ImportToSceneResult in its context.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return skill_error(
            "Maya not available",
            "maya.cmds could not be imported",
            possible_solutions=["Run this skill inside Maya or mayapy"],
        )

    descriptor = request.descriptor
    material_mode = request.material_mode or "as_authored"
    placement = request.placement
    collection = request.target_collection
    skip_existing = request.skip_existing
    extra = request.extra or {}

    warnings: List[ImportWarning] = []

    # --- Validate descriptor --------------------------------------------------
    try:
        descriptor.validate()
    except Exception as exc:
        return skill_error(
            "Invalid AssetDescriptor",
            str(exc),
            asset_id=descriptor.asset_id,
        )

    # --- Skip-existing check -------------------------------------------------
    existing_root = _check_skip_existing(cmds, descriptor.asset_id)
    if skip_existing and existing_root is not None:
        return skill_success(
            "Skipped import: asset_id '{}' already present (node: {})".format(
                descriptor.asset_id, existing_root
            ),
            result=ImportToSceneResult(
                success=True,
                imported_nodes=[existing_root],
                warnings=[
                    ImportWarning(
                        code=ImportWarningCode.UNKNOWN,
                        message="Import skipped",
                        detail="Already imported as {}".format(existing_root),
                    )
                ],
                error_message=None,
                extra=extra,
            ),
            prompt="Use get_scene_info or inspect_mgear_environment to inspect the existing asset.",
        )

    # --- Select best variant -------------------------------------------------
    try:
        variant = _select_best_variant(descriptor)
    except ValueError as exc:
        return skill_error(
            "No variants available",
            str(exc),
            asset_id=descriptor.asset_id,
        )

    file_path = _normalize_path(variant.local_path)
    if not os.path.exists(file_path):
        return skill_error(
            "File not found",
            "{} does not exist on disk".format(file_path),
            file_path=file_path,
            asset_id=descriptor.asset_id,
        )

    resolved_format = _resolve_format(variant)

    # .blend files are not importable into Maya.
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".blend":
        return skill_error(
            "Unsupported format",
            "Blender .blend files cannot be imported into Maya",
            file_path=file_path,
            format="BLEND",
        )

    # --- Load plug-ins -------------------------------------------------------
    if resolved_format != AssetFormat.UNKNOWN:
        try:
            _ensure_plugins(cmds, resolved_format)
        except Exception as exc:  # noqa: BLE001
            return skill_error(
                "Plugin unavailable",
                "Failed to load plugin for {}: {}".format(file_path, exc),
                file_path=file_path,
                format=str(resolved_format),
            )

    # --- Snapshot scene state before import ---------------------------------
    before = cmds.ls(long=True) or []

    # --- Dispatch import ----------------------------------------------------
    namespace = _make_namespace(descriptor.asset_id) if descriptor.asset_id else None
    try:
        _file_import(cmds, file_path, resolved_format, material_mode, namespace)
        after = cmds.ls(long=True) or []
    except Exception as exc:  # noqa: BLE001
        return skill_exception(
            exc,
            message="Import failed: {}".format(file_path),
            file_path=file_path,
            asset_id=descriptor.asset_id,
            format=str(resolved_format),
        )

    # --- Determine imported nodes -------------------------------------------
    imported_long = [n for n in after if n not in set(before)]
    if not imported_long:
        try:
            imported_long = cmds.ls(importedNodes=True, long=True) or []
        except Exception:  # noqa: BLE001
            imported_long = []

    # --- Tag asset_id -------------------------------------------------------
    if descriptor.asset_id:
        roots = [
            n
            for n in imported_long
            if n.count("|") <= 1 and cmds.objectType(n) == "transform"
        ]
        if roots:
            _tag_asset_id(cmds, roots[0], descriptor.asset_id)

    # --- Apply placement ----------------------------------------------------
    placement_warnings = _apply_placement(cmds, imported_long, placement)
    warnings.extend(placement_warnings)

    # --- Apply material mode ------------------------------------------------
    if material_mode != "as_authored":
        mat_warnings = _apply_material_mode(cmds, material_mode)
        warnings.extend(mat_warnings)

    # --- Assign to display layer --------------------------------------------
    if collection:
        try:
            _assign_to_collection(cmds, imported_long, collection)
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                ImportWarning(
                    code=ImportWarningCode.UNSUPPORTED_FEATURE,
                    message="Failed to assign display layer",
                    detail="Layer '{}': {}".format(collection, exc),
                )
            )

    # --- mGear context probe (the mGear-specific addition) -----------------
    mgear_context = _probe_mgear_context()

    result = ImportToSceneResult(
        success=True,
        imported_nodes=imported_long,
        warnings=warnings,
        error_message=None,
        extra={
            **(extra or {}),
            "file_path": file_path,
            "asset_id": descriptor.asset_id,
            "namespace": namespace,
            "imported_count": len(imported_long),
            "mgear_context": mgear_context,
        },
    )

    # Build a context-aware prompt.
    prompt_parts: List[str] = [
        "Imported {} node(s) from {}".format(len(imported_long), file_path),
    ]
    if mgear_context.get("mgear_available"):
        prompt_parts.append(
            "mGear {} detected".format(mgear_context.get("mgear_version", ""))
        )
        guide_count = mgear_context.get("guide_count", 0)
        if guide_count:
            prompt_parts.append("{} Shifter guide(s) in scene".format(guide_count))
        rig_count = mgear_context.get("rig_root_count", 0)
        if rig_count:
            prompt_parts.append("{} built rig(s) in scene".format(rig_count))
    else:
        prompt_parts.append("mGear not detected — import was plain Maya")

    return skill_success(
        ". ".join(prompt_parts),
        result=result,
        prompt=(
            "Use get_scene_info or inspect_mgear_environment to inspect "
            "imported nodes and the rigging context."
        ),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; builds ImportToSceneRequest from flat kwargs.

    Accepts the same flat parameters as the *input_schema* defined in
    ``tools.yaml``:
        descriptor (dict, required)
        material_mode (str, default: as_authored)
        placement (dict, optional)
        target_collection (str, optional)
        skip_existing (bool, default: false)
        extra (dict, optional)
    """
    try:
        raw_descriptor = kwargs.get("descriptor")
        if not raw_descriptor:
            return skill_error(
                "Missing descriptor",
                "descriptor is required",
                possible_solutions=[
                    "Pass an AssetDescriptor dict with asset_id and at least one variant"
                ],
            )

        # Convert nested variant dicts to AssetFileVariant objects.
        raw_variants = raw_descriptor.get("variants", [])
        variants = [
            AssetFileVariant(**v) if isinstance(v, dict) else v for v in raw_variants
        ]
        raw_descriptor["variants"] = variants
        raw_descriptor.setdefault("extra", {})
        descriptor = AssetDescriptor(**raw_descriptor)

        raw_placement = kwargs.get("placement")
        placement = PlacementHint(**raw_placement) if raw_placement else None

        request = ImportToSceneRequest(
            descriptor=descriptor,
            material_mode=kwargs.get("material_mode", "as_authored"),
            placement=placement,
            target_collection=kwargs.get("target_collection"),
            skip_existing=kwargs.get("skip_existing", False),
            extra=kwargs.get("extra", {}),
        )
        return import_to_scene(request)
    except Exception as exc:
        return skill_exception(exc, message="Failed to build import request")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
