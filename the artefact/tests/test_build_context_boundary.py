from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_oci_build_context_is_allowlisted():
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
        "!clayverse/**",
        "!policy/",
        "!policy/**",
        "!entityos.lock.json",
        "!EntityOS",
    ):
        assert required in rules


def test_sensitive_and_runtime_material_are_not_reincluded():
    rules = (ROOT / ".dockerignore").read_text()
    for forbidden in ("!.env", "!receipts", "!tests", "!.git", "!unified.db", "!state"):
        assert forbidden not in rules
