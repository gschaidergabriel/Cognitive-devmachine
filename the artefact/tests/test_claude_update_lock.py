from __future__ import annotations

import json
from pathlib import Path


def test_claude_native_updates_are_fully_disabled_across_image_policy_and_launch():
    root = Path(__file__).parents[1]
    settings = json.loads((root / "policy" / "managed-settings.json").read_text())
    terminal_source = (root / "clayverse" / "terminal_sessions.py").read_text()
    dockerfile = (root / "Dockerfile").read_text()

    # DISABLE_UPDATES is the stronger managed/image lock: it blocks both background
    # and manual update paths. The sanitized launch also carries the explicit
    # background-updater fence before managed settings are loaded.
    assert settings["env"]["DISABLE_UPDATES"] == "1"
    assert "DISABLE_UPDATES=1" in dockerfile
    assert '"DISABLE_AUTOUPDATER=1"' in terminal_source
    assert "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1" in terminal_source
