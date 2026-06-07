"""Shared test fixtures and path configuration."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path so the dcc_mcp_maya_mgear package is importable.
# This also ensures coverage can track the package when it's imported.
_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# Also ensure skill/ is on sys.path for direct script imports.
_skill = Path(__file__).parent.parent / "skill"
if str(_skill) not in sys.path:
    sys.path.insert(0, str(_skill))
