from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_oci_build_context_is_allowlisted():
    rules = (ROOT / ".dockerignore").read_text().splitlines()
    assert "*" in rules
    for required in (
        "!Dockerfile",
        "!requirements.txt",
        "!clayverse/",
        "!clayverse/**",
        "!policy/",
        "!policy/**",
        "!EntityOS",
    ):
        assert required in rules


def test_sensitive_and_runtime_material_are_not_reincluded():
    rules = (ROOT / ".dockerignore").read_text()
    for forbidden in ("!.env", "!receipts", "!tests", "!.git", "!unified.db", "!state"):
        assert forbidden not in rules
