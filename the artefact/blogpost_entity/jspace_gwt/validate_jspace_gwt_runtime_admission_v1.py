#!/usr/bin/env python3
"""Compose canonical J-Space/GWT boot validation with exact checkout identity.

This wrapper adds no J-Space, GWT, state, truth, or effect authority. It reuses the
canonical JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 validator, then proves that the
receipt's source commit/tree are the clean Git checkout containing this validator
and the admitted manifest/source-lock files.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import validate_jspace_gwt_boot_binding_v1 as boot  # noqa: E402

SCHEMA = "JSPACE_GWT_RUNTIME_ADMISSION/v1"


class RuntimeAdmissionError(ValueError):
    pass


def fail(code: str) -> None:
    raise RuntimeAdmissionError(code)


def _git(repo_root: Path, *args: str) -> str:
    try:
        cp = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"SOURCE_GIT_UNAVAILABLE:{type(exc).__name__}")
    if cp.returncode != 0:
        detail = (cp.stderr or cp.stdout).strip().replace("\n", " ")[:240]
        fail(f"SOURCE_GIT_COMMAND_FAILED:{args[0]}:{detail}")
    return cp.stdout.strip()


def _require_under_root(path: Path, repo_root: Path, label: str) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        fail(f"{label}_OUTSIDE_SOURCE_ROOT")


def validate_checkout_binding(data: dict, repo_root: Path) -> dict[str, str]:
    root = repo_root.resolve()
    if not root.is_dir():
        fail("SOURCE_ROOT_NOT_DIRECTORY")

    top = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        fail("SOURCE_ROOT_NOT_GIT_TOPLEVEL")

    source = boot.req_obj(data, "source")
    if boot.req_bool(source, "dirty"):
        fail("SOURCE_RECEIPT_DIRTY_NOT_RUNTIME_ADMISSIBLE")

    actual_head = _git(root, "rev-parse", "--verify", "HEAD")
    actual_tree = _git(root, "rev-parse", "--verify", "HEAD^{tree}")
    actual_dirty = bool(_git(root, "status", "--porcelain=v1", "--untracked-files=all"))
    if actual_dirty:
        fail("SOURCE_CHECKOUT_DIRTY")

    if boot.req_sha(source, "main_sha", 40) != actual_head:
        fail("SOURCE_HEAD_MISMATCH")
    if boot.req_sha(source, "tree_sha", 40) != actual_tree:
        fail("SOURCE_TREE_MISMATCH")

    return {"main_sha": actual_head, "tree_sha": actual_tree}


def validate_runtime_admission(
    data: dict,
    manifest_path: Path,
    source_lock_path: Path,
    source_lock: dict,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    root = repo_root.resolve()
    _require_under_root(Path(__file__), root, "VALIDATOR")
    _require_under_root(HERE / "validate_jspace_gwt_boot_binding_v1.py", root, "BOOT_VALIDATOR")
    _require_under_root(manifest_path, root, "BUNDLED_MANIFEST")
    _require_under_root(source_lock_path, root, "SOURCE_LOCK")

    boot.validate(data)
    boot.validate_manifest_binding(data, manifest_path, source_lock)
    return validate_checkout_binding(data, root)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: validate_jspace_gwt_runtime_admission_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json",
            file=sys.stderr,
        )
        return 2
    try:
        receipt_path = Path(sys.argv[1])
        manifest_path = Path(sys.argv[2])
        source_lock_path = Path(sys.argv[3])
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        source_lock = json.loads(source_lock_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            fail("TOP_LEVEL_NOT_OBJECT")
        if not isinstance(source_lock, dict):
            fail("SOURCE_LOCK_TOP_LEVEL_NOT_OBJECT")
        bound = validate_runtime_admission(data, manifest_path, source_lock_path, source_lock)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        RuntimeAdmissionError,
        boot.ValidationError,
        boot.BundledManifestError,
    ) as exc:
        print(f"FAIL {exc}")
        return 1
    print(
        "PASS JSPACE_GWT_RUNTIME_ADMISSION/v1 "
        f"main_sha={bound['main_sha']} tree_sha={bound['tree_sha']} clean=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
