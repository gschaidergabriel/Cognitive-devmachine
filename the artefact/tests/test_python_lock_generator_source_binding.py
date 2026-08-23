from pathlib import Path
import json
import re

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "clayverse-python-lock-generator.yml"
DOCKERFILE = REPO_ROOT / "the artefact" / "Dockerfile"
SOURCE_LOCK = REPO_ROOT / "the artefact" / "SOURCE_LOCK.json"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _source_lock() -> dict:
    return json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))


def _first_from_image() -> str:
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*FROM\s+(\S+)", line, re.IGNORECASE)
        if match:
            return match.group(1)
    raise AssertionError("Dockerfile has no FROM image")


def test_exact_pr_source_and_product_inputs_are_bound():
    text = _workflow_text()
    assert "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" in text
    assert "persist-credentials: false" in text
    assert "ref: ${{ github.event.pull_request.head.sha }}" in text
    assert "EXPECTED_PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}" in text
    assert 'ACTUAL_PR_HEAD_SHA="$(git rev-parse HEAD)"' in text
    assert 'test "$ACTUAL_PR_HEAD_SHA" = "$EXPECTED_PR_HEAD_SHA"' in text
    assert "PRODUCT_DOCKERFILE='the artefact/Dockerfile'" in text
    assert "PRODUCT_REQUIREMENTS='the artefact/requirements.txt'" in text
    assert "PRODUCT_SOURCE_LOCK='the artefact/SOURCE_LOCK.json'" in text
    assert '-v "$GITHUB_WORKSPACE:/workspace:ro"' in text


def test_product_first_from_matches_source_lock():
    image = _first_from_image()
    source_base = _source_lock()["base_image"]
    assert re.fullmatch(r"python:\S+@sha256:[0-9a-f]{64}", image), image
    assert image == f"{source_base['reference']}@{source_base['index_digest']}"


def test_base_image_drift_fails_before_container_execution():
    text = _workflow_text()
    marker = 'if [ "$BASE_IMAGE" != "$SOURCE_LOCK_BASE_IMAGE" ]; then'
    assert "SOURCE_LOCK_BASE_IMAGE_MISSING" in text
    assert "SOURCE_LOCK_BASE_REFERENCE_INVALID" in text
    assert "SOURCE_LOCK_BASE_DIGEST_INVALID" in text
    assert "Dockerfile/SOURCE_LOCK base image drift" in text
    assert text.index(marker) < text.index("docker run --rm -i")


def test_source_lock_has_complete_linux_py313_generator_bootstrap_set():
    generator = _source_lock()["python_lock_generator"]
    assert generator["pip_tools"]["version"] == "7.5.3"
    assert generator["pip_tools"]["wheel"] == "pip_tools-7.5.3-py3-none-any.whl"
    assert generator["pip_tools"]["sha256"] == "3aac0c473240ae90db7213c033401f345b05197293ccbdd2704e52e7a783785e"
    expected = {
        "build==1.2.2.post1": ("build-1.2.2.post1-py3-none-any.whl", "1d61c0887fa860c01971625baae8bdd338e517b836a2f70dd1f7aa3a6b2fc5b5"),
        "click==8.3.3": ("click-8.3.3-py3-none-any.whl", "a2bf429bb3033c89fa4936ffb35d5cb471e3719e1f3c8a7c3fff0b8314305613"),
        "packaging==24.2": ("packaging-24.2-py3-none-any.whl", "09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759"),
        "pip==26.1.2": ("pip-26.1.2-py3-none-any.whl", "382ff9f685ee3bc25864f820aa50505825f10f5458ffff07e30a6d96e5715cab"),
        "pyproject-hooks==1.2.0": ("pyproject_hooks-1.2.0-py3-none-any.whl", "9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913"),
        "setuptools==83.0.0": ("setuptools-83.0.0-py3-none-any.whl", "29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3"),
        "wheel==0.46.2": ("wheel-0.46.2-py3-none-any.whl", "33ae60725d69eaa249bc1982e739943c23b34b58d51f1cb6253453773aca6e65"),
    }
    observed = {item["requirement"]: (item["wheel"], item["sha256"]) for item in generator["bootstrap_dependencies"]}
    assert observed == expected


def test_bootstrap_is_hash_checked_then_installed_offline():
    text = _workflow_text()
    assert "GENERATOR_BOOTSTRAP_CLOSURE_MISMATCH" in text
    assert "generator-bootstrap.requirements" in text
    assert "generator-bootstrap.expected" in text
    assert "--only-binary=:all: --require-hashes" in text
    assert "sha256sum -c /tmp/generator-bootstrap.expected" in text
    assert "--no-index --find-links=/tmp/pip-tools-bootstrap" in text
    assert "python -m pip --version | grep -F 'pip 26.1.2 '" in text
    assert "pip-compile --version | grep -F 'version 7.5.3'" in text


def test_reproducible_lock_uses_stable_output_path_and_wheel_receipts():
    text = _workflow_text()
    assert text.count("pip-compile --generate-hashes") == 2
    assert "LOCK_PATH='/tmp/requirements.lock'" in text
    assert "LOCK_FIRST='/tmp/requirements.lock.first'" in text
    assert text.count('-o "$LOCK_PATH" /tmp/requirements.in') == 2
    assert 'diff -u "$LOCK_FIRST" "$LOCK_PATH"' in text
    assert "WHEELHOUSE_SHA256_BEGIN" in text
    assert "WHEELHOUSE_SHA256_END" in text
    assert 'sha256sum "$wheel"' in text
    assert "LOCK_GZIP_B64=" in text


def test_no_parallel_product_semantics_or_experiment_are_embedded():
    text = _workflow_text()
    for forbidden in (
        "cat >/tmp/requirements.in <<'EOF'",
        "PyJWT[crypto]==",
        "fastapi==",
        "uvicorn[standard]==",
        "mcp==",
        "python:3.",
        "HASH_LESION",
        "requirements.lock.lesion",
    ):
        assert forbidden not in text
