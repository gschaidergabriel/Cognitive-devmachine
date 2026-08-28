#!/usr/bin/env python3
"""Fail-closed authority-origin gate for Trigger-2 executable-transition pilots.

This gate checks a property intentionally stronger than structural ABI validity:
protected deterministic envelope values that appear in a supervised result target
must already be bound as deterministic/evaluator inputs. A model must not be taught
to invent admission IDs, causal IDs, generations, work IDs, scheduler lease IDs, or
runtime executor identities merely because the target packet structurally requires them.

It imports the current executable-transition pilot and is expected to BLOCK until the
pilot exposes an equivalent bound deterministic-input envelope. This is eval/source
design only and mints no training/runtime/canonical/effect credit.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PILOT = ROOT / "tools/trigger2_executable_transition_pilot_v1.py"
SCHEMA = "TRIGGER2_EXECUTABLE_TRANSITION_AUTHORITY_ORIGIN_GATE/v1"

# These values originate from deterministic admission/routing/runtime machinery or
# from a deterministic result-envelope assembler. They are not free-form cognition.
PROTECTED_TOP_LEVEL = (
    "causal_event_id",
    "admission_id",
    "generation",
    "work_id",
    "process_id",
    "result_id",
)
PROTECTED_EXECUTOR_FIELDS = (
    "grid_instance_id",
    "requested_N",
    "available_N",
    "executor_id",
    "lease_id",
    "process_id",
    "runtime_identity",
)


def load_pilot(path: Path):
    spec = importlib.util.spec_from_file_location("trigger2_transition_pilot", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("PILOT_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _eq(a: Any, b: Any) -> bool:
    return a == b


def adjudicate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    checked = 0
    for row in rows:
        rid = str(row.get("case_id", "UNKNOWN"))
        target = row.get("target")
        if not isinstance(target, dict):
            failures.append(f"TARGET_DICT_REQUIRED:{rid}")
            continue

        # Successor implementations may call this field bound_deterministic_inputs,
        # deterministic_envelope_input, or work_packet. The important property is
        # origin/binding, not a preferred spelling.
        candidates = [
            ("bound_deterministic_inputs", row.get("bound_deterministic_inputs")),
            ("deterministic_envelope_input", row.get("deterministic_envelope_input")),
            ("work_packet", row.get("work_packet")),
        ]
        input_name, bound = next(((n, v) for n, v in candidates if isinstance(v, dict)), (None, None))
        if bound is None:
            failures.append(f"PROTECTED_ENVELOPE_INPUT_MISSING:{rid}")
            continue

        visible = row.get("model_visible_fields")
        if not isinstance(visible, list) or input_name not in visible:
            failures.append(f"PROTECTED_ENVELOPE_NOT_MODEL_BOUND:{rid}:{input_name}")

        checked += 1
        for field in PROTECTED_TOP_LEVEL:
            if field not in bound:
                failures.append(f"PROTECTED_INPUT_FIELD_MISSING:{rid}:{field}")
            elif not _eq(target.get(field), bound.get(field)):
                failures.append(f"PROTECTED_FIELD_DRIFT:{rid}:{field}")

        target_executor = target.get("executor_binding")
        bound_executor = bound.get("executor_binding")
        if not isinstance(target_executor, dict):
            failures.append(f"TARGET_EXECUTOR_BINDING_MISSING:{rid}")
        if not isinstance(bound_executor, dict):
            failures.append(f"BOUND_EXECUTOR_BINDING_MISSING:{rid}")
        if isinstance(target_executor, dict) and isinstance(bound_executor, dict):
            for field in PROTECTED_EXECUTOR_FIELDS:
                if field not in bound_executor:
                    failures.append(f"PROTECTED_EXECUTOR_INPUT_MISSING:{rid}:{field}")
                elif not _eq(target_executor.get(field), bound_executor.get(field)):
                    failures.append(f"PROTECTED_EXECUTOR_FIELD_DRIFT:{rid}:{field}")

        # A source-design/runtime-unknown target must not create a positive runtime
        # identity through the supervised packet.
        receipt = target.get("runtime_receipt")
        if isinstance(receipt, dict) and receipt.get("model_runtime_observed") is True:
            failures.append(f"UNOBSERVED_RUNTIME_PROMOTED:{rid}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "rows_seen": len(rows),
        "rows_with_bound_protected_envelope": checked,
        "failures": sorted(set(failures)),
        "policy": {
            "deterministic_authority_values_must_be_inputs_not_model_inventions": True,
            "protected_top_level": list(PROTECTED_TOP_LEVEL),
            "protected_executor_fields": list(PROTECTED_EXECUTOR_FIELDS),
            "training_eligible": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "runtime_credit_minted": 0,
            "canonical_truth_minted": False,
            "effect_authority_minted": False,
        },
        "expected_current_v1_status": "BLOCKED_UNTIL_PROTECTED_ENVELOPE_IS_BOUND_AS_INPUT",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=Path, default=DEFAULT_PILOT)
    args = ap.parse_args()
    module = load_pilot(args.pilot)
    result = adjudicate(module.rows())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
