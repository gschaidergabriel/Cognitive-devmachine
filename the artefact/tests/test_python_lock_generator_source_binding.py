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


def test_python_lock_generator_checks_out_exact_source_and_uses_product_inputs():
    text = _workflow_text()
    assert "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" in text
    assert "persist-credentials: false" in text
    assert "PRODUCT_DOCKERFILE='the artefact/Dockerfile'" in text
    assert "PRODUCT_REQUIREMENTS='the artefact/requirements.txt'" in text
    assert "PRODUCT_SOURCE_LOCK='the artefact/SOURCE_LOCK.json'" in text
    assert "sed -n -E" in text
    assert "[Ff][Rr][Oo][Mm]" in text
    assert "ARG BASE_IMAGE=" not in text
    assert "^python:[^[:space:]]+@sha256:[0-9a-f]{64}$" in text
    assert 'REQUIREMENTS_SHA256="$(sha256sum "$PRODUCT_REQUIREMENTS"' in text
    assert 'SOURCE_LOCK_SHA256="$(sha256sum "$PRODUCT_SOURCE_LOCK"' in text
    assert '-v "$GITHUB_WORKSPACE:/workspace:ro"' in text
    assert "PRODUCT_REQUIREMENTS='/workspace/the artefact/requirements.txt'" in text
    assert "PRODUCT_SOURCE_LOCK='/workspace/the artefact/SOURCE_LOCK.json'" in text
    assert "EXPECTED_SOURCE_LOCK_SHA256" in text


def test_current_product_first_from_is_exact_digest_pinned_python():
    image = _first_from_image()
    assert re.fullmatch(r"python:\S+@sha256:[0-9a-f]{64}", image), image
    assert image in DOCKERFILE.read_text(encoding="utf-8")


def test_python_lock_generator_uses_source_locked_python_313_supported_pip_tools():
    lock = _source_lock()
    pip_tools = lock["python_lock_generator"]["pip_tools"]
    assert pip_tools == {
        "version": "7.5.3",
        "wheel": "pip_tools-7.5.3-py3-none-any.whl",
        "sha256": "3aac0c473240ae90db7213c033401f345b05197293ccbdd2704e52e7a783785e",
        "source": "PyPI pip-tools 7.5.3 bdist_wheel metadata",
    }
    assert any(
        "transitive generator dependencies" in gate
        for gate in lock["known_open_supply_chain_gates"]
    )

    text = _workflow_text()
    assert "lock['python_lock_generator']['pip_tools']" in text
    assert "pip-tools==$PIP_TOOLS_VERSION" in text
    assert "--only-binary=:all: --no-deps" in text
    assert 'PIP_TOOLS_WHEEL_PATH="/tmp/pip-tools-bootstrap/$PIP_TOOLS_WHEEL"' in text
    assert "PIP_TOOLS_WHEEL_SHA256=" in text
    assert '"$PIP_TOOLS_SHA256" "$PIP_TOOLS_WHEEL_PATH" | sha256sum -c -' in text
    assert '--only-binary=:all: --report /tmp/generator-install-report.json' in text
    assert '"$PIP_TOOLS_WHEEL_PATH"' in text
    assert 'pip-compile --version | grep -F "version $PIP_TOOLS_VERSION"' in text
    assert "GENERATOR_BASE_FREEZE_SHA256=" in text
    assert "GENERATOR_BASE_ENVIRONMENT_BEGIN" in text
    assert "GENERATOR_BASE_ENVIRONMENT_END" in text
    assert "GENERATOR_FREEZE_SHA256=" in text
    assert "GENERATOR_ENVIRONMENT_BEGIN" in text
    assert "GENERATOR_ENVIRONMENT_END" in text
    assert "'pip-tools==7.5.3'" not in text
    assert "'pip-tools==7.5.0'" not in text


def test_python_lock_generator_emits_transitive_bootstrap_download_provenance_without_promoting_it_to_lock():
    text = _workflow_text()
    assert "generator-install-report.json" in text
    assert "report.get('version') != '1'" in text
    assert "download_info" in text
    assert "archive_info" in text
    assert "hashes" in text
    assert "GENERATOR_DEPENDENCY_NON_HTTPS_SOURCE" in text
    assert "GENERATOR_DEPENDENCY_SHA256_MISSING" in text
    assert "SOURCE_LOCK" in text
    assert "GENERATOR_DOWNLOAD_PROVENANCE_SHA256=" in text
    assert "GENERATOR_DOWNLOAD_PROVENANCE_BEGIN" in text
    assert "GENERATOR_DOWNLOAD_PROVENANCE_END" in text
    assert "generator.download-provenance" in text
    assert "transitive bootstrap" in text
    assert "not itself a trusted lock" in text


def test_python_lock_generator_does_not_embed_parallel_product_semantics_or_experiment():
    text = _workflow_text()
    assert "cat >/tmp/requirements.in <<'EOF'" not in text
    assert "PyJWT[crypto]==" not in text
    assert "fastapi==" not in text
    assert "uvicorn[standard]==" not in text
    assert "mcp==" not in text
    assert "python:3." not in text
    assert "HASH_LESION" not in text
    assert "requirements.lock.lesion" not in text


def test_python_lock_generator_verifies_reproducibility_hash_enforcement_and_selected_wheel_provenance():
    text = _workflow_text()
    assert text.count("pip-compile --generate-hashes") == 2
    assert "diff -u /tmp/requirements.lock.1 /tmp/requirements.lock.2" in text
    assert "--only-binary=:all: --require-hashes" in text
    assert "LOCK_SHA256=" in text
    assert "WHEELHOUSE_FILE_COUNT=" in text
    assert "WHEELHOUSE_SHA256_BEGIN" in text
    assert "WHEELHOUSE_SHA256_END" in text
    assert 'sha256sum "$wheel"' in text
    assert '${wheel##*/}' in text
    assert "LC_ALL=C sort" in text
    assert "LOCK_GZIP_B64=" in text
