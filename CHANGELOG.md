# Changelog

## [0.7.0](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/compare/dcc-mcp-maya-mgear-v0.6.0...dcc-mcp-maya-mgear-v0.7.0) (2026-06-23)


### Features

* add import_shifter_sample_template tool for full-rig sample templates ([705fa41](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/705fa41b9d850a62cd5e02d453711d4deffccbca))
* add marketplace registration with icon and docs ([926e60c](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/926e60c203baa1304017b3cce11937ef029cfe41))
* add marketplace-compatible layout at repo root ([7b6509d](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7b6509d319df2c774102bbec3944bb8df3c9e5cb))
* add mgear-import-to-scene skill (PIP-1896) ([fae2a85](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/fae2a850b6e450a6a68cc90c781c4981bcc023f8))
* add mgear-import-to-scene skill with contract-aligned import and mGear context probe ([5ef3617](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/5ef3617c95ac96d9c3fef6a768301aaaf6b8a0ae))
* add UPV math-node dependency probe to inspect_mgear_environment ([49d4b1d](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/49d4b1d6f3772484a9bb2fd33ba73152c9c82ae2)), closes [#38](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/38)
* auto-sync marketplace.json version on release ([c9fb14a](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/c9fb14ac0b678a94840e6fe06063acd36b664433))
* **ci:** add marketplace.json schema validation job ([3e83e7f](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/3e83e7f223692a8f9728b2924a36e5a77fa49ccd))
* define canonical DCC-MCP skill repo layout ([2bc9aea](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2bc9aea46a3e705f65fe9c45a89986546bbd7362))
* define canonical DCC-MCP skill repo layout ([e694fdd](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/e694fdd98a1676aab3f6648ff9ff65ae7e095376))
* define canonical DCC-MCP skill repo layout ([#46](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/46)) ([2bc9aea](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2bc9aea46a3e705f65fe9c45a89986546bbd7362))
* implement 5 MVP mGear Shifter typed tools ([25866f7](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/25866f708b3209a680993485702530cec62d1a7a))
* initial scaffold for dcc-mcp-maya-mgear ([ade0818](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/ade081859526017b08f7af0510479e52d3a2fb98))
* update marketplace registration for Phase 2 CLI install/update/uninstall ([f767df9](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/f767df9b593b006c88037094566073c53bf16e0e))


### Bug Fixes

* add issues: write permission to release workflow ([7cd11dd](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7cd11dd8a6d03294e9ba51f17c76b7542b3aad7b))
* add issues: write permission to release workflow ([91cf769](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/91cf769e907865ac5d056b44178a927f1dc3196a))
* add tools.yaml reference to SKILL.md metadata ([7088fd6](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7088fd682977ffda8d9b61f71ba5326d8b6097c3))
* address code review findings for PR [#18](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/18) ([26977b6](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/26977b6e994c76d2947c2252a56baf48e4f370bb))
* address re-review — real guide detection, error-on-null, guide-not-found ([972bb27](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/972bb27b3158e08e5986cfa28317dddaf3764697))
* align tool calls to real mGear upstream function signatures ([7e76996](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7e76996fdd7dc3f0b706121071f3b526972811e8))
* allow SKILL.md in release PR file validation ([905ff51](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/905ff5173c8145ea82f1e48e60375ec574eada87))
* bind 4 core tools to verified real mGear upstream APIs ([9e4fbe7](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/9e4fbe7099fc6f1917d53437f64d6f5151df35fb))
* **ci:** harden marketplace validation — entry type guard, require install ([#13](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/issues/13)) ([a610851](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/a6108513e8317b4a5812902e1845aefb9047c040))
* **ci:** remove explicit token from release-please-action ([5274278](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/52742786c2264ab150b88f0052d38013e2015b85))
* **ci:** use correct action versions (v4/v5) ([e049f26](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/e049f2601958cd9e993393e0d057aa959be15511))
* **ci:** use heredoc syntax for inline Python in skill-lint job ([6a97b46](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/6a97b460d919a23e228346d082ff2fa8b7736b2b))
* create missing directories before writing marketplace.json copies ([8763571](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/8763571b6645d0a68a2ac0dab28da5529063a6b8))
* marketplace install.ref and document source-add requirement ([41839ba](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/41839ba384e90714d0db3753a27bf1001c359aa9))
* marketplace install.ref and document source-add requirement ([4fb1309](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/4fb13097aed877360c6fe3553727652dd21d50e6))
* normalize mgear dependency metadata ([3372a3a](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/3372a3a8e596058c1bc50d87354938089817b6c4))
* rebind runtime API to verified mGear upstream interfaces ([39381d8](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/39381d8831eddd98df7f40c69d13509e9152dd77))
* remove unused yaml import in validate_skill_package.py ([4abfe63](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/4abfe6350cb595270b354b413e03eaeb5991aec8))
* replace missing PERSONAL_ACCESS_TOKEN with GITHUB_TOKEN in release workflow ([86b85f4](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/86b85f45a8040850792841bf94002273128b0fb3))
* replace tomllib with re for cross-python version parsing ([1954564](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/195456484aa9092712eadd1c138741ad6806bc45))
* resolve CI lint/skill validation failures (ruff, tool count, mirror file) ([71b7104](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/71b7104bbc5d40eea5a2725241725d6c004d146d))
* resolve SKILL.md strict-loader rejection and create_shifter_guide_from_template reporting ([32f56dc](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/32f56dc004bfdae6b842c582ba490c9e3034c7a4))
* ruff format (reformat test_package.py and validate_skill_package.py) ([def0e53](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/def0e535faf20072dc1cfc0fdcaaf364d9e28989))
* set dcc=maya, add version field, filter __init__.py from components ([2cffbcb](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/2cffbcb9a3a5c6fa02b1bd715260d471bc788c4f))
* sync marketplace.json version to 0.6.0 for release ([8f3b34c](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/8f3b34c086e960384b1c7c247223787d0f482799))
* sync SKILL.md version to v0.6.0 for release ([976a473](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/976a473888e86b0461ba5e436369f52b220a807d))
* update SKILL.md version to v0.4.5 in release-please bump ([7beccef](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/7beccefc45f57c3e58e6a72cd301714fb05b4c74))


### Documentation

* rewrite README as marketplace listing ([f7e1e85](https://github.com/dcc-mcp/dcc-mcp-maya-mgear/commit/f7e1e8503c3e4a7c4b8a74d01a4975ee0bebf79a))

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
