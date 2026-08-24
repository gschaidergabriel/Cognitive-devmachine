#!/usr/bin/env python3
"""Fail-closed Trigger-1 intermediate -> exact-source -> gate-v3 pipeline.

This is an orchestration adapter, not a new evidence authority. It reuses the current
intermediate causal experiment, the canonical exact-source envelope primitives, the
intermediate promotion bridge, and the existing promotion gate. The existing self-hosted
workflow still consumes the historical ``trigger1_local_activation_api_result.json``
filename, so this pipeline emits that file only as a compatibility projection of the
stronger intermediate result plus bounded pipeline provenance.

A direct steering candidate survives only when:
- the intermediate experiment produced its declared PASS and candidate;
- exact repository/runtime/model/provider-fence binding passed;
- source identity stayed stable through the promotion bridge and gate execution; and
- the bridge emitted a v3-compatible direct candidate.

No canonical EntityOS/HCU, full J-Space, or training credit is minted here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from trigger1_exact_source_envelope import (
    CANDIDATE_NAME as INTERMEDIATE_CANDIDATE_NAME,
    RECEIPT_NAME as EXACT_SOURCE_RECEIPT_NAME,
    RESULT_NAME as INTERMEDIATE_RESULT_NAME,
    build_envelope,
    capture_source_identity,
)

PIPELINE_SCHEMA = "CLAY_TRIGGER1_INTERMEDIATE_V3_PIPELINE/v1"
COMPAT_RESULT_NAME = "trigger1_local_activation_api_result.json"
DIRECT_CANDIDATE_NAME = "trigger1_direct_steering_candidate.json"
PROMOTION_GATE_NAME = "promotion_gate.json"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_object(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"JSON_OBJECT_UNAVAILABLE:{path.name}:{type(exc).__name__}") from exc
    if not isinstance(obj, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return obj


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def pipeline_paths(root: Path) -> dict[str, Path]:
    tools = root / "tools"
    return {
        "pipeline": tools / "trigger1_midlayer_v3_pipeline.py",
        "workflow_launcher": tools / "trigger1_local_qwen06_midlayer_causal.sh",
        "exact_source": tools / "trigger1_exact_source_envelope.py",
        "launcher": tools / "trigger1_local_qwen06_intermediate.sh",
        "executor": tools / "trigger1_local_qwen06_intermediate_execute.py",
        "protocol": tools / "trigger1_intermediate_contrastive_protocol.py",
        "activation_runtime": tools / "trigger1_local_qwen06_activation_api_execute.py",
        "bridge": tools / "trigger1_intermediate_promotion_bridge.py",
        "gate": tools / "trigger1_jspace_promotion_gate.py",
    }


def blocked_compat(reason: str, *, pipeline_rc: int) -> dict[str, Any]:
    payload = {
        "schema": "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1",
        "status": "BLOCKED_TRIGGER1_V3_PIPELINE",
        "reason": reason,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
        "credit_scope": "NONE",
        "pipeline": {
            "schema": PIPELINE_SCHEMA,
            "pipeline_returncode": pipeline_rc,
            "direct_candidate_present": False,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
        },
    }
    payload["result_sha256"] = canonical_sha(payload)
    return payload


def emit_compat_result(
    *,
    out: Path,
    envelope: dict[str, Any],
    intermediate_rc: int,
    bridge_rc: int | None,
    gate_rc: int | None,
    source_stable_through_gate: bool,
) -> dict[str, Any]:
    result_path = out / INTERMEDIATE_RESULT_NAME
    try:
        result = read_object(result_path)
    except RuntimeError as exc:
        result = blocked_compat(str(exc), pipeline_rc=4)

    result.pop("result_sha256", None)
    direct = out / DIRECT_CANDIDATE_NAME
    gate = out / PROMOTION_GATE_NAME
    exact_summary = {
        "schema": envelope.get("schema"),
        "status": envelope.get("status"),
        "receipt_sha256": envelope.get("receipt_sha256"),
        "source_identity_sha256": (envelope.get("source_identity_pre") or {}).get("source_identity_sha256"),
        "source_stable_across_intermediate": envelope.get("source_stable_across_run"),
        "source_stable_through_gate": source_stable_through_gate,
        "runtime_required_fields_bound": envelope.get("runtime_required_fields_bound"),
        "model_identity_bound": envelope.get("model_identity_bound"),
        "provider_fence_pass": envelope.get("provider_fence_pass"),
    }
    result["exact_source_envelope"] = exact_summary
    result["pipeline"] = {
        "schema": PIPELINE_SCHEMA,
        "intermediate_returncode": intermediate_rc,
        "promotion_bridge_returncode": bridge_rc,
        "promotion_gate_returncode": gate_rc,
        "direct_candidate_present": direct.is_file(),
        "direct_candidate_sha256": sha256_file(direct),
        "promotion_gate_present": gate.is_file(),
        "promotion_gate_sha256": sha256_file(gate),
        "source_stable_through_gate": source_stable_through_gate,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
    }
    result["result_sha256"] = canonical_sha(result)
    write_json(out / COMPAT_RESULT_NAME, result)
    return result


def run_pipeline(root: Path, out: Path) -> int:
    root = root.resolve()
    out = out.resolve()
    # Never create an output path inside the repository merely to report the rejection;
    # doing so would itself mutate the exact source identity we are protecting.
    if inside(out, root):
        return 6
    out.mkdir(parents=True, exist_ok=True)

    direct = out / DIRECT_CANDIDATE_NAME
    compat = out / COMPAT_RESULT_NAME
    gate_out = out / PROMOTION_GATE_NAME
    for stale in (direct, compat, gate_out):
        if stale.exists():
            stale.unlink()

    paths = pipeline_paths(root)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        write_json(compat, blocked_compat("EXECUTOR_MISSING:" + ",".join(sorted(missing)), pipeline_rc=6))
        return 6

    executor_paths = list(paths.values())
    pre = capture_source_identity(root, executor_paths)
    intermediate = subprocess.run(
        ["bash", str(paths["launcher"]), str(out)],
        cwd=str(root),
        check=False,
    )
    post_intermediate = capture_source_identity(root, executor_paths)

    try:
        envelope, exact = build_envelope(
            root=root,
            out_dir=out,
            pre=pre,
            post=post_intermediate,
            delegated_returncode=intermediate.returncode,
        )
    except Exception as exc:
        envelope = {
            "schema": "CLAY_TRIGGER1_EXACT_SOURCE_ENVELOPE/v1",
            "status": "BLOCKED_EXACT_SOURCE_BINDING",
            "credit_scope": "NONE",
            "canonical_or_whole_product_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "delegated_returncode": intermediate.returncode,
            "reason": f"{type(exc).__name__}:{str(exc)[:1200]}",
            "source_identity_pre": pre,
            "source_identity_post": post_intermediate,
        }
        exact = False

    bridge_rc: int | None = None
    gate_rc: int | None = None
    source_stable_through_gate = bool(exact)
    intermediate_result_path = out / INTERMEDIATE_RESULT_NAME
    intermediate_candidate_path = out / INTERMEDIATE_CANDIDATE_NAME

    if exact and intermediate.returncode == 0 and intermediate_candidate_path.is_file():
        bridge = subprocess.run(
            [
                sys.executable,
                str(paths["bridge"]),
                "--result",
                str(intermediate_result_path),
                "--candidate",
                str(intermediate_candidate_path),
                "--output",
                str(direct),
            ],
            cwd=str(root),
            check=False,
        )
        bridge_rc = bridge.returncode
        if bridge.returncode != 0 and direct.exists():
            direct.unlink()

        if bridge.returncode == 0 and direct.is_file():
            with gate_out.open("wb") as fh:
                gate = subprocess.run(
                    [sys.executable, str(paths["gate"]), "--candidate", str(direct)],
                    cwd=str(root),
                    stdout=fh,
                    check=False,
                )
            gate_rc = gate.returncode

    post_gate = capture_source_identity(root, executor_paths)
    source_stable_through_gate = bool(
        exact and pre.get("source_identity_sha256") == post_gate.get("source_identity_sha256")
    )
    if not source_stable_through_gate:
        exact = False
        if direct.exists():
            direct.unlink()
        if gate_out.exists():
            gate_out.unlink()
        envelope["status"] = "BLOCKED_EXACT_SOURCE_BINDING"
        envelope["promotion_candidate_retained"] = False

    envelope["pipeline_schema"] = PIPELINE_SCHEMA
    envelope["source_identity_post_gate"] = post_gate
    envelope["source_stable_through_gate"] = source_stable_through_gate
    envelope["promotion_bridge_returncode"] = bridge_rc
    envelope["promotion_gate_returncode"] = gate_rc
    envelope["direct_candidate_present"] = direct.is_file()
    envelope["direct_candidate_sha256"] = sha256_file(direct)
    envelope["promotion_gate_sha256"] = sha256_file(gate_out)
    envelope.pop("receipt_sha256", None)
    envelope["receipt_sha256"] = canonical_sha(envelope)
    write_json(out / EXACT_SOURCE_RECEIPT_NAME, envelope)

    emit_compat_result(
        out=out,
        envelope=envelope,
        intermediate_rc=intermediate.returncode,
        bridge_rc=bridge_rc,
        gate_rc=gate_rc,
        source_stable_through_gate=source_stable_through_gate,
    )

    if not exact:
        return 4
    if intermediate.returncode != 0:
        return int(intermediate.returncode)
    if bridge_rc != 0 or not direct.is_file():
        return 5
    if gate_rc != 0 or not gate_out.is_file():
        return 5
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--repo-root", default=None)
    args = ap.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    return run_pipeline(root, Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
