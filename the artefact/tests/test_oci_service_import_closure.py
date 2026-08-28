from __future__ import annotations

import ast
import fnmatch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "clayverse"
DOCKERIGNORE = ROOT / ".dockerignore"


def _docker_excluded_python_patterns() -> tuple[str, ...]:
    patterns: list[str] = []
    for raw in DOCKERIGNORE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if line.startswith("clayverse/") and (line.endswith(".py") or "*.py" in line):
            patterns.append(line)
    return tuple(patterns)


def _relative_import_targets(source: Path) -> list[Path]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    relative = source.relative_to(PACKAGE)
    package_parts = list(relative.parent.parts)
    targets: list[Path] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level < 1:
            continue
        ascend = node.level - 1
        if ascend > len(package_parts):
            continue
        base = package_parts[: len(package_parts) - ascend]
        module_parts = node.module.split(".") if node.module else []
        resolved = base + module_parts

        if node.module:
            file_candidate = PACKAGE.joinpath(*resolved).with_suffix(".py")
            package_candidate = PACKAGE.joinpath(*resolved, "__init__.py")
            if file_candidate.is_file():
                targets.append(file_candidate)
            elif package_candidate.is_file():
                targets.append(package_candidate)
        else:
            for alias in node.names:
                candidate = PACKAGE.joinpath(*(base + [alias.name])).with_suffix(".py")
                if candidate.is_file():
                    targets.append(candidate)
    return targets


def _docker_path(path: Path) -> str:
    return "clayverse/" + path.relative_to(PACKAGE).as_posix()


def _is_excluded(path: Path, patterns: tuple[str, ...]) -> bool:
    value = _docker_path(path)
    return any(fnmatch.fnmatchcase(value, pattern) for pattern in patterns)


def test_service_import_graph_never_reaches_docker_excluded_module():
    """The production entry point must be importable from exactly the OCI-admitted bytes."""

    excluded = _docker_excluded_python_patterns()
    pending: list[tuple[Path, tuple[str, ...]]] = [(PACKAGE / "service.py", ("clayverse/service.py",))]
    visited: set[Path] = set()

    while pending:
        source, chain = pending.pop()
        source = source.resolve()
        if source in visited:
            continue
        visited.add(source)
        for target in _relative_import_targets(source):
            target_display = _docker_path(target)
            next_chain = chain + (target_display,)
            assert not _is_excluded(target, excluded), (
                "production service import graph reaches a module excluded by .dockerignore: "
                + " -> ".join(next_chain)
            )
            pending.append((target, next_chain))


def test_retired_mistral_probe_is_a_fail_closed_tombstone():
    source = (PACKAGE / "final_acceptance_probe.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "adapters" not in imported
    assert "engine" not in imported
    assert "MISTRAL_ACCEPTANCE_PROBE_RETIRED" in source
