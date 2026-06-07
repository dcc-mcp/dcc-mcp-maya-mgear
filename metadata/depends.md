---
dependencies:
  maya-rigging:
    required: true
    reason: Uses detect_rig_frameworks from maya-rigging skill for mGear detection.
    version: "*"
---

# Dependency: maya-rigging

The `maya-mgear` skill depends on the `maya-rigging` skill for framework detection.
Specifically, `detect_rig_frameworks` is used to check whether mGear is available in
the current Maya environment.

If `maya-rigging` is not available, the mGear tools will still function in degraded
mode (reporting mGear as unavailable).
