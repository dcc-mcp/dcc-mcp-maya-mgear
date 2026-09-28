# AGENTS.md — dcc-mcp-maya-mgear

> mGear Shifter rigging integration for the DCC-MCP ecosystem — inspect mGear environments, list Shifter components, create guides, build rigs, export rigs to FBX/Alembic, and export templates through typed MCP tools.
> Navigation map for AI agents, not a reference manual. Detailed tool tables and API live in `README.md`.

## Repo shape — read this first

This is a **skill-only repository**. There is no `pyproject.toml`, no Python package, no `justfile`, and no PyPI publish step. The deliverable is the two skill directories under `skill/`, installed from Git through the [marketplace](https://github.com/dcc-mcp/marketplace):

```bash
dcc-mcp marketplace install dcc-mcp-maya-mgear --dcc maya
# -> ~/.dcc-mcp/marketplace/maya/dcc-mcp-maya-mgear/
```

If you were looking for an adapter package with a `src/` layout, you are in the wrong repo — that is `dcc-mcp-maya`.

## Build & test

CI runs everything on Python 3.12 with plain commands. No justfile — do not invent `vx just` recipes here.

```bash
pip install ruff
ruff check skill/ tests/
ruff format --check skill/ tests/

pip install pytest pyyaml dcc-mcp-core
pytest tests/ -q
```

Additional gates, all defined inline in `.github/workflows/ci.yml`:

- **skill-lint / skill-package** — `SKILL.md` frontmatter must declare `name: maya-mgear` with `metadata.dcc-mcp.depends`; `skill/maya-mgear/tools.yaml` must list **exactly 7 tools**; `metadata/depends.md` must exist; `scripts/` must contain `.py` files.
- **marketplace-lint** — validates `marketplace.json` against a copy of the `marketplace-v1` schema plus a relative-icon-exists check. Needs `pip install jsonschema`.
- **layout guard** — root-level `SKILL.md`, `tools.yaml`, `metadata/`, and `scripts/` are **forbidden**; the canonical paths are the two `skill/*/` directories.

Lint config lives in `ruff.toml`: line-length 88, `target-version = "py37"`, and a deliberately narrow rule set (`E4`, `E7`, `E9`, `F`) pinned so a ruff upgrade cannot silently widen it. Widen the rule set on purpose, never by accident.

## Repo layout

| Path | Role |
|---|---|
| `skill/maya-mgear/` | Canonical installable skill package — `SKILL.md`, `tools.yaml`, `metadata/depends.md`, `scripts/` (7 mGear tools) |
| `skill/mgear-import-to-scene/` | Second skill package — 1 import tool over the `AssetDescriptor` contract |
| `tests/` | pytest suite for the skill scripts (no `src/` on the path; scripts are imported as skill modules) |
| `marketplace.json` | Marketplace catalog entry (schema `marketplace-v1`) |
| `icon.png` | Catalog icon referenced by `marketplace.json` |
| `ruff.toml` | Pinned lint rule set |
| `docs/` | Logo (`assets/`), showcase image |

## Release

- release-please drives versioning from Conventional Commits on `main` (`release-type: python`, package-name `dcc-mcp-maya-mgear`).
- Whether a release is cut at all is a changelog question, not a prefix question: if every
  commit in the batch lands in a `hidden: true` section the changelog entry is empty, and
  release-please skips the whole batch — no release pull request, **no version bump**
  (`strategies/base.ts` logs “No user facing commits found since … - skipping” when
  `changelogEmpty()` finds only the heading line).
- For `release-type: python`: `chore:`/`ci:`/`style:`/`refactor:`/`test:`/`build:` are
  `hidden: true`; `docs:` is a **visible** `Documentation` section.
- Only once a release *is* cut does the prefix choose the bump: breaking → major,
  `feat:` → minor, anything else → patch
  (`DefaultVersioningStrategy.determineReleaseType()`).
- Use `chore:` when the batch should **not** cut a release; use `docs:` when doc-only work
  should cut a patch release.
- There is **no version file in the repo** — release-please keeps the version in `.release-please-manifest.json` only.
- `.github/workflows/release.yml` attaches a source archive to the GitHub Release, then syncs `entries[0].version` in `marketplace.json` to the released version and pushes that commit.

## Do / Don't

- **Do** single-source agent instructions here. This is the only agent contract file at the repo root.
- **Do** probe the host before touching mGear (`inspect_mgear_environment`), and prefer typed skill tools over raw MEL or `execute_python`.
- **Do** keep skill files inside `skill/<name>/`. CI validates that location (`skill/maya-mgear/SKILL.md` and its `tools.yaml`) and rejects root-level `SKILL.md` / `tools.yaml` / `metadata/` / `scripts/`; it does not scan the whole repo for other skill files.
- **Don't** add `CLAUDE.md` / `GEMINI.md` / `CURSOR.md` / `ANTHROPIC.md` / `OPENAI.md` / `COPILOT.md` / `CODEBUDDY.md` / `.cursorrules` / `.clinerules` / `.windsurfrules` at the root. This repo has no `docs/integrations/`; keep any vendor-specific notes here.
- **Don't** hardcode an exact version in tests or in `marketplace.json` by hand — release-please rewrites `marketplace.json` on release.
- **Don't** commit build artifacts to the repo root.
