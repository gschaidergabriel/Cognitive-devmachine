#!/usr/bin/env python3
"""Adversarial validation for deterministic ClayCode BASE cancellation/error adapter."""
from __future__ import annotations

import hashlib
import json
import random
import tempfile
from pathlib import Path

from claycode_base_runtime import ClayRuntime, CapabilityFault
from claycode_base_concurrency_extensions import install, CONCURRENCY_EXT_VERSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/autonomous/BASE_CONCURRENCY_CANCELLATION_RECEIPT.json"


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    checks = {}
    with tempfile.TemporaryDirectory(prefix="claycode-concurrency-") as td:
        rt = install(ClayRuntime(td))
        cap = rt.mint_capability("async.cancellable", {
            "operations": ["square", "inverse100"],
            "max_items": 10000,
            "max_workers": 16,
            "max_calls": 20,
            "max_units": 100000,
        })

        rng = random.Random(202608091236)
        values = [rng.randint(-1000, 1000) for _ in range(257)]
        full = rt.invoke("async.cancellable_map", cap, "square", values, None, 8)
        expected = [x * x for x in values]
        observed = [row.get("value") for row in full["rows"]]
        checks["concurrent_positive"] = observed == expected and full["cancelled"] == 0 and full["errors"] == 0
        checks["publication_order_deterministic"] = [row["index"] for row in full["rows"]] == list(range(len(values)))

        cut = 113
        cancelled = rt.invoke("async.cancellable_map", cap, "square", values, cut, 8)
        checks["cancel_prefix_exact"] = (
            cancelled["submitted"] == cut
            and cancelled["cancelled"] == len(values) - cut
            and [row["status"] for row in cancelled["rows"][:cut]] == ["OK"] * cut
            and [row["status"] for row in cancelled["rows"][cut:]] == ["CANCELLED"] * (len(values) - cut)
            and cancelled["post_cancel_dispatch"] == 0
        )

        errors = rt.invoke("async.cancellable_map", cap, "inverse100", [10, 5, 0, -4], None, 4)
        checks["structured_error_path"] = (
            [row["status"] for row in errors["rows"]] == ["OK", "OK", "ERROR", "OK"]
            and errors["errors"] == 1
            and errors["rows"][2].get("error_type") == "ZeroDivisionError"
        )

        # A policy-scoped operation cannot be widened by request text.
        try:
            rt.invoke("async.cancellable_map", cap, "identity", [1], None, 1)
            checks["caller_cannot_widen_operation_scope"] = False
        except CapabilityFault:
            checks["caller_cannot_widen_operation_scope"] = True

        # Descriptive capability metadata is not an authorizing handle.
        desc = rt.capability_descriptor(cap)
        try:
            rt.invoke("async.cancellable_map", desc, "square", [2], None, 1)
            checks["descriptor_not_authority"] = False
        except CapabilityFault:
            checks["descriptor_not_authority"] = True

        rt.revoke(cap)
        try:
            rt.invoke("async.cancellable_map", cap, "square", [2], None, 1)
            checks["revocation_rejected"] = False
        except CapabilityFault:
            checks["revocation_rejected"] = True

        trace = rt.trace_receipt()
        checks["trace_commits_faults_and_passes"] = any(x["status"] == "PASS" for x in trace) and any(x["status"] == "FAULT" for x in trace)
        checks["trace_no_handle_secret"] = "nonce" not in json.dumps(trace, sort_keys=True)

    report = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE deterministic async cancellation/error semantics",
        "concurrency_extension_version": CONCURRENCY_EXT_VERSION,
        "checks": checks,
        "pass": all(checks.values()),
        "trace_sha256": sha(trace),
        "supports": ["CC-WP-09-CONCURRENCY-MEMORY", "APP-04-CONCURRENT-SERVICE", "CC-WP-11-FUZZ-CONFORMANCE"],
        "counts_as_work_package_pass": False,
        "counts_as_application_acceptance_pass": False,
        "counts_as_target_acceptance": False,
        "authority_invariant": "operation selection and cancellation control never mint or widen authority",
        "scope_guard": "Hosted/local adapter evidence. APP-04 acceptance still requires the production ClayCode chain on the Andreas Ubuntu target and target receipt fields.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "checks": checks}, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
