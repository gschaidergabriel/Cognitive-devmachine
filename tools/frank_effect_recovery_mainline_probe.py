#!/usr/bin/env python3
"""FRANK current-mainline effect recovery lineage probe.

This probe does not discover the generic exactly-once ambiguity; that negative result
already exists in the ClayCode research history. It asks a narrower integration
question: does the currently selected BASE mainline runtime carry that recovered
semantic contract forward, or can a visible external mutation occur with no durable
runtime outcome identity and then be duplicated by a retry?

Hosted GitHub/Ubuntu execution is component evidence only. It is not Andreas target-host
acceptance and it does not prove that all external adapters are non-idempotent.
"""
from __future__ import annotations

import inspect
import json
import tempfile
from pathlib import Path

from claycode_base_runtime import ClayRuntime, RUNTIME_VERSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/trigger_runs/frank/frank_20260809T1921p0700_chatgpt_secondary_runtime_lineage/MAINLINE_EFFECT_RECOVERY_RECEIPT.json"


def read_count(path: Path) -> int:
    return int(path.read_text(encoding="utf-8")) if path.exists() else 0


def write_count(path: Path, value: int) -> None:
    path.write_text(str(value), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="frank_effect_lineage_") as td:
        root = Path(td)
        sink = root / "external_sink_counter.txt"
        rt = ClayRuntime(root)

        def external_increment(_policy, crash_after_apply: bool):
            # Deliberately non-idempotent external effect surrogate.
            write_count(sink, read_count(sink) + 1)
            if crash_after_apply:
                # ClayRuntime.invoke catches Exception, not BaseException. SystemExit is
                # used here as an in-process fault-injection surrogate for losing the
                # worker after the sink mutation but before invoke can publish PASS.
                raise SystemExit("FAULT_AFTER_EXTERNAL_APPLY_BEFORE_RUNTIME_RECEIPT")
            return {"count": read_count(sink)}

        rt.register_adapter("test.external_increment", "test.external", external_increment)
        cap = rt.mint_capability("test.external")

        crash_observed = False
        try:
            rt.invoke("test.external_increment", cap, True)
        except SystemExit:
            crash_observed = True

        count_after_ambiguous_crash = read_count(sink)
        trace_after_ambiguous_crash = rt.trace_receipt()

        # Recovery surrogate: caller retries the same semantic operation. The current
        # public runtime ABI has no stable effect_operation_id / semantic fingerprint /
        # delivery-recovery class parameter on invoke, so this becomes a fresh call.
        retry_result = rt.invoke("test.external_increment", cap, False)
        count_after_retry = read_count(sink)
        final_trace = rt.trace_receipt()

        invoke_parameters = list(inspect.signature(rt.invoke).parameters)
        trace_keys = sorted({key for row in final_trace for key in row})

        negative_reproduced = (
            crash_observed
            and count_after_ambiguous_crash == 1
            and len(trace_after_ambiguous_crash) == 0
            and count_after_retry == 2
            and retry_result.get("count") == 2
        )

        receipt = {
            "schema_version": "1.0",
            "experiment_id": "EXP-FRANK-MAINLINE-EFFECT-RECOVERY-LINEAGE-001",
            "actor": "chatgpt-secondary",
            "runtime_version": RUNTIME_VERSION,
            "runtime_path": "tools/claycode_base_runtime.py",
            "evidence_class": "HOSTED_OR_LOCAL_LINUX_MAINLINE_RUNTIME_FAULT_INJECTION_NOT_ANDREAS_TARGET",
            "counts_as_target_acceptance": False,
            "counts_as_work_package_pass": False,
            "prior_negative_result": "NR-CC-LOCAL-PREPARED-NOT-EXACTLY-ONCE-20260809",
            "question": "Does the selected mainline runtime carry stable external-effect recovery identity across an ambiguous post-apply/pre-receipt crash?",
            "fault_injection": "SystemExit after sink mutation and before ClayRuntime.invoke PASS receipt",
            "observations": {
                "crash_observed": crash_observed,
                "sink_count_after_ambiguous_crash": count_after_ambiguous_crash,
                "trace_rows_after_ambiguous_crash": len(trace_after_ambiguous_crash),
                "sink_count_after_retry": count_after_retry,
                "retry_result": retry_result,
                "invoke_parameters": invoke_parameters,
                "trace_keys": trace_keys,
            },
            "negative_result_reproduced_on_current_mainline": negative_reproduced,
            "interpretation": (
                "The current mainline authority boundary prevents capability forgery but does not by itself expose the stable effect operation identity / semantic fingerprint / recovery class needed to reconcile an external effect whose outcome becomes locally ambiguous after a crash. A naive retry of the demonstrated non-idempotent sink duplicates the effect."
                if negative_reproduced else
                "The expected lineage counterexample was not reproduced; inspect runtime changes before drawing a conclusion."
            ),
            "required_followup": [
                "Integrate the already-researched effect_operation_id + semantic fingerprint + explicit delivery/recovery class into the selected production-bound runtime/effect bridge without granting model authority.",
                "Represent unreconcilable post-crash outcomes as UNCERTAIN rather than silently retrying or claiming DONE.",
                "Add idempotent, queryable/reconcilable, same-transaction-domain, and deliberately non-idempotent adapter arms.",
                "Differential-test the same semantic contract through H1 ordinary code and H2 ClayCode, then rerun on Andreas Ubuntu before release credit."
            ],
            "status": "NEGATIVE_RESULT_REPRODUCED" if negative_reproduced else "INCONCLUSIVE",
        }

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": receipt["status"],
            "runtime": RUNTIME_VERSION,
            "sink_after_crash": count_after_ambiguous_crash,
            "trace_after_crash": len(trace_after_ambiguous_crash),
            "sink_after_retry": count_after_retry,
        }, sort_keys=True))
        return 0 if negative_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
