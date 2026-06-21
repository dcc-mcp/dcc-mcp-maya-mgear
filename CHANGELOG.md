# Changelog

## [0.7.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.6.0...dcc-mcp-maya-mgear-v0.7.0) (2026-06-21)


### Features

* add mgear-import-to-scene skill (PIP-1896) ([dccd75e](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/dccd75eedf7c445a73ad747d231e09a270b0aa60))
* add mgear-import-to-scene skill with contract-aligned import and mGear context probe ([0db1337](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/0db1337332afb2ef0c2d9f4158ee6fac7e23864d))

## [0.6.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.5.0...dcc-mcp-maya-mgear-v0.6.0) (2026-06-16)


### Features

* define canonical DCC-MCP skill repo layout ([2c30806](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2c308068ff96660655e2035f6a2ba79ada14eb7d))
* define canonical DCC-MCP skill repo layout ([27a97fa](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/27a97fa2132abb96da77927fb5d4d8bdc0137ebe))
* define canonical DCC-MCP skill repo layout ([#46](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/46)) ([2c30806](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2c308068ff96660655e2035f6a2ba79ada14eb7d))


### Bug Fixes

* remove unused yaml import in validate_skill_package.py ([e12fdab](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/e12fdabd787767c923df974705deccbe9b5117e4))
* ruff format (reformat test_package.py and validate_skill_package.py) ([339ea04](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/339ea040fce0c65b08eada3387041dbe8fcb31a5))

## [0.5.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.5...dcc-mcp-maya-mgear-v0.5.0) (2026-06-16)


### Features

* add UPV math-node dependency probe to inspect_mgear_environment ([f103371](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/f103371a7d89ece9820b10be5bb82648786c9159)), closes [#38](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/38)

## [0.4.5](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.4...dcc-mcp-maya-mgear-v0.4.5) (2026-06-15)


### Bug Fixes

* resolve SKILL.md strict-loader rejection and create_shifter_guide_from_template reporting ([7899c13](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7899c13d830f7ff8042ebfd53aae2c58171a7c1c))

## [0.4.4](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.3...dcc-mcp-maya-mgear-v0.4.4) (2026-06-14)


### Bug Fixes

* allow SKILL.md in release PR file validation ([98f633a](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/98f633a444877fb73ccdb382f79a6be78cee1a93))
* replace tomllib with re for cross-python version parsing ([ae4549c](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/ae4549c3bf6459247306b2c51933a042b7400718))
* set dcc=maya, add version field, filter __init__.py from components ([c1a4150](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/c1a415035da1c8a7c888fb12c9052f1327d4137b))

## [0.4.3](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.2...dcc-mcp-maya-mgear-v0.4.3) (2026-06-14)


### Bug Fixes

* add tools.yaml reference to SKILL.md metadata ([2cb40b2](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2cb40b2286ba92904644c1839dd2daccc9c6ab0b))

## [0.4.2](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.1...dcc-mcp-maya-mgear-v0.4.2) (2026-06-13)


### Bug Fixes

* normalize mgear dependency metadata ([af12b1f](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/af12b1f965657c5d49e3eab7b132d28b5dbfe794))

## [0.4.1](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.4.0...dcc-mcp-maya-mgear-v0.4.1) (2026-06-07)


### Bug Fixes

* create missing directories before writing marketplace.json copies ([59f565d](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/59f565d40488941da86d977eebd500346e86ad3b))

## [0.4.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.3.0...dcc-mcp-maya-mgear-v0.4.0) (2026-06-07)


### Features

* auto-sync marketplace.json version on release ([9f45f31](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/9f45f31528446cb05e79e8981aa3c2b8f94189e7))


### Bug Fixes

* address code review findings for PR [#18](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/18) ([82baac7](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/82baac718f3301d100d2baaf9bafc1a74924473e))

## [0.3.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.2.0...dcc-mcp-maya-mgear-v0.3.0) (2026-06-07)


### Features

* add marketplace-compatible layout at repo root ([b0c1b8c](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/b0c1b8c493a164a30441a60526db81736198be48))
* update marketplace registration for Phase 2 CLI install/update/uninstall ([a50f37b](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/a50f37b88ae5e81a42cbd9d20666267a5af066ca))

## [0.2.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.1.0...dcc-mcp-maya-mgear-v0.2.0) (2026-06-06)


### Features

* add marketplace registration with icon and docs ([3d95d6b](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/3d95d6bc707ab327a177a2257ee3f9a689a609e6))
* **ci:** add marketplace.json schema validation job ([d876348](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/d8763481c73815e2ab567ce1ac5944be707ec5e4))
* implement 5 MVP mGear Shifter typed tools ([a8c4f8a](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/a8c4f8a99cf370626ef8647862de2fc92eb99368))
* initial scaffold for dcc-mcp-maya-mgear ([ade0818](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/ade081859526017b08f7af0510479e52d3a2fb98))


### Bug Fixes

* add issues: write permission to release workflow ([b512358](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/b51235811108abfbc87d467316499439de85af96))
* add issues: write permission to release workflow ([7760106](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/776010699722fe1d57ff1c9fa96069b283794b41))
* address re-review — real guide detection, error-on-null, guide-not-found ([8aaded5](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/8aaded5b5f5f0d64d97ac55aa3c4244fcc19e203))
* align tool calls to real mGear upstream function signatures ([1551154](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/1551154c6055179a852213e42346bb8a59a4f69a))
* bind 4 core tools to verified real mGear upstream APIs ([d42d126](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/d42d12634ff363584a1ab22466dc91c6f03cbb1e))
* **ci:** harden marketplace validation — entry type guard, require install ([#13](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/13)) ([94864c4](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/94864c448d4c09ad55994bc88abf8b6e4170b4fa))
* **ci:** remove explicit token from release-please-action ([f50b5dd](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/f50b5dd122ca3ee538bbab26417300bbc29f95ac))
* **ci:** use correct action versions (v4/v5) ([8c3caf8](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/8c3caf80de6a1efa196dd42c7d88f32d1b44d49a))
* **ci:** use heredoc syntax for inline Python in skill-lint job ([91a6fe9](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/91a6fe905b80d6dd1edaecf07cb8129f90c93872))
* marketplace install.ref and document source-add requirement ([8b29900](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/8b299004a5d52e879f28924190e5788cc03bd0c2))
* marketplace install.ref and document source-add requirement ([1bce6ea](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/1bce6ea210e86595d738c569043290a3c89a5adc))
* rebind runtime API to verified mGear upstream interfaces ([9751c4e](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/9751c4e9a0b558d5cd2ae2121d570453caf59905))
* replace missing PERSONAL_ACCESS_TOKEN with GITHUB_TOKEN in release workflow ([fb51ceb](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/fb51ceb52e63b06d9d374dc821f2ef82fd1d2f01))
