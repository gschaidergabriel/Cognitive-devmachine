from __future__ import annotations

import ast
from pathlib import Path


ARTEFACT_ROOT = Path(__file__).resolve().parents[1]


def _literal_dockerignore_denies() -> set[str]:
    lines = (ARTEFACT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    return {
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#") and not line.startswith("!")
    }


def test_final_mistral_probe_dependencies_are_not_excluded_from_oci_context():
    probe_path = ARTEFACT_ROOT / "clayverse" / "final_acceptance_probe.py"
    tree = ast.parse(probe_path.read_text(encoding="utf-8"))
    local_imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module
    }

    assert {"adapters", "engine", "entityos_bridge", "store"} <= local_imports

    denied = _literal_dockerignore_denies()
    for module in ("adapters", "engine", "inference_protocol", "final_acceptance_probe"):
        assert f"clayverse/{module}.py" not in denied

    dockerfile = (ARTEFACT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY clayverse ./clayverse" in dockerfile


def test_retired_public_alternate_python_surfaces_remain_outside_oci_context():
    denied = _literal_dockerignore_denies()
    assert "clayverse/api.py" in denied
    assert "clayverse/terminal.py" in denied
