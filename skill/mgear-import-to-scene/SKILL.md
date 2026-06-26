---
name: mgear-import-to-scene
description: Import asset files into Maya scene with mGear rigging context awareness, following the dcc_mcp_core.asset_import contract.
license: MIT
compatibility: "dcc-mcp-core 0.18+"
metadata:
  dcc-mcp:
    version: v0.6.0
    dcc: maya
    layer: domain
    tags:
      - maya
      - mgear
      - import
      - asset
      - fbx
      - usd
      - rigging
    search-hint: "maya mgear, import asset, import to scene, fbx import, usd import, asset descriptor, rigging context"
    tools: tools.yaml
    depends:
      - maya-import-to-scene
      - maya-rigging
---
