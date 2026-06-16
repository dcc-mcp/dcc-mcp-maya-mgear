# dcc-mcp-maya-mgear

[![Marketplace](https://img.shields.io/badge/dcc--mcp-marketplace-orange)](https://github.com/dcc-mcp/marketplace)
[![DCC](https://img.shields.io/badge/dcc-maya-blue)](https://github.com/dcc-mcp/dcc-mcp-maya)

mGear Shifter rigging integration for the DCC-MCP ecosystem — inspect mGear
environments, list Shifter components, create guides, build rigs, and export
templates through typed MCP tools.

## Install

```bash
dcc-mcp marketplace install dcc-mcp-maya-mgear --dcc maya
```

Installed to `~/.dcc-mcp/marketplace/maya/dcc-mcp-maya-mgear/`. After install,
the skill is automatically registered with the running Maya adapter.

## Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| `maya-mgear` | 6 | Inspect, list, create, import, build, and export mGear Shifter components |

### Tools

| Tool | Description |
|------|-------------|
| `inspect_mgear_environment` | Check mGear availability, version, and module diagnostics |
| `list_shifter_components` | List Shifter component types and scene guides |
| `create_shifter_guide_from_template` | Create a guide from a named template at a position |
| `build_shifter_rig` | Build a rig from an existing Shifter guide |
| `import_shifter_sample_template` | Import an official Shifter sample template (e.g. quadruped) |
| `export_shifter_guide_template` | Export a guide or component as a reusable template |

## Prerequisites

- Autodesk Maya 2022+
- [dcc-mcp-maya](https://github.com/dcc-mcp/dcc-mcp-maya) installed and configured
- [mGear Shifter](https://github.com/mgear-dev/mgear) installed and accessible from Maya
- dcc-mcp-core ≥ 0.18.2

## Contributing

This is a standalone skill repo. See [CONTRIBUTING.md](https://github.com/dcc-mcp/marketplace/blob/main/CONTRIBUTING.md) in the marketplace repo for how to propose changes.

```bash
# Dev setup
pip install -e ".[dev]"

# Lint
ruff check . && ruff format --check .

# Test (76 tests, 6 tools, 3 OS × 5 Python on CI)
pytest tests/ -v
```

## Related

- [DCC-MCP Marketplace](https://github.com/dcc-mcp/marketplace) — skill catalog
- [dcc-mcp-core](https://github.com/dcc-mcp/dcc-mcp-core) — runtime
- [dcc-mcp-maya](https://github.com/dcc-mcp/dcc-mcp-maya) — Maya adapter

## License

MIT
