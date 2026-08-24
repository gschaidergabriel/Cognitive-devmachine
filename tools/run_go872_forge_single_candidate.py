#!/usr/bin/env python3
"""Produce one deterministic exact-source Forge evaluation through the real safe validator.

This is a runtime witness helper, not a general Forge entrypoint. It performs no
provider discovery or model/network calls. The only candidate changes a dedicated
noncanonical fixture inside a disposable Forge clone so baseline fails and patched
execution passes under the same current safe-Forge admission machinery used by live
candidate validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_free_evidence_forge_safe_871 as safe_forge  # noqa: E402

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
FIXTURE = "tests/fixtures/forge_runtime_witness_872.txt"
CHECK = "tests/forge_runtime_witness_check_872.py"


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def build_proposal() -> dict[str, object]:
    patch = (
        "diff --git a/tests/fixtures/forge_runtime_witness_872.txt "
        "b/tests/fixtures/forge_runtime_witness_872.txt\n"
        "--- a/tests/fixtures/forge_runtime_witness_872.txt\n"
        "+++ b/tests/fixtures/forge_runtime_witness_872.txt\n"
        "@@ -1 +1 @@\n"
        "-BASELINE\n"
        "+PATCHED\n"
    )
    return {
        "delta_id": "go872-real-safe-forge-producer-witness",
        "ready_for_forge": True,
        "hypothesis": "The real safe Forge validator can produce an evidence-qualified ACCEPT whose measured execution is then admitted exactly once by Distillery.",
        "falsifier": "If baseline does not fail, patched does not pass twice, execution admission is absent, or Distillery cannot preserve idempotence, the gate fails.",
        "target_files": [FIXTURE],
        "patch_unified_diff": patch,
        "test_commands": [f"python3 {CHECK}"],
        "negative_test_commands": [
            "python3 -m unittest -q runtime_checks.test_forge_distillery_requires_execution_admission_871"
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_sha = args.source_sha.strip().lower()
    if not COMMIT_RE.fullmatch(source_sha):
        raise SystemExit("SOURCE_SHA_INVALID")

    proposal = build_proposal()
    proposal_json = canonical_json(proposal)
    worker_payload = canonical_json({
        "schema": "CLAY_FORGE_RUNTIME_WITNESS_WORKER_PAYLOAD/v1",
        "source_sha": source_sha,
        "proposal": proposal,
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME_WITNESS",
    })
    worker_sha = hashlib.sha256(worker_payload.encode("utf-8")).hexdigest()
    row = {
        "delta_id": proposal["delta_id"],
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME_WITNESS",
        "worker_sha": worker_sha,
        "repo_head": source_sha,
        "proposal_json": proposal_json,
    }

    safe_forge.base.FORGE_ROOT.mkdir(parents=True, exist_ok=True)
    evaluation = safe_forge.validate_candidate(None, row)
    evaluation["witness_worker_payload_sha256"] = worker_sha
    evaluation["witness_producer"] = "run_free_evidence_forge_safe_871.validate_candidate"
    evaluation["witness_external_provider_calls"] = 0
    evaluation["witness_paid_fallback_attempt_count"] = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(evaluation) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": evaluation.get("status"),
        "worker_sha": worker_sha,
        "source_repo_head": evaluation.get("source_repo_head"),
        "evaluation_repo_head": evaluation.get("evaluation_repo_head"),
        "execution_admitted": bool((evaluation.get("execution_admission") or {}).get("all_commands_admitted")),
    }, sort_keys=True))
    return 0 if str(evaluation.get("status", "")).lower() == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
