#!/usr/bin/env python3
"""Fail-closed resolver for the current EntityOS/HCU owner product target.

The newest explicit owner directive remains authority. This module only provides a
machine-readable resolution index plus drift diagnostics so stale secondary surfaces
cannot silently redefine the current architecture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

INDEX_REL = Path("research_entity/continuity/CURRENT_OWNER_PRODUCT_TARGET.json")
BOOTSTRAP_REL = Path("research_entity/continuity/BOOTSTRAP_MINIMAL.json")
PROGRAM_REL = Path("research_entity/rooms/PROGRAM_STATE.json")
EXPECTED_SCHEMA = "CLAY_CURRENT_OWNER_PRODUCT_TARGET/v1"

REQUIRED_OWNER_MARKERS = (
    "CURRENT OWNER TARGET / HIGHEST PRECEDENCE WHERE CONFLICTING",
    "VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE",
    "The cognitive grid is not fixed to GRID10.",
    "`N` is a runtime parameter, not the definition of the architecture.",
    "`SIMULATE COGNITION; STORE DURABLE DATA.`",
    "No unproven activation-level access to Claude Code may be claimed.",
    "GRID10 may be used as one benchmark configuration, but has no special final authority.",
)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path}: root must be an object")
    return value


def _secondary_drift(repo_root: Path) -> list[dict[str, str]]:
    drift: list[dict[str, str]] = []

    bootstrap_path = repo_root / BOOTSTRAP_REL
    if bootstrap_path.exists():
        b = _load_json(bootstrap_path)
        st = b.get("scale_target")
        if type(st) is dict and st.get("baseline_logical_cells") == 10:
            drift.append({
                "surface": str(BOOTSTRAP_REL),
                "field": "scale_target.baseline_logical_cells",
                "reason": "fixed-10 baseline wording lags owner RUNTIME_VARIABLE_N target; GRID10 is benchmark-only",
            })

    program_path = repo_root / PROGRAM_REL
    if program_path.exists():
        p = _load_json(program_path)
        mp = p.get("mode_policy")
        if type(mp) is dict and mp.get("baseline") == "GRID10":
            drift.append({
                "surface": str(PROGRAM_REL),
                "field": "mode_policy.baseline",
                "reason": "GRID10 cannot be the architectural baseline after owner correction; N is runtime-variable",
            })
        sp = p.get("scale_policy")
        if type(sp) is dict and sp.get("baseline_logical_cells") == 10:
            drift.append({
                "surface": str(PROGRAM_REL),
                "field": "scale_policy.baseline_logical_cells",
                "reason": "fixed-10 baseline wording lags owner RUNTIME_VARIABLE_N target",
            })
    return drift


def resolve_owner_target(repo_root: str | Path, *, require_secondary_alignment: bool = False) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    index_path = root / INDEX_REL
    if not index_path.is_file():
        raise FileNotFoundError(f"missing owner target resolution index: {INDEX_REL}")

    idx = _load_json(index_path)
    if idx.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("owner target resolution index schema mismatch")
    if idx.get("status") != "NON_AUTHORITATIVE_RESOLUTION_INDEX_NEWEST_EXPLICIT_OWNER_STILL_WINS":
        raise ValueError("resolution index must not claim owner authority")
    if idx.get("grid_size_policy") != "RUNTIME_VARIABLE_N":
        raise ValueError("current owner target must resolve grid size as RUNTIME_VARIABLE_N")
    if idx.get("grid10_status") != "BENCHMARK_FIXTURE_ONLY_NO_SPECIAL_FINAL_AUTHORITY":
        raise ValueError("GRID10 status mismatch")

    owner_rel_raw = idx.get("owner_directive_path")
    if type(owner_rel_raw) is not str or not owner_rel_raw:
        raise ValueError("owner_directive_path missing")
    owner_rel = Path(owner_rel_raw)
    if owner_rel.is_absolute() or ".." in owner_rel.parts:
        raise ValueError("owner_directive_path must be repo-relative")
    owner_path = root / owner_rel
    data = owner_path.read_bytes()

    expected_blob = idx.get("owner_directive_git_blob_sha1")
    if type(expected_blob) is not str or len(expected_blob) != 40:
        raise ValueError("owner_directive_git_blob_sha1 malformed")
    observed_blob = git_blob_sha1(data)
    if observed_blob != expected_blob:
        raise ValueError(
            f"owner directive identity mismatch: expected {expected_blob}, observed {observed_blob}"
        )

    text = data.decode("utf-8")
    missing = [marker for marker in REQUIRED_OWNER_MARKERS if marker not in text]
    if missing:
        raise ValueError(f"owner directive missing required invariants: {missing}")

    finished = idx.get("finished_runtime")
    if finished != ["VARIABLE_COGNITIVE_GRID", "PERSISTENT_DATABASE", "CLAUDE_CODE"]:
        raise ValueError("finished_runtime mismatch")
    if idx.get("global_jspace_bridge") != "STRONGEST_EXPOSED_INTERFACE_ONLY_NO_UNPROVEN_CLAUDE_CODE_ACTIVATION_ACCESS":
        raise ValueError("Global J-Space evidence ceiling mismatch")

    drift = _secondary_drift(root)
    if require_secondary_alignment and drift:
        raise ValueError(f"secondary authority surfaces lag owner correction: {drift}")

    return {
        "schema": "CLAY_OWNER_TARGET_RESOLUTION_RESULT/v1",
        "status": "PASS" if not drift else "PASS_OWNER_AUTHORITY_WITH_SECONDARY_SURFACE_DRIFT",
        "persistent_entity": idx.get("persistent_entity"),
        "product": idx.get("product"),
        "architecture": idx.get("architecture"),
        "owner_directive_path": str(owner_rel),
        "owner_directive_git_blob_sha1": observed_blob,
        "grid_size_policy": idx.get("grid_size_policy"),
        "grid10_status": idx.get("grid10_status"),
        "finished_runtime": finished,
        "durable_state_rule": idx.get("durable_state_rule"),
        "claude_code_role": idx.get("claude_code_role"),
        "global_jspace_bridge": idx.get("global_jspace_bridge"),
        "small_model_target": idx.get("small_model_target"),
        "go_priority_chain": idx.get("go_priority_chain"),
        "credit_boundary": idx.get("credit_boundary"),
        "secondary_surface_drift": drift,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--require-secondary-alignment", action="store_true")
    args = ap.parse_args()
    try:
        result = resolve_owner_target(
            args.repo_root, require_secondary_alignment=args.require_secondary_alignment
        )
    except Exception as exc:
        print(json.dumps({"schema": "CLAY_OWNER_TARGET_RESOLUTION_RESULT/v1", "status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
