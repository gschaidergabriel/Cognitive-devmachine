from __future__ import annotations

import json
from pathlib import Path


def test_claude_native_updates_are_fully_disabled_across_image_policy_and_launch():
    root = Path(__file__).parents[1]
    settings = json.loads((root / "policy" / "managed-settings.json").read_text())
    terminal_source = (root / "clayverse" / "terminal_sessions.py").read_text()
    dockerfile = (root / "Dockerfile").read_text()

    assert settings["env"]["DISABLE_UPDATES"] == "1"
    assert '"DISABLE_UPDATES=1"' in terminal_source
    assert "DISABLE_UPDATES=1" in dockerfile
    assert "DISABLE_AUTOUPDATER" not in terminal_source
    assert "DISABLE_AUTOUPDATER" not in dockerfile
