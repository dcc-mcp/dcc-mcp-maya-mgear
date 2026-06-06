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

## Testing

Tests are located in `tests/` and use pytest with signature-constrained mocks
that match the real mGear upstream API.  The test suite validates all 5 MVP
tools across multiple scenarios:

- **Graceful degradation** — every tool returns a proper error result when
  mGear is not installed (success=False, error populated, prompt with
  actionable guidance).
- **API contract** — mocks enforce real mGear function signatures; calling
  `draw_comp()` with wrong kwarg names or `build_from_selection()` with
  extra arguments causes a test failure.
- **Partial availability** — tools handle broken sub-modules,
  `RuntimeError` from upstream, and missing Maya commands safely.

### Running tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov --cov-report=term

# Run a single test module
pytest tests/test_mgear_skills.py -v
```

### Coverage

Coverage is tracked across all source modules under `src/`.  The CI
pipeline uploads `coverage.xml` to Codecov on every push and PR.
Minimum expected coverage: ≥80% per module.

Current coverage baseline (68 tests, all 5 tools): **87%**.

### Linting

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

## CI

| Job | Matrix | Purpose |
|-----|--------|---------|
| Test | 3 OS × 5 Python versions | Unit tests + coverage |
| Lint | ubuntu / 3.12 | Ruff check + format |
| Skill Lint | ubuntu / 3.12 | Validate SKILL.md + tools.yaml |

## License

MIT
