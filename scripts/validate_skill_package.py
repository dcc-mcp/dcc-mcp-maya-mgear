"""Validate DCC-MCP skill package layout, drift, metadata, and discovery.

This script performs comprehensive CI validation of the skill package:
- Lint the canonical SKILL.md manifest and tools.yaml
- Verify source_file paths resolve inside the installable skill package
- Verify root/package mirrors do not drift
- Validate marketplace metadata and version consistency
- Run a no-Maya discovery/load smoke test

Usage:
    python scripts/validate_skill_package.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()

# Canonical installable skill root
SKILL_ROOT = REPO_ROOT / "skill" / "maya-mgear"

# Canonical paths (source of truth)
CANONICAL_SKILL_MD = SKILL_ROOT / "SKILL.md"
CANONICAL_TOOLS_YAML = SKILL_ROOT / "tools.yaml"
CANONICAL_MARKETPLACE_JSON = REPO_ROOT / "marketplace.json"
CANONICAL_SCRIPTS_DIR = SKILL_ROOT / "scripts"
CANONICAL_DEPENDS_MD = SKILL_ROOT / "metadata" / "depends.md"

# Mirror paths (must match canonical)
MIRROR_SKILL_MD = REPO_ROOT / "SKILL.md"
MIRROR_TOOLS_YAML = REPO_ROOT / "tools.yaml"
MIRROR_SCRIPTS_DIR = REPO_ROOT / "scripts"
MIRROR_DEPENDS_MD = REPO_ROOT / "metadata" / "depends.md"
MIRROR_MARKETPLACE_DIR = REPO_ROOT / "marketplace"
MIRROR_MARKETPLACE_PKG = REPO_ROOT / "dcc-mcp-maya-mgear" / "marketplace.json"

PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"
RELEASE_PLEASE_MANIFEST = REPO_ROOT / ".release-please-manifest.json"
ICON_PNG = REPO_ROOT / "icon.png"

# Files that are exact mirrors of the canonical (content must match byte-for-byte)
EXACT_MIRRORS: List[Tuple[pathlib.Path, pathlib.Path, str]] = [
    (CANONICAL_SKILL_MD, MIRROR_SKILL_MD, "SKILL.md (root)"),
    (CANONICAL_TOOLS_YAML, MIRROR_TOOLS_YAML, "tools.yaml (root)"),
    (CANONICAL_DEPENDS_MD, MIRROR_DEPENDS_MD, "metadata/depends.md (root)"),
]

# marketplace.json mirrors (only dcc-mcp-maya-mgear/ copy is expected to match)
MARKETPLACE_MIRRORS: List[Tuple[pathlib.Path, pathlib.Path, str]] = [
    (CANONICAL_MARKETPLACE_JSON, MIRROR_MARKETPLACE_PKG, "dcc-mcp-maya-mgear/marketplace.json"),
]

# Script mirrors — each script must match byte-for-byte
SCRIPT_MIRRORS: List[Tuple[pathlib.Path, pathlib.Path, str]] = []
for _script in sorted(CANONICAL_SCRIPTS_DIR.glob("*.py")):
    _name = _script.name
    _mirror = MIRROR_SCRIPTS_DIR / _name
    SCRIPT_MIRRORS.append((_script, _mirror, f"scripts/{_name} (root)"))

# tools.yaml required tool names
REQUIRED_TOOLS = [
    "inspect_mgear_environment",
    "list_shifter_components",
    "create_shifter_guide_from_template",
    "build_shifter_rig",
    "export_shifter_guide_template",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: pathlib.Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_yaml(path: pathlib.Path) -> dict:
    import yaml

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Check 1: File existence
# ---------------------------------------------------------------------------

def check_files_exist() -> None:
    """Verify all required files exist."""
    required = [
        CANONICAL_SKILL_MD,
        CANONICAL_TOOLS_YAML,
        CANONICAL_MARKETPLACE_JSON,
        PYPROJECT_TOML,
        RELEASE_PLEASE_MANIFEST,
        ICON_PNG,
        CANONICAL_DEPENDS_MD,
    ]
    for p in required:
        if not p.is_file():
            _fail(f"Required file missing: {p.relative_to(REPO_ROOT)}")
    print(f"  [OK] All {len(required)} required files exist")


# ---------------------------------------------------------------------------
# Check 2: SKILL.md lint
# ---------------------------------------------------------------------------

def check_skill_md() -> None:
    """Lint the canonical SKILL.md frontmatter."""
    import yaml

    content = _read_text(CANONICAL_SKILL_MD)
    parts = content.split("---")
    if len(parts) < 3:
        _fail("SKILL.md must have YAML frontmatter delimited by ---")

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        _fail(f"SKILL.md frontmatter is not valid YAML: {e}")

    if not isinstance(frontmatter, dict):
        _fail("SKILL.md frontmatter must be a YAML mapping")

    # Required top-level keys
    if frontmatter.get("name") != "maya-mgear":
        _fail(f"SKILL.md name must be 'maya-mgear', got {frontmatter.get('name')!r}")

    if "description" not in frontmatter:
        _fail("SKILL.md missing 'description' field")

    if "metadata" not in frontmatter:
        _fail("SKILL.md missing 'metadata' field")

    # No top-level 'version' (strict loader contract)
    if "version" in frontmatter:
        _fail("SKILL.md has top-level 'version' — must be under metadata.dcc-mcp.version")

    metadata = frontmatter["metadata"]
    dcc_mcp = metadata.get("dcc-mcp")
    if not dcc_mcp:
        _fail("SKILL.md metadata missing 'dcc-mcp' section")

    if dcc_mcp.get("dcc") != "maya":
        _fail(f"SKILL.md dcc must be 'maya', got {dcc_mcp.get('dcc')!r}")

    if "version" not in dcc_mcp:
        _fail("SKILL.md metadata.dcc-mcp missing 'version' field")

    if "tools" not in dcc_mcp:
        _fail("SKILL.md metadata.dcc-mcp missing 'tools' field")

    if dcc_mcp.get("tools") != "tools.yaml":
        _fail(f"SKILL.md tools reference must be 'tools.yaml', got {dcc_mcp.get('tools')!r}")

    if "depends" not in dcc_mcp:
        _fail("SKILL.md metadata.dcc-mcp missing 'depends' field")

    print("  [OK] SKILL.md frontmatter valid")


# ---------------------------------------------------------------------------
# Check 3: tools.yaml lint + source_file resolution
# ---------------------------------------------------------------------------

def check_tools_yaml() -> None:
    """Lint tools.yaml and verify source_file paths resolve."""
    import yaml

    data = _read_yaml(CANONICAL_TOOLS_YAML)
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        _fail("tools.yaml 'tools' must be a list")

    tool_names = [t["name"] for t in tools if isinstance(t, dict) and "name" in t]
    if len(tools) != len(REQUIRED_TOOLS):
        _fail(f"tools.yaml has {len(tools)} tools, expected {len(REQUIRED_TOOLS)}")

    for req in REQUIRED_TOOLS:
        if req not in tool_names:
            _fail(f"tools.yaml missing required tool: {req}")

    # Verify source_file paths resolve
    for tool in tools:
        name = tool.get("name", "<unnamed>")
        source_file = tool.get("source_file")
        if source_file:
            source_path = SKILL_ROOT / source_file
            if not source_path.is_file():
                _fail(f"Tool '{name}' source_file '{source_file}' not found in skill package")
            print(f"    source_file resolved: {source_file}")
        else:
            # Without explicit source_file, check by convention: scripts/<name>.py
            script_path = CANONICAL_SCRIPTS_DIR / f"{name}.py"
            if not script_path.is_file():
                _fail(f"Tool '{name}' has no source_file and no script at scripts/{name}.py")

    print(f"  [OK] tools.yaml: {len(tools)} tools validated, all source paths resolved")


# ---------------------------------------------------------------------------
# Check 4: Drift detection
# ---------------------------------------------------------------------------

def check_drift() -> None:
    """Verify all mirror files match their canonical counterparts."""
    errors = []

    # Exact mirrors (byte-for-byte)
    for canonical, mirror, label in EXACT_MIRRORS:
        if not mirror.is_file():
            errors.append(f"{label}: mirror file missing at {mirror.relative_to(REPO_ROOT)}")
            continue
        can_content = canonical.read_bytes()
        mir_content = mirror.read_bytes()
        if can_content != mir_content:
            errors.append(f"{label}: content differs from canonical {canonical.relative_to(REPO_ROOT)}")

    # Script mirrors
    for canonical, mirror, label in SCRIPT_MIRRORS:
        if not mirror.is_file():
            errors.append(f"{label}: mirror file missing at {mirror.relative_to(REPO_ROOT)}")
            continue
        can_content = canonical.read_bytes()
        mir_content = mirror.read_bytes()
        if can_content != mir_content:
            errors.append(f"{label}: content differs from canonical {canonical.relative_to(REPO_ROOT)}")

    # marketplace.json mirrors
    for canonical, mirror, label in MARKETPLACE_MIRRORS:
        if not mirror.is_file():
            errors.append(f"{label}: mirror file missing at {mirror.relative_to(REPO_ROOT)}")
            continue
        can_content = canonical.read_bytes()
        mir_content = mirror.read_bytes()
        if can_content != mir_content:
            errors.append(f"{label}: content differs from canonical {canonical.relative_to(REPO_ROOT)}")

    if errors:
        print("  Drift detected:")
        for e in errors:
            print(f"    ERROR: {e}")
        _fail("Drift detected — update mirror files to match canonical")
    print(f"  [OK] All mirrors match canonical ({len(EXACT_MIRRORS) + len(SCRIPT_MIRRORS) + len(MARKETPLACE_MIRRORS)} files checked)")


# ---------------------------------------------------------------------------
# Check 5: Version consistency
# ---------------------------------------------------------------------------

def check_version_consistency() -> None:
    """Verify version is consistent across all metadata sources."""
    import yaml

    # pyproject.toml version
    pptext = _read_text(PYPROJECT_TOML)
    m = re.search(r'^version\s*=\s*"([^"]+)"', pptext, re.MULTILINE)
    if not m:
        _fail("Could not find version in pyproject.toml")
    pyproject_version = m.group(1)

    # .release-please-manifest.json
    rp_data = _read_json(RELEASE_PLEASE_MANIFEST)
    rp_version = rp_data.get(".")
    if not rp_version:
        _fail("Could not find version in .release-please-manifest.json")

    if rp_version != pyproject_version:
        _fail(f"Version mismatch: pyproject.toml={pyproject_version}, release-please={rp_version}")

    # SKILL.md version (metadata.dcc-mcp.version)
    skill_content = _read_text(CANONICAL_SKILL_MD)
    parts = skill_content.split("---")
    fm = yaml.safe_load(parts[1])
    skill_version = fm.get("metadata", {}).get("dcc-mcp", {}).get("version", "")
    expected_skill_ver = f"v{pyproject_version}"
    if skill_version != expected_skill_ver:
        _fail(f"SKILL.md version={skill_version}, expected {expected_skill_ver}")

    # marketplace.json version
    mp_data = _read_json(CANONICAL_MARKETPLACE_JSON)
    mp_entries = mp_data.get("entries", [])
    if not mp_entries:
        _fail("marketplace.json has no entries")

    mp_version = mp_entries[0].get("version")
    if mp_version != pyproject_version:
        _fail(f"marketplace.json version={mp_version}, expected {pyproject_version}")

    print(f"  [OK] Version consistent: {pyproject_version} across pyproject.toml, SKILL.md, marketplace.json, release-please")


# ---------------------------------------------------------------------------
# Check 6: No-Maya discovery/load smoke
# ---------------------------------------------------------------------------

def check_discovery_smoke() -> None:
    """Verify the skill package can be discovered and loaded without Maya.

    This is a no-Maya smoke test that:
    - Imports the Python package (dcc_mcp_maya_mgear)
    - Loads and validates the SKILL.md manifest
    - Loads and validates tools.yaml
    - Ensures all 5 tool scripts are importable
    """
    # Test package import
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        import dcc_mcp_maya_mgear  # noqa: F401
        print("    [OK] dcc_mcp_maya_mgear package imported")
    except ImportError as e:
        _fail(f"Package import failed: {e}")

    # Test tool script imports
    scripts_dir = str(CANONICAL_SCRIPTS_DIR)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    for tool_name in REQUIRED_TOOLS:
        try:
            __import__(tool_name)
            print(f"    [OK] {tool_name} imported")
        except ImportError as e:
            _fail(f"Tool script '{tool_name}' import failed: {e}")

    print(f"  [OK] No-Maya discovery/load smoke passed — all {len(REQUIRED_TOOLS)} tools importable")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all validation checks."""
    print("=" * 60)
    print("DCC-MCP Skill Package Validation")
    print("=" * 60)
    print(f"Repo root: {REPO_ROOT}")
    print(f"Skill root: {SKILL_ROOT.relative_to(REPO_ROOT)}")
    print()

    checks = [
        ("Check 1: File existence", check_files_exist),
        ("Check 2: SKILL.md lint", check_skill_md),
        ("Check 3: tools.yaml lint + source_file resolution", check_tools_yaml),
        ("Check 4: Drift detection (root vs nested mirrors)", check_drift),
        ("Check 5: Version consistency", check_version_consistency),
        ("Check 6: No-Maya discovery/load smoke", check_discovery_smoke),
    ]

    failed = False
    for name, fn in checks:
        try:
            fn()
        except SystemExit:
            failed = True
        except Exception as e:
            print(f"  ERROR: {e}")
            failed = True
        print()

    print("=" * 60)
    if failed:
        print("VALIDATION FAILED")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
