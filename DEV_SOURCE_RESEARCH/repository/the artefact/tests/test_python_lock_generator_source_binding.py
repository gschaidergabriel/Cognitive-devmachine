from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "clayverse-python-lock-generator.yml"
DOCKERFILE = REPO_ROOT / "the artefact" / "Dockerfile"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


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
    assert "sed -n -E" in text
    assert "[Ff][Rr][Oo][Mm]" in text
    assert "ARG BASE_IMAGE=" not in text
    assert "^python:[^[:space:]]+@sha256:[0-9a-f]{64}$" in text
    assert 'REQUIREMENTS_SHA256="$(sha256sum "$PRODUCT_REQUIREMENTS"' in text
    assert '-v "$GITHUB_WORKSPACE:/workspace:ro"' in text
    assert "PRODUCT_REQUIREMENTS='/workspace/the artefact/requirements.txt'" in text


def test_current_product_first_from_is_exact_digest_pinned_python():
    image = _first_from_image()
    assert re.fullmatch(r"python:\S+@sha256:[0-9a-f]{64}", image), image
    assert image in DOCKERFILE.read_text(encoding="utf-8")


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


def test_python_lock_generator_verifies_reproducibility_and_hash_enforcement():
    text = _workflow_text()
    assert text.count("pip-compile --generate-hashes") == 2
    assert "diff -u /tmp/requirements.lock.1 /tmp/requirements.lock.2" in text
    assert "--only-binary=:all: --require-hashes" in text
    assert "LOCK_SHA256=" in text
    assert "WHEELHOUSE_FILE_COUNT=" in text
    assert "LOCK_GZIP_B64=" in text
