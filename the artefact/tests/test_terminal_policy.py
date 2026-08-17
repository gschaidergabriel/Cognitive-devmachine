from __future__ import annotations

import json
from pathlib import Path

from clayverse.terminal import TerminalSupervisor


def test_default_terminal_is_interactive_and_tool_dark():
    supervisor = TerminalSupervisor()
    argv = supervisor.for_user("gabriel").argv

    assert argv[0] == "claude"
    assert "-p" not in argv and "--print" not in argv
    tools = argv.index("--tools")
    assert argv[tools + 1] == ""
    assert "--strict-mcp-config" in argv
    mcp = argv.index("--mcp-config")
    assert argv[mcp + 1] == TerminalSupervisor.MANAGED_MCP_CONFIG
    assert supervisor.for_user("andreas").argv == argv


def test_managed_mcp_policy_exposes_only_clayverse_stdio_server():
    managed = Path(__file__).parents[1] / "policy" / "managed-mcp.json"
    payload = json.loads(managed.read_text())
    assert list(payload["mcpServers"]) == ["clayverse"]
    server = payload["mcpServers"]["clayverse"]
    assert server["type"] == "stdio"
    assert server["command"] == "/usr/local/bin/python"
    assert server["args"] == ["-m", "clayverse.mcp_server"]
