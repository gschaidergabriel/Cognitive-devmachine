#!/usr/bin/env python3
"""One-command fail-closed ClayCode BASE diagnostic for Andreas' Ubuntu target.

The runner verifies the local target registration, executes the strongest current
production/proxy gates in dependency order and writes a target-local diagnostic receipt.
It NEVER writes the authoritative ANDREAS_UBUNTU_BASE_ACCEPTANCE.json because several
current gates are explicitly proxy/incomplete. The final acceptance generator must
consume only contract-complete target evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from claycode_target_host_identity import verify, DEFAULT_REGISTRATION, TARGET_HOST

OUT = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_BASE_DIAGNOSTIC.json"


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def run(name: str, argv: list[str], timeout: int = 600) -> dict:
    try:
        cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "name": name,
            "argv": argv,
            "returncode": cp.returncode,
            "pass": cp.returncode == 0,
            "stdout_tail": cp.stdout[-40000:],
            "stderr_tail": cp.stderr[-40000:],
        }
    except Exception as exc:
        return {"name": name, "argv": argv, "returncode": None, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ok_host, host = verify(DEFAULT_REGISTRATION)
    stages: list[dict] = []
    if ok_host:
        py = sys.executable
        stages.extend([
            run("WP02_STRICT_V7", [py, "tools/claycode_strict_lalr_probe.py", "--grammar", "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark", "--output", "research_entity/claycode/target/WP02_STRICT_V7.json"]),
            run("WP03_TYPED_IR", [py, "tools/claycode_wp03_ci_runner.py"]),
            run("WP04_06_EFFECT_PIPELINE", [py, "tools/claycode_base_effect_pipeline.py", "--self-test", "--output", "research_entity/claycode/target/WP04_06_EFFECT_PIPELINE.json"]),
            run("WP04_08_REAL_EFFECT_RUNTIME", [py, "tools/claycode_effect_runtime_bridge_validation.py"]),
            run("WP07_09_RUNTIME", [py, "tools/claycode_base_runtime_validation.py"]),
            run("WP09_CANCELLATION", [py, "tools/claycode_base_concurrency_validation.py"]),
            run("WP10_APPLICATION_PROXY_V2", [py, "tools/claycode_base_application_proxy_suite_v2.py"]),
            run("WP12_HELDOUT", [py, "tools/claycode_wp12_heldout.py", "--positive", "128", "--negative", "96", "--output", "research_entity/claycode/target/WP12_HELDOUT_TARGET_RUN.json"], timeout=1200),
            run("WP13_PACKET_SCORE_HANDOFF", [py, "tools/claycode_frank_packet_score_handoff.py"]),
            run("WP14_RELEASE_AUDIT_PREVIEW", [py, "tools/claycode_base_release_audit.py"]),
        ])
    else:
        stages.append({"name": "TARGET_HOST_IDENTITY", "pass": False, "errors": host.get("errors", [])})

    by_name = {x["name"]: x for x in stages}
    # These are diagnostic closure indicators, deliberately stricter than a green process.
    wp = {
        "CC-WP-02-PARSER-CANON": {"pass": bool(by_name.get("WP02_STRICT_V7", {}).get("pass")), "acceptance_complete": False, "reason": "strict parser evidence exists but official canonical parser/canonicalizer receipt still requires promotion review"},
        "CC-WP-03-IR-TYPES": {"pass": bool(by_name.get("WP03_TYPED_IR", {}).get("pass")), "acceptance_complete": False, "reason": "target execution of current typed IR slice; collections/universal core remain audit items"},
        "CC-WP-04-TYPE-EFFECT": {"pass": bool(by_name.get("WP04_06_EFFECT_PIPELINE", {}).get("pass") and by_name.get("WP04_08_REAL_EFFECT_RUNTIME", {}).get("pass")), "acceptance_complete": False},
        "CC-WP-05-EVALUATOR": {"pass": bool(by_name.get("WP04_06_EFFECT_PIPELINE", {}).get("pass")), "acceptance_complete": False},
        "CC-WP-06-COMPILER-LOWERING": {"pass": bool(by_name.get("WP04_06_EFFECT_PIPELINE", {}).get("pass")), "acceptance_complete": False, "reason": "effectful target is Python lowering while pure core has native C; one production backend chain still required"},
        "CC-WP-07-RUNTIME-ABI-FFI": {"pass": bool(by_name.get("WP07_09_RUNTIME", {}).get("pass") and by_name.get("WP04_08_REAL_EFFECT_RUNTIME", {}).get("pass")), "acceptance_complete": False},
        "CC-WP-08-STDLIB-SDK": {"pass": bool(by_name.get("WP07_09_RUNTIME", {}).get("pass") and by_name.get("WP10_APPLICATION_PROXY_V2", {}).get("pass")), "acceptance_complete": False},
        "CC-WP-09-CONCURRENCY-MEMORY": {"pass": bool(by_name.get("WP07_09_RUNTIME", {}).get("pass") and by_name.get("WP09_CANCELLATION", {}).get("pass")), "acceptance_complete": False},
        "CC-WP-10-GENERAL-APP-SUITE": {"pass": bool(by_name.get("WP10_APPLICATION_PROXY_V2", {}).get("pass")), "acceptance_complete": False, "reason": "V2 suite is explicitly proxy and does not satisfy contract-complete target app rows/full FRANK handoff"},
        "CC-WP-11-FUZZ-CONFORMANCE": {"pass": False, "acceptance_complete": False, "reason": "target diagnostic does not yet aggregate all current fuzz/mutation/conformance lanes into one target receipt"},
        "CC-WP-12-CORPUS-HELDOUT": {"pass": bool(by_name.get("WP12_HELDOUT", {}).get("pass")), "acceptance_complete": False, "reason": "heldout target execution alone is not the package promotion receipt"},
        "CC-WP-13-HARNESS-HANDOFF": {"pass": bool(by_name.get("WP13_PACKET_SCORE_HANDOFF", {}).get("pass")), "acceptance_complete": False, "reason": "packet_score is a real frozen FRANK slice but not full ActiveAssembly/H2/H3 handoff"},
        "CC-WP-14-BASE-AUDIT": {"pass": False, "acceptance_complete": False, "reason": "release audit can pass only after WP01-13 and ten application rows are contract-complete"},
    }

    current_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    receipt = {
        "schema_version": "1.0",
        "target_host": TARGET_HOST,
        "target_host_verified": ok_host,
        "repository_commit": current_commit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "host_fingerprint": host.get("host_fingerprint", {}),
        "host_identity_evidence": {k: v for k, v in host.items() if k != "host_fingerprint"},
        "stages": stages,
        "work_package_diagnostics": wp,
        "all_executed_stages_pass": ok_host and all(x.get("pass") for x in stages),
        "acceptance_contract_complete": False,
        "overall_pass": False,
        "counts_as_target_acceptance": False,
        "acceptance_blockers": [
            "contract-complete APP-01..APP-10 target rows",
            "one production effectful/native compiler-runtime chain",
            "aggregated target fuzz/conformance receipt",
            "full frozen FRANK ActiveAssembly/H2/H3 handoff",
            "official package promotion receipts",
        ],
        "rule": "A target diagnostic is not an acceptance receipt; do not copy/rename this file to ANDREAS_UBUNTU_BASE_ACCEPTANCE.json.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"target_host_verified": ok_host, "all_stages_pass": receipt["all_executed_stages_pass"], "overall_pass": False, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if ok_host and receipt["all_executed_stages_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
