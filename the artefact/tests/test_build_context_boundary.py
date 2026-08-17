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
        "!build-assets/",
        "build-assets/*",
        "!build-assets/entityos/",
        "build-assets/entityos/*",
        "!build-assets/entityos/.keep",
        "!build-assets/entityos/EntityOS",
    ):
        assert required in rules
    assert "!EntityOS" not in rules
    assert "!build-assets/**" not in rules


def test_sensitive_and_runtime_material_are_not_reincluded():
    rules = (ROOT / ".dockerignore").read_text()
    for forbidden in ("!.env", "!receipts", "!tests", "!.git", "!unified.db", "!state"):
        assert forbidden not in rules
