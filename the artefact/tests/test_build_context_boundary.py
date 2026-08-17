from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RETIRED_RUNTIME_MODULES = {
    "adapters.py",
    "api.py",
    "engine.py",
    "inference_protocol.py",
    "terminal.py",
}

EXPECTED_POLICY_FILES = {
    "managed-mcp.json",
    "managed-settings.json",
    "managed-tmux.conf",
    "deny-shell",
}


def _included_files(rules: list[str], directory: str) -> set[str]:
    prefix = f"!{directory}/"
    return {
        rule[len(prefix):]
        for rule in rules
        if rule.startswith(prefix) and rule != f"!{directory}/" and "*" not in rule
    }


def test_oci_build_context_is_file_allowlisted():
    rules = (ROOT / ".dockerignore").read_text().splitlines()
    assert "*" in rules
    for required in (
        "!Dockerfile",
        "!requirements.txt",
        "!SOURCE_LOCK.json",
        "!build/install_pinned_apt.py",
        "!build/install_pinned_xterm.py",
        "!build/install_pinned_claude.py",
        "!clayverse/",
        "!policy/",
        "!entityos.lock.json",
        "!EntityOS",
    ):
        assert required in rules

    # A subtree wildcard defeats the default-deny boundary for untracked bytes.
    assert "!clayverse/**" not in rules
    assert "!policy/**" not in rules

    runtime_files = {
        path.name
        for path in (ROOT / "clayverse").iterdir()
        if path.is_file() and path.suffix == ".py"
    }
    assert RETIRED_RUNTIME_MODULES <= runtime_files
    assert _included_files(rules, "clayverse") == runtime_files - RETIRED_RUNTIME_MODULES
    assert _included_files(rules, "policy") == EXPECTED_POLICY_FILES


def test_sensitive_and_runtime_material_are_not_reincluded():
    rules = (ROOT / ".dockerignore").read_text()
    for forbidden in ("!.env", "!receipts", "!tests", "!.git", "!unified.db", "!state"):
        assert forbidden not in rules
