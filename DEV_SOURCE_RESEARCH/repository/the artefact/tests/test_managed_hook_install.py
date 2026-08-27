from __future__ import annotations

import json
from pathlib import Path


def test_managed_lifecycle_hooks_are_in_oci_build_contract():
    root = Path(__file__).parents[1]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    settings = json.loads((root / "policy" / "managed-settings.json").read_text(encoding="utf-8"))

    assert "policy/managed-settings.json /etc/claude-code/managed-settings.json" in dockerfile
    assert "chmod 0444 /etc/claude-code/managed-mcp.json /etc/claude-code/managed-settings.json" in dockerfile

    hooks = settings["hooks"]
    assert set(hooks) == {"UserPromptSubmit", "Stop", "StopFailure"}
    commands = {
        name: hooks[name][0]["hooks"][0]["command"]
        for name in hooks
    }
    assert commands == {
        "UserPromptSubmit": "/usr/local/bin/python -m clayverse.terminal_hooks user_prompt",
        "Stop": "/usr/local/bin/python -m clayverse.terminal_hooks stop",
        "StopFailure": "/usr/local/bin/python -m clayverse.terminal_hooks stop_failure",
    }
