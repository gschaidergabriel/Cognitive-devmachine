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


def test_python_lock_generator_source_locks_complete_linux_py313_bootstrap_set():
    lock = _source_lock()
    generator = lock["python_lock_generator"]
    pip_tools = generator["pip_tools"]
    assert pip_tools == {
        "version": "7.5.3",
        "wheel": "pip_tools-7.5.3-py3-none-any.whl",
        "sha256": "3aac0c473240ae90db7213c033401f345b05197293ccbdd2704e52e7a783785e",
        "source": "PyPI pip-tools 7.5.3 bdist_wheel metadata",
    }

    dependencies = generator["bootstrap_dependencies"]
    expected = {
        "build==1.2.2.post1": ("build-1.2.2.post1-py3-none-any.whl", "1d61c0887fa860c01971625baae8bdd338e517b836a2f70dd1f7aa3a6b2fc5b5"),
        "click==8.3.3": ("click-8.3.3-py3-none-any.whl", "a2bf429bb3033c89fa4936ffb35d5cb471e3719e1f3c8a7c3fff0b8314305613"),
        "packaging==24.2": ("packaging-24.2-py3-none-any.whl", "09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759"),
        "pip==26.1.2": ("pip-26.1.2-py3-none-any.whl", "382ff9f685ee3bc25864f820aa50505825f10f5458ffff07e30a6d96e5715cab"),
        "pyproject-hooks==1.2.0": ("pyproject_hooks-1.2.0-py3-none-any.whl", "9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913"),
        "setuptools==83.0.0": ("setuptools-83.0.0-py3-none-any.whl", "29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3"),
        "wheel==0.46.2": ("wheel-0.46.2-py3-none-any.whl", "33ae60725d69eaa249bc1982e739943c23b34b58d51f1cb6253453773aca6e65"),
    }
    observed = {
        item["requirement"]: (item["wheel"], item["sha256"])
        for item in dependencies
    }
    assert observed == expected
    assert any(
        "source-locked" in gate and "no-extra-download closure" in gate
        for gate in lock["known_open_supply_chain_gates"]
    )


def test_python_lock_generator_downloads_hash_checked_bootstrap_then_installs_offline():
    text = _workflow_text()
    assert "generator['bootstrap_dependencies']" in text
    assert "GENERATOR_BOOTSTRAP_CLOSURE_MISMATCH" in text
    assert "generator-bootstrap.requirements" in text
    assert "generator-bootstrap.expected" in text
    assert "GENERATOR_BOOTSTRAP_EXPECTED_COUNT=" in text
    assert "--only-binary=:all: --require-hashes" in text
    assert "-r /tmp/generator-bootstrap.requirements" in text
    assert "-d /tmp/pip-tools-bootstrap" in text
    assert "sha256sum -c /tmp/generator-bootstrap.expected" in text
    assert "GENERATOR_BOOTSTRAP_SHA256_BEGIN" in text
    assert "GENERATOR_BOOTSTRAP_SHA256_END" in text
    assert "--no-index --find-links=/tmp/pip-tools-bootstrap" in text
    assert "python -m pip --version | grep -F 'pip 26.1.2 '" in text
    assert "pip-compile --version | grep -F 'version 7.5.3'" in text
    assert "--only-binary=:all: --no-deps" not in text
    assert "generator-install-report.json" not in text


def test_python_lock_generator_preserves_base_and_final_environment_evidence():
    text = _workflow_text()
    assert "GENERATOR_BASE_FREEZE_SHA256=" in text
    assert "GENERATOR_BASE_ENVIRONMENT_BEGIN" in text
    assert "GENERATOR_BASE_ENVIRONMENT_END" in text
    assert "GENERATOR_FREEZE_SHA256=" in text
    assert "GENERATOR_ENVIRONMENT_BEGIN" in text
    assert "GENERATOR_ENVIRONMENT_END" in text


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
    assert "LOCK_PATH='/tmp/requirements.lock'" in text
    assert "LOCK_FIRST='/tmp/requirements.lock.first'" in text
    assert text.count('-o "$LOCK_PATH" /tmp/requirements.in') == 2
    assert 'cp "$LOCK_PATH" "$LOCK_FIRST"' in text
    assert text.count('rm -f "$LOCK_PATH"') >= 2
    assert 'diff -u "$LOCK_FIRST" "$LOCK_PATH"' in text
    assert "/tmp/requirements.lock.1" not in text
    assert "/tmp/requirements.lock.2" not in text
    assert "--only-binary=:all: --require-hashes" in text
    assert "LOCK_SHA256=" in text
    assert "WHEELHOUSE_FILE_COUNT=" in text
    assert "WHEELHOUSE_SHA256_BEGIN" in text
    assert "WHEELHOUSE_SHA256_END" in text
    assert 'sha256sum "$wheel"' in text
    assert '${wheel##*/}' in text
    assert "LC_ALL=C sort" in text
    assert "LOCK_GZIP_B64=" in text
