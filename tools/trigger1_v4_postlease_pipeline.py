#!/usr/bin/env python3
"""Purpose-specific post-lease Trigger1 v4 evidence pipeline.

This module does NOT acquire an unusual-experiment lease. It is intentionally inert
unless the retained dispatcher already admitted a canonical atomic `go` claim and
exported that claim identity into the environment.

After lease admission it composes the strongest current local Qwen path without
creating a second execution authority:

    exact-source envelope
      -> intermediate contrastive experiment
      -> intermediate promotion bridge
      -> Trigger1 promotion gate
      -> one bounded pipeline receipt

The pipeline never mints canonical EntityOS/HCU/J-Space/training credit. A positive
promotion verdict remains a candidate requiring the enclosing admitted runtime receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_EXPERIMENT = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1"
PIPELINE_SCHEMA = "CLAY_TRIGGER1_V4_POSTLEASE_PIPELINE/v1"
RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(r"^ts_[0-9]{8}T[0-9]{12}Z__p_[0-9a-f]{64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

PROVIDER_ENV_PATTERNS = (
    "OPENAI",
    "ANTHROPIC",
    "GROQ",
    "MISTRAL",
    "NVIDIA",
    "NGC",
    "OPENROUTER",
    "TOGETHER",
)
HF_TOKEN_NAMES = {
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
}


class PipelineBlocked(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _required(env: Mapping[str, str], key: str) -> str:
    value = str(env.get(key) or "").strip()
    if not value:
        raise PipelineBlocked(f"LEASE_ENV_REQUIRED:{key}")
    return value


def validate_postlease_environment(env: Mapping[str, str]) -> dict[str, str]:
    """Fail closed before any intervention unless canonical lease identity is present."""
    if env.get("TRIGGER1_LEASE_ADMITTED") != "true":
        raise PipelineBlocked("CANONICAL_ATOMIC_LEASE_NOT_ADMITTED")

    trigger_key = _required(env, "TRIGGER1_TRIGGER_KEY")
    if not (RID_RE.fullmatch(trigger_key) or TS_RE.fullmatch(trigger_key)):
        raise PipelineBlocked("TRIGGER_KEY_NONCANONICAL")

    experiment = _required(env, "TRIGGER1_EXPERIMENT_NAME")
    if experiment != EXPECTED_EXPERIMENT:
        raise PipelineBlocked("LEASE_EXPERIMENT_IDENTITY_MISMATCH")

    claim_sha = _required(env, "TRIGGER1_CLAIM_SHA256")
    if not SHA256_RE.fullmatch(claim_sha):
        raise PipelineBlocked("LEASE_CLAIM_SHA256_INVALID")

    source_head = _required(env, "TRIGGER1_SOURCE_HEAD")
    source_tree = _required(env, "TRIGGER1_SOURCE_TREE")
    if not HEAD_RE.fullmatch(source_head) or not HEAD_RE.fullmatch(source_tree):
        raise PipelineBlocked("LEASE_SOURCE_IDENTITY_INVALID")
    if str(env.get("TRIGGER1_SOURCE_DIRTY") or "").lower() != "false":
        raise PipelineBlocked("LEASE_SOURCE_NOT_CLEAN")

    claim_path = _required(env, "TRIGGER1_CLAIM_PATH")
    claimant = _required(env, "TRIGGER1_CLAIMANT_ORGAN")
    return {
        "trigger_key": trigger_key,
        "experiment_name": experiment,
        "claim_sha256": claim_sha,
        "claim_path": claim_path,
        "claimant_organ": claimant,
        "source_head": source_head,
        "source_tree": source_tree,
    }


def sanitized_environment(env: Mapping[str, str], out_dir: Path) -> dict[str, str]:
    """Return a child environment with external provider credentials removed."""
    clean = {str(k): str(v) for k, v in env.items()}
    for name in list(clean):
        upper = name.upper()
        if name in HF_TOKEN_NAMES:
            clean.pop(name, None)
            continue
        if "KEY" in upper and any(marker in upper for marker in PROVIDER_ENV_PATTERNS):
            clean.pop(name, None)
    clean["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    clean["HF_TOKEN_PATH"] = str(out_dir / "no-hf-token")
    return clean


def _load_object(path: Path, reason: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PipelineBlocked(f"{reason}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise PipelineBlocked(reason)
    return value


def _run(command: list[str], *, env: Mapping[str, str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def execute_pipeline(out_dir: Path, env: Mapping[str, str] | None = None) -> tuple[dict[str, Any], int]:
    """Execute the fixed v4 chain after lease admission and return receipt + exit code."""
    source_env = dict(os.environ if env is None else env)
    lease = validate_postlease_environment(source_env)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    child_env = sanitized_environment(source_env, out_dir)
    token_path = Path(child_env["HF_TOKEN_PATH"])
    token_path.unlink(missing_ok=True)

    exact_script = ROOT / "tools/trigger1_exact_source_envelope.py"
    bridge_script = ROOT / "tools/trigger1_intermediate_promotion_bridge.py"
    gate_script = ROOT / "tools/trigger1_jspace_promotion_gate.py"
    for path in (exact_script, bridge_script, gate_script):
        if not path.is_file():
            raise PipelineBlocked(f"PIPELINE_COMPONENT_MISSING:{path.name}")

    exact_proc = _run(
        [sys.executable, str(exact_script), "--output-dir", str(out_dir)],
        env=child_env,
    )

    exact_receipt_path = out_dir / "trigger1_intermediate_exact_source_receipt.json"
    result_path = out_dir / "trigger1_intermediate_result.json"
    intermediate_candidate_path = out_dir / "trigger1_intermediate_candidate.json"
    direct_candidate_path = out_dir / "trigger1_direct_steering_candidate_v4.json"
    gate_path = out_dir / "trigger1_promotion_gate_v4.json"

    exact_receipt = _load_object(exact_receipt_path, "EXACT_SOURCE_RECEIPT_REQUIRED")
    exact_bound = exact_receipt.get("status") == "PASS_EXACT_SOURCE_BINDING"
    result = _load_object(result_path, "INTERMEDIATE_RESULT_REQUIRED")

    bridge_rc: int | None = None
    bridge_output = ""
    gate_rc: int | None = None
    gate: dict[str, Any]

    if exact_bound and result.get("status") == "PASS" and intermediate_candidate_path.is_file():
        bridge_proc = _run(
            [
                sys.executable,
                str(bridge_script),
                "--result",
                str(result_path),
                "--candidate",
                str(intermediate_candidate_path),
                "--output",
                str(direct_candidate_path),
            ],
            env=child_env,
        )
        bridge_rc = bridge_proc.returncode
        bridge_output = bridge_proc.stdout[-4000:]
        if bridge_rc == 0 and direct_candidate_path.is_file():
            gate_proc = _run(
                [sys.executable, str(gate_script), "--candidate", str(direct_candidate_path)],
                env=child_env,
            )
            gate_rc = gate_proc.returncode
            try:
                gate_value = json.loads(gate_proc.stdout)
            except Exception:
                gate_value = {
                    "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
                    "owner_trigger1_goal_credit_candidate": False,
                    "mechanism_runtime_vector_credit_candidate": False,
                    "failures": ["PROMOTION_GATE_OUTPUT_INVALID"],
                }
            gate = gate_value if isinstance(gate_value, dict) else {
                "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
                "owner_trigger1_goal_credit_candidate": False,
                "mechanism_runtime_vector_credit_candidate": False,
                "failures": ["PROMOTION_GATE_OUTPUT_NOT_OBJECT"],
            }
        else:
            gate = {
                "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
                "owner_trigger1_goal_credit_candidate": False,
                "mechanism_runtime_vector_credit_candidate": False,
                "failures": ["INTERMEDIATE_PROMOTION_BRIDGE_FAILED"],
            }
    else:
        gate = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
            "owner_trigger1_goal_credit_candidate": False,
            "mechanism_runtime_vector_credit_candidate": False,
            "failures": [
                "EXACT_SOURCE_BINDING_REQUIRED" if not exact_bound else "INTERMEDIATE_SCIENTIFIC_PASS_REQUIRED"
            ],
        }

    gate_path.write_text(json.dumps(gate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    receipt: dict[str, Any] = {
        "schema": PIPELINE_SCHEMA,
        "lease": lease,
        "pipeline_components": {
            "exact_source_envelope_sha256": sha256_file(exact_script),
            "intermediate_bridge_sha256": sha256_file(bridge_script),
            "promotion_gate_sha256": sha256_file(gate_script),
        },
        "exact_source": {
            "process_exit_code": exact_proc.returncode,
            "receipt_sha256": sha256_file(exact_receipt_path),
            "status": exact_receipt.get("status"),
            "source_stable_across_run": exact_receipt.get("source_stable_across_run"),
            "delegated_source_matches_pre": exact_receipt.get("delegated_source_matches_pre"),
        },
        "intermediate": {
            "result_sha256": sha256_file(result_path),
            "status": result.get("status"),
            "verdict": result.get("verdict"),
            "candidate_sha256": sha256_file(intermediate_candidate_path) if intermediate_candidate_path.is_file() else None,
        },
        "bridge": {
            "process_exit_code": bridge_rc,
            "output_tail": bridge_output,
            "direct_candidate_sha256": sha256_file(direct_candidate_path) if direct_candidate_path.is_file() else None,
        },
        "promotion_gate": gate,
        "promotion_gate_sha256": sha256_file(gate_path),
        "credential_fence": {
            "external_provider_credential_names_forwarded": sorted(
                name for name in child_env
                if (
                    ("KEY" in name.upper() and any(marker in name.upper() for marker in PROVIDER_ENV_PATTERNS))
                    or name in HF_TOKEN_NAMES
                )
            ),
            "hf_implicit_token_disabled": child_env.get("HF_HUB_DISABLE_IMPLICIT_TOKEN") == "1",
        },
        "credits": {
            "canonical_entityos_hcu": 0,
            "hcu_full": 0,
            "jspace_model_runtime": 0,
            "training": 0,
            "whole_product_pass": False,
        },
        "evidence_boundary": (
            "Post-lease composition only. Even a positive v4 promotion verdict is a bounded candidate; "
            "canonical EntityOS/HCU/J-Space/training credit requires the enclosing admitted runtime/evidence path."
        ),
    }
    receipt["receipt_sha256"] = canonical_sha(receipt)
    (out_dir / "trigger1_v4_postlease_pipeline_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not exact_bound:
        return receipt, 4
    if result.get("status") != "PASS":
        return receipt, exact_proc.returncode if exact_proc.returncode else 3
    if bridge_rc != 0:
        return receipt, 5
    if gate.get("owner_trigger1_goal_credit_candidate") is not True:
        return receipt, 6
    return receipt, 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    try:
        receipt, rc = execute_pipeline(Path(args.output_dir))
        print(json.dumps({
            "status": "PASS_CANDIDATE" if rc == 0 else "BOUNDED_NONPASS",
            "pipeline_receipt_sha256": receipt.get("receipt_sha256"),
            "exit_code": rc,
        }, sort_keys=True))
        return rc
    except PipelineBlocked as exc:
        print(json.dumps({"status": "BLOCKED_BEFORE_INTERVENTION", "reason": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
