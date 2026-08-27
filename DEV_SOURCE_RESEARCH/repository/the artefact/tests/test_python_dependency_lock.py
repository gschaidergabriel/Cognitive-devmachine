from __future__ import annotations

import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARTEFACT = HERE.parent
REQUIREMENTS = ARTEFACT / "requirements.txt"
LOCK = ARTEFACT / "requirements.lock.txt"
DOCKERFILE = ARTEFACT / "Dockerfile"
DOCKERIGNORE = ARTEFACT / ".dockerignore"
SOURCE_LOCK = ARTEFACT / "SOURCE_LOCK.json"
WORKFLOW = ARTEFACT.parents[0] / ".github" / "workflows" / "clayverse-python-lock-generator.yml"


def _lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]


def test_top_level_python_requirements_are_exactly_version_pinned():
    requirements = [
        line for line in _lines(REQUIREMENTS)
        if line and not line.startswith("#")
    ]
    assert requirements
    for requirement in requirements:
        assert re.fullmatch(r"[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_.,-]+\])?==[^;\s]+", requirement), requirement


def test_python_hash_lock_transition_is_fail_closed_and_truthful():
    """A materialized lock and product consumption must appear as one coherent state.

    Until exact resolver execution has produced requirements.lock.txt, SOURCE_LOCK must
    continue to expose the gap and the Dockerfile must not pretend hash enforcement.
    Once the lock exists, Dockerfile/.dockerignore must consume it with --require-hashes
    and the old open-gate statement must be retired in the same source state.
    """
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    dockerignore = DOCKERIGNORE.read_text(encoding="utf-8")
    source_lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    open_gates = source_lock.get("known_open_supply_chain_gates", [])
    python_gap = "Python requirements are version pinned but not yet installed with --require-hashes"

    if not LOCK.exists():
        assert python_gap in open_gates
        assert "COPY requirements.lock.txt" not in dockerfile
        assert "--require-hashes" not in dockerfile
        return

    assert LOCK.stat().st_size > 0
    lock_text = LOCK.read_text(encoding="utf-8")
    assert "--hash=sha256:" in lock_text
    assert "COPY requirements.lock.txt" in dockerfile
    assert "--require-hashes" in dockerfile
    assert "requirements.lock.txt" in dockerfile
    assert "!requirements.lock.txt" in dockerignore.splitlines()
    assert python_gap not in open_gates


def test_lock_generator_tracks_the_atomic_transition_surface():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for path in (
        "the artefact/requirements.txt",
        "the artefact/requirements.lock.txt",
        "the artefact/Dockerfile",
        "the artefact/SOURCE_LOCK.json",
        "the artefact/tests/test_python_dependency_lock.py",
        "the artefact/tests/test_python_lock_generator_source_binding.py",
    ):
        assert path in workflow
    assert workflow.count("pip-compile --generate-hashes") == 2
    assert "diff -u /tmp/requirements.lock.1 /tmp/requirements.lock.2" in workflow
    assert "--only-binary=:all: --require-hashes" in workflow
