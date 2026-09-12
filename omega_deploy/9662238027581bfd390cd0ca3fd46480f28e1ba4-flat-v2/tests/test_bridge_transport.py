from omega.bridge_transport import BridgeTarget, command_from_effect


def test_command_binds_selected_host_identity():
    target = BridgeTarget(
        organ_id="host:andreas-maco", owner_id="andreas", machine_id="andreas-maco",
        control_branch="chatgpt-local-andreas-maco-control",
        results_branch="chatgpt-local-andreas-maco-results",
    )
    cmd = command_from_effect(
        "effect_abcdef",
        target,
        {"op":"exec","command":"printf omega","cwd":"/tmp","timeout_seconds":99999},
    )
    assert cmd["owner"] == "andreas"
    assert cmd["machine_id"] == "andreas-maco"
    assert cmd["command_id"].startswith("omega-")
    assert cmd["timeout_seconds"] == 3600


def test_read_file_payload_is_preserved():
    target = BridgeTarget(
        organ_id="host:ai-core-node", owner_id="gabriel", machine_id="ai-core-node",
        control_branch="c", results_branch="r",
    )
    cmd = command_from_effect("effect_xyz", target, {"op":"read_file","path":"/tmp/x"})
    assert cmd["op"] == "read_file"
    assert cmd["path"] == "/tmp/x"
    assert cmd["owner"] == "gabriel"
