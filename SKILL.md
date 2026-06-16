---
name: maya-mgear
description: mGear Shifter deep integration — inspect environments, list components, create guides, and build rigs.
metadata:
  dcc-mcp:
    version: v0.5.0
    dcc: maya
    display_name: Maya mGear
    group: maya.job.pipeline
    default_icon: rigging
    affinity: main
    marketplace: dcc-mcp-maya-mgear
    tools: tools.yaml
    depends:
      - maya-rigging
    execution: sync
    permissions:
      - maya
    examples:
      - "Inspect the mGear environment"
      - "List all Shifter components in the scene"
      - "Create a Shifter guide from template"
      - "Build a rig from an existing guide"
      - "Export a Shifter guide template"
    contact:
      name: dcc-mcp team
      url: https://github.com/dcc-mcp/dcc-mcp-maya-mgear
    install:
      add_source: "dcc-mcp marketplace add dcc-mcp/dcc-mcp-maya-mgear"
      then_install: "dcc-mcp marketplace install dcc-mcp-maya-mgear"
---
