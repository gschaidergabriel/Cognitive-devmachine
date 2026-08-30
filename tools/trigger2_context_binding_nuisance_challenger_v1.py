#!/usr/bin/env python3
"""Dataset-level nuisance-only and semantic-ablation challenger for Trigger-2 binder rows.

This is a deterministic adversarial dataset audit. It does not run or train a model and
cannot mint J-Space/HCU/EntityOS/training credit. By default it evaluates the retained
Trigger-2 context-binding generator v2 blueprint.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger2_context_binding_generator_v2 as gen

SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_NUISANCE_CHALLENGER/v1"
CHANCE = 1.0 / 3.0
EVIDENCE_BLOCK = re.compile(r"(?s)(\nEVIDENCE\n).*?(\nPROPOSITION\n)")


def ablate_semantic_evidence(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    matches = list(EVIDENCE_BLOCK.finditer(prompt))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one EVIDENCE->PROPOSITION span, found {len(matches)}")
    return EVIDENCE_BLOCK.sub(r"\1<EVIDENCE_ABLATED>\2", prompt, count=1)


def _majority_lookup_accuracy(signatures: Sequence[str], labels: Sequence[str]) -> tuple[float, dict[str, Counter[str]]]:
    if len(signatures) != len(labels) or not signatures:
        raise ValueError("nonempty aligned signatures/labels required")
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for signature, label in zip(signatures, labels):
        groups[signature][label] += 1
    correct = sum(max(counts.values()) for counts in groups.values())
    return correct / len(labels), groups


def _base_generator_pass(rows: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    audit = gen.validate_rows(rows)
    ok = audit.get("pass") is True or audit.get("status") == "PASS"
    return ok, audit


def challenge_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rr = list(rows)
    failures: list[str] = []
    if not rr:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["EMPTY_ROWS"],
            "rows_total": 0,
            "accepted_dataset_tokens": 0,
            "training_credit_minted": False,
            "jspace_credit_minted": False,
            "runtime_credit_minted": False,
        }

    base_ok, base_audit = _base_generator_pass(rr)
    if not base_ok:
        failures.append("BASE_GENERATOR_VALIDATION_FAILED")

    ablated_prompts: list[str] = []
    full_prompts: list[str] = []
    semantic_classes: list[str] = []
    targets: list[str] = []
    hidden_projection_violations: list[int] = []
    state_label_leaks: list[int] = []

    state_names = tuple(getattr(gen, "STATES", ("SUPPORTS", "CONTRADICTS", "UNKNOWN")))
    classes = tuple(getattr(gen, "CLASSES", ("ALLOW", "DENY", "ABSTAIN")))
    slots = tuple(getattr(gen, "SLOTS", ("<ABI_SLOT_0>", "<ABI_SLOT_1>", "<ABI_SLOT_2>")))

    for i, row in enumerate(rr):
        try:
            prompt = row["prompt"]
            semantic = row["audit_target_semantic_class"]
            target = row["target"]
            if semantic not in classes:
                failures.append(f"SEMANTIC_CLASS_INVALID:{i}")
            if target not in slots:
                failures.append(f"TARGET_SLOT_INVALID:{i}")
            if row.get("model_visible_fields") != ["prompt"] or row.get("supervision_field") != "target":
                hidden_projection_violations.append(i)
            if row.get("audit_metadata_must_not_enter_model_context") is not True:
                hidden_projection_violations.append(i)
            if row.get("training_eligible") is not False:
                hidden_projection_violations.append(i)
            ablated = ablate_semantic_evidence(prompt)
            if any(re.search(rf"\b{re.escape(state)}\b", ablated, flags=re.I) for state in state_names):
                state_label_leaks.append(i)

            full_prompts.append(prompt)
            ablated_prompts.append(ablated)
            semantic_classes.append(semantic)
            targets.append(target)
        except Exception as exc:
            failures.append(f"ROW_CHALLENGE_EXCEPTION:{i}:{type(exc).__name__}:{exc}")

    if hidden_projection_violations:
        failures.append("MODEL_VISIBLE_PROJECTION_VIOLATION:" + ",".join(map(str, sorted(set(hidden_projection_violations))[:20])))
    if state_label_leaks:
        failures.append("SEMANTIC_STATE_LABEL_LEAK_IN_MODEL_PROMPT:" + ",".join(map(str, state_label_leaks[:20])))

    metrics: dict[str, Any] = {}
    if len(ablated_prompts) == len(rr) and len(semantic_classes) == len(rr):
        full_class_acc, _ = _majority_lookup_accuracy(full_prompts, semantic_classes)
        ablated_class_acc, ablated_class_groups = _majority_lookup_accuracy(ablated_prompts, semantic_classes)
        full_target_acc, _ = _majority_lookup_accuracy(full_prompts, targets)
        ablated_target_acc, ablated_target_groups = _majority_lookup_accuracy(ablated_prompts, targets)

        class_support_sizes = [len(c) for c in ablated_class_groups.values()]
        target_support_sizes = [len(c) for c in ablated_target_groups.values()]
        class_group_balanced = all(set(c) == set(classes) and len(set(c.values())) == 1 for c in ablated_class_groups.values())
        target_group_balanced = all(set(c) == set(slots) and len(set(c.values())) == 1 for c in ablated_target_groups.values())

        metrics = {
            "chance": CHANCE,
            "full_prompt_exact_lookup_semantic_class_accuracy": full_class_acc,
            "ablated_prompt_exact_lookup_semantic_class_accuracy": ablated_class_acc,
            "full_prompt_exact_lookup_target_slot_accuracy": full_target_acc,
            "ablated_prompt_exact_lookup_target_slot_accuracy": ablated_target_acc,
            "ablated_signature_groups": len(ablated_class_groups),
            "ablated_class_support_min": min(class_support_sizes) if class_support_sizes else 0,
            "ablated_class_support_max": max(class_support_sizes) if class_support_sizes else 0,
            "ablated_target_support_min": min(target_support_sizes) if target_support_sizes else 0,
            "ablated_target_support_max": max(target_support_sizes) if target_support_sizes else 0,
            "ablated_class_groups_exactly_balanced": class_group_balanced,
            "ablated_target_groups_exactly_balanced": target_group_balanced,
            "semantic_ablation_drop_class_accuracy": full_class_acc - ablated_class_acc,
            "semantic_ablation_drop_target_accuracy": full_target_acc - ablated_target_acc,
        }

        if not math.isclose(ablated_class_acc, CHANCE, abs_tol=1e-12):
            failures.append(f"ABLATED_CLASS_LOOKUP_NOT_CHANCE:{ablated_class_acc:.17g}")
        if not math.isclose(ablated_target_acc, CHANCE, abs_tol=1e-12):
            failures.append(f"ABLATED_TARGET_LOOKUP_NOT_CHANCE:{ablated_target_acc:.17g}")
        if not class_group_balanced:
            failures.append("ABLATED_NUISANCE_SIGNATURE_NOT_CLASS_BALANCED")
        if not target_group_balanced:
            failures.append("ABLATED_NUISANCE_SIGNATURE_NOT_TARGET_BALANCED")
        if full_class_acc < 1.0 - 1e-12:
            failures.append(f"FULL_PROMPT_CLASS_SIGNATURE_AMBIGUOUS:{full_class_acc:.17g}")
        if full_target_acc < 1.0 - 1e-12:
            failures.append(f"FULL_PROMPT_TARGET_SIGNATURE_AMBIGUOUS:{full_target_acc:.17g}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "rows_total": len(rr),
        "generator_schema": getattr(gen, "GENERATOR_SCHEMA", getattr(gen, "SCHEMA", "UNKNOWN")),
        "base_generator_pass": base_ok,
        "base_generator_audit": base_audit,
        "metrics": metrics,
        "interpretation": {
            "what_pass_means": "For these realized blueprint rows, any deterministic exact lookup using only the model-visible prompt after semantic EVIDENCE ablation is forced to chance for both semantic class and target slot; this is a dataset-level shortcut discriminator, not model evidence.",
            "what_pass_does_not_mean": "It does not prove a trained model will use semantics, does not cover unseen generalized nuisance functions, and must be rerun on final ABI-rendered/serialized rows before training admission."
        },
        "accepted_dataset_tokens": 0,
        "training_credit_minted": False,
        "jspace_credit_minted": False,
        "runtime_credit_minted": False,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"line {line_no}: object required")
        rows.append(obj)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=Path, help="Optional materialized rows. Default: retained generator v2 blueprint.")
    ap.add_argument("--output", type=Path)
    ns = ap.parse_args()
    rows = _load_jsonl(ns.jsonl) if ns.jsonl else gen.generate_rows()
    result = challenge_rows(rows)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if ns.output:
        ns.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
