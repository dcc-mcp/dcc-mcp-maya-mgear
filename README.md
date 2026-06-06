# dcc-mcp-maya-mgear

mGear Shifter deep integration skills for [dcc-mcp-maya](https://github.com/dcc-mcp/dcc-mcp-maya).

This repository provides a set of MCP skills that wrap mGear's Shifter
API into typed, callable tools for Maya — enabling LLM-based agents to inspect mGear environments,
interact with Shifter components, and build rigs programmatically.

## Prerequisites

- Autodesk Maya 2022+
- [dcc-mcp-maya](https://github.com/dcc-mcp/dcc-mcp-maya) installed and configured
- mGear Shifter installed and accessible from Maya's Python environment

## Installation

```bash
pip install dcc-mcp-maya-mgear
```

## Skills

| Skill | Description |
|-------|-------------|
| `maya-mgear` | Core mGear Shifter integration tools |

## Usage

In Claude Desktop (or any MCP client), load the skill and call tools:

1. Load the skill: `load_skill("maya-mgear")`
2. Use the tools: `inspect_mgear_environment()`, `list_shifter_components()`, etc.

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
pytest tests/
```

## License

MIT
