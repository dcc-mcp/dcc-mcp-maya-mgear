"""Release automation must fail closed rather than suppress its PR CI events."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "${{ secrets.PERSONAL_ACCESS_TOKEN }}"


def _release_steps():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["release-please"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["if"] == "github.ref == 'refs/heads/main'"
    steps = job["steps"]
    action_index = next(
        i for i, step in enumerate(steps) if step.get("id") == "release"
    )
    assert action_index > 0, "release-please needs a preceding token preflight"
    guard, action = steps[action_index - 1 : action_index + 1]
    assert guard["name"] == "Require organization release token"
    assert guard["shell"] == "bash"
    assert guard["env"] == {"PERSONAL_ACCESS_TOKEN": TOKEN}
    assert "if" not in guard
    assert "continue-on-error" not in guard
    return workflow, guard, action


def test_release_please_requires_organization_token():
    workflow, _, action = _release_steps()
    assert action["uses"] == "googleapis/release-please-action@v5"
    assert action["with"]["token"] == TOKEN
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if step.get("uses", "").startswith("actions/checkout@"):
                assert "token" not in step.get("with", {})


@pytest.mark.parametrize("token", [None, "", "synthetic-token-do-not-print"])
def test_release_token_guard_rejects_missing_values_without_leaking(
    token: Optional[str],
):
    _, guard, _ = _release_steps()
    env = os.environ.copy()
    env.pop("PERSONAL_ACCESS_TOKEN", None)
    if token is not None:
        env["PERSONAL_ACCESS_TOKEN"] = token
    result = subprocess.run(
        [_bash(), "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", guard["run"]],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if token:
        assert result.returncode == 0, output
        assert token not in output
    else:
        assert result.returncode != 0
        assert "::error::" in output
        assert "PERSONAL_ACCESS_TOKEN" in output


def _bash() -> str:
    bash = shutil.which("bash")
    assert bash, "Bash is required to exercise the Ubuntu release preflight"
    return bash
