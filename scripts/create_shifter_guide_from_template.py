"""Create a Shifter guide from a named template at a specified location.

Real mGear API: ``mgear.shifter.guide_manager.draw_comp(comp_type, parent=None, showUI=True)``
(guide_manager.py:24-42). Naming follows the component template's convention;
the *guide_name* parameter is applied post-creation via Maya rename.

Some mGear versions (e.g. 5.2.1) have ``draw_comp`` return None while still
creating guide nodes in the scene.  This module handles that by falling back
to a scene query that discovers newly-created nodes via the ``isGearGuide``
and ``ismodel`` attributes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success


def _set_position(node: str, pos: List[float]) -> None:
    """Move *node* to *pos* in world space if Maya is available."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return
    try:
        cmds.xform(node, ws=True, translation=pos)
    except Exception:
        pass


def _rename_guide(node: str, desired_name: str) -> str:
    """Rename *node* to *desired_name* (Maya rename). Returns the final name."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return node
    try:
        return cmds.rename(node, desired_name)
    except Exception:
        return node


def _get_existing_guide_paths() -> Set[str]:
    """Return full-path names of all existing guide nodes in the scene."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return set()

    existing: Set[str] = set()
    try:
        for node in (cmds.ls(type="transform", long=True) or []):
            try:
                is_gear = cmds.attributeQuery("isGearGuide", node=node, exists=True)
                is_model = cmds.attributeQuery("ismodel", node=node, exists=True)
                if is_gear or is_model:
                    existing.add(node)
            except Exception:
                continue
    except Exception:
        pass
    return existing


def _get_new_nodes(previous: Set[str]) -> List[str]:
    """Return guide nodes created since *previous* snapshot, sorted by short name."""
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return []

    created: List[str] = []
    try:
        for node in (cmds.ls(type="transform", long=True) or []):
            if node in previous:
                continue
            try:
                is_gear = cmds.attributeQuery("isGearGuide", node=node, exists=True)
                is_model = cmds.attributeQuery("ismodel", node=node, exists=True)
                if is_gear or is_model:
                    created.append(node)
            except Exception:
                continue
    except Exception:
        pass
    return sorted(created, key=lambda n: n.split("|")[-1])


def _get_guide_root(created_nodes: List[str]) -> Optional[str]:
    """Return the guide root node from the created node list.

    The guide root is the top-most node with the ``ismodel`` attribute.
    If no ``ismodel`` node is found, return the first created node.
    """
    try:
        import maya.cmds as cmds  # noqa: PLC0415
    except ImportError:
        return created_nodes[0] if created_nodes else None

    for node in created_nodes:
        try:
            if cmds.attributeQuery("ismodel", node=node, exists=True):
                return node
        except Exception:
            continue
    return created_nodes[0] if created_nodes else None


def _create_guide(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a Shifter guide via ``draw_comp()`` — the verified real mGear API.

    ``draw_comp(comp_type, parent=None, showUI=True)`` is the sole guide
    creation entry point.  *guide_name* is not a parameter of draw_comp;
    we apply it after creation.  *position* is applied via Maya transforms.

    When ``draw_comp`` returns None (observed in mGear 5.2.1), we fall back
    to detecting newly-created nodes in the scene.
    """
    import mgear.shifter.guide_manager as gui_mgr

    pos = position if position else [0.0, 0.0, 0.0]

    # Snapshot existing guide nodes before creation
    before = _get_existing_guide_paths()

    node = gui_mgr.draw_comp(comp_type=template, parent=parent_guide, showUI=False)

    if node:
        # draw_comp returned a node — the normal path
        final_name = _rename_guide(str(node), guide_name)
        _set_position(final_name, pos)

        # Discover any additional nodes created alongside the returned one
        new_nodes = _get_new_nodes(before)
        guide_root = _get_guide_root(new_nodes) if new_nodes else final_name

        result: Dict[str, Any] = {
            "guide_name": guide_name,
            "template": template,
            "position": pos,
            "node": final_name,
            "guide_root": guide_root,
            "created_nodes": [n.split("|")[-1] for n in new_nodes] if new_nodes else [final_name],
        }
        return result

    # draw_comp returned None — check if nodes were created anyway
    new_nodes = _get_new_nodes(before)
    if new_nodes:
        guide_root = _get_guide_root(new_nodes)
        # Rename the guide root to the requested name
        if guide_root and guide_name:
            renamed = _rename_guide(guide_root, guide_name)
            guide_root = renamed
        if guide_root:
            _set_position(guide_root, pos)

        result = {
            "guide_name": guide_name,
            "template": template,
            "position": pos,
            "node": guide_root,
            "guide_root": guide_root,
            "created_nodes": [n.split("|")[-1] for n in new_nodes],
        }
        return result

    # Neither draw_comp nor scene inspection found nodes
    return {
        "guide_name": guide_name,
        "template": template,
        "position": pos,
    }


def create_shifter_guide_from_template(
    guide_name: str,
    template: str,
    position: Optional[List[float]] = None,
    parent_guide: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Shifter guide from a named template.

    Args:
        guide_name: Desired name for the new guide.  Applied post-creation;
            the component template controls the initial Maya node name.
        template: Component template name (e.g. ``"arm_2jnt_01"``, ``"leg_2jnt_01"``).
        position: World-space position ``[x, y, z]``. Defaults to origin.
        parent_guide: Optional parent guide name for hierarchy.
        parameters: Reserved for future use.  Component parameters are set
            via the component's own config system, not at draw_comp() time.
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

        result = _create_guide(
            guide_name=guide_name,
            template=template,
            position=position,
            parent_guide=parent_guide,
        )

        if result.get("node"):
            return skill_success(
                "Created guide '{}' from template '{}'".format(result["node"], template),
                **result,
                prompt="Use build_shifter_rig to generate the rig from this guide.",
            )
        else:
            return skill_error(
                "Failed to create guide '{}' — no guide nodes were created".format(guide_name),
                "draw_comp('{}') returned None and no new guide nodes found in scene".format(template),
                prompt="Verify the component type '{}' is valid. Use list_shifter_components to see available types.".format(
                    template
                ),
                component_type=template,
            )
    except Exception as exc:
        return skill_exception(exc, message="Failed to create Shifter guide from template")


@skill_entry
def main(**kwargs: Any) -> Dict[str, Any]:
    """Entry point; delegates to :func:`create_shifter_guide_from_template`."""
    return create_shifter_guide_from_template(**kwargs)


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
