from __future__ import annotations

import json
from pathlib import Path


def test_managed_clayverse_mcp_is_startup_bound():
    root = Path(__file__).parents[1]
    managed = json.loads((root / "policy" / "managed-mcp.json").read_text())

    assert list(managed) == ["mcpServers"]
    assert list(managed["mcpServers"]) == ["clayverse"]
    assert managed["mcpServers"]["clayverse"] == {
        "type": "stdio",
        "command": "/usr/local/bin/python",
        "args": ["-m", "clayverse.mcp_server"],
        "alwaysLoad": True,
    }
