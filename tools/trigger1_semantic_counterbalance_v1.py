#!/usr/bin/env python3
"""Counterbalanced semantic holdout wrapper for the local Qwen3-0.6B Trigger-1 mid-layer experiment.

This module deliberately changes only the *scientific target family* around the current
executor. It keeps the existing exact-source/runtime/lease surfaces separate. No model is
loaded at import time and no provider credential is accessed.

The current mid-layer executor derives an internal direction keyed by A/B/C-labelled basis
prompts and evaluates a fixed A-vs-(B,C) output-token contrast. That is useful mechanism
measurement, but a fixed output-label mapping can self-confirm lexical/readout preference.

This wrapper replaces the basis with label-free numeric-direction examples and evaluates
one semantic target (INCREASE vs DECREASE/SAME) over all six A/B/C label permutations.
Thus each semantic class is mapped to each physical output token exactly twice. The output
metric still uses token logits, so the receipt states that fact explicitly; what changes is
that physical label identity is counterbalanced rather than aligned with the target.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys
import threading
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_EXECUTOR = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal_execute.py"
SCHEMA = "CLAY_TRIGGER1_SEMANTIC_COUNTERBALANCE_WRAPPER/v1"
SEMANTICS = ("INCREASE", "DECREASE", "SAME")
TOKENS = ("A", "B", "C")
MAP_RE = re.compile(r"\[CBMAP:INCREASE=([ABC]);DECREASE=([ABC]);SAME=([ABC])\]")

# Internal labels A/B/C are metadata only here; the prompts themselves contain no output
# option labels and no target word such as "increase"/"decrease".
BASIS_PROMPTS = (
    (2101, "A", "/no_think\nA quantity starts at 2 and ends at 5. Encode the direction of change internally. Continue:"),
    (2102, "B", "/no_think\nA quantity starts at 5 and ends at 2. Encode the direction of change internally. Continue:"),
    (2103, "C", "/no_think\nA quantity starts at 4 and ends at 4. Encode the direction of change internally. Continue:"),
    (2111, "A", "/no_think\nA measured level moves from 11 to 17. Represent the relation between start and end. Continue:"),
    (2112, "B", "/no_think\nA measured level moves from 17 to 11. Represent the relation between start and end. Continue:"),
    (2113, "C", "/no_think\nA measured level moves from 13 to 13. Represent the relation between start and end. Continue:"),
)

MAPPINGS = tuple(
    {semantic: token for semantic, token in zip(SEMANTICS, perm)}
    for perm in itertools.permutations(TOKENS)
)

CALIBRATION_CASES = (
    (3701, 3, 8, "Gain C1"),
    (3702, 14, 19, "Gain C2"),
    (3703, 21, 29, "Gain C3"),
    (3704, 32, 41, "Gain C4"),
    (3705, 6, 12, "Gain C5"),
    (3706, 50, 73, "Gain C6"),
)
HOLDOUT_CASES = (
    (4711, 7, 15, "Holdout H1"),
    (4721, 18, 27, "Holdout H2"),
    (4731, 31, 46, "Holdout H3"),
    (4741, 44, 63, "Holdout H4"),
    (4751, 9, 22, "Holdout H5"),
    (4761, 81, 95, "Holdout H6"),
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def mapping_marker(mapping: dict[str, str]) -> str:
    return (
        f"[CBMAP:INCREASE={mapping['INCREASE']};"
        f"DECREASE={mapping['DECREASE']};SAME={mapping['SAME']}]"
    )


def parse_mapping(prompt: str) -> dict[str, str] | None:
    match = MAP_RE.search(prompt)
    if not match:
        return None
    mapping = dict(zip(SEMANTICS, match.groups()))
    if set(mapping.values()) != set(TOKENS):
        raise ValueError("COUNTERBALANCE_MAPPING_NOT_BIJECTIVE")
    return mapping


def token_to_semantic(mapping: dict[str, str]) -> dict[str, str]:
    return {token: semantic for semantic, token in mapping.items()}


def render_case(seed: int, start: int, end: int, name: str, mapping: dict[str, str]) -> tuple[int, str]:
    inverse = token_to_semantic(mapping)
    option_text = {
        "INCREASE": "the ending value is larger than the starting value",
        "DECREASE": "the ending value is smaller than the starting value",
        "SAME": "the ending value is unchanged from the starting value",
    }
    lines = [
        "/no_think",
        f"{name}. A measured value moves from {start} to {end}.",
        "Choose the relation that is true and output only its letter.",
    ]
    for token in TOKENS:
        lines.append(f"{token}: {option_text[inverse[token]]}")
    lines.append(mapping_marker(mapping))
    return seed, "\n".join(lines)


def build_family(cases: tuple[tuple[int, int, int, str], ...]) -> tuple[tuple[int, str], ...]:
    if len(cases) != len(MAPPINGS):
        raise ValueError("COUNTERBALANCE_REQUIRES_ALL_SIX_PERMUTATIONS")
    return tuple(render_case(*case, mapping) for case, mapping in zip(cases, MAPPINGS))


def balance_receipt() -> dict[str, Any]:
    counts = {
        semantic: {token: sum(1 for mapping in MAPPINGS if mapping[semantic] == token) for token in TOKENS}
        for semantic in SEMANTICS
    }
    complete = len({tuple(mapping[s] for s in SEMANTICS) for mapping in MAPPINGS}) == 6
    balanced = complete and all(counts[s][t] == 2 for s in SEMANTICS for t in TOKENS)
    return {
        "schema": SCHEMA,
        "semantic_target": "INCREASE_VS_DECREASE_OR_SAME",
        "metric_uses_output_tokens": True,
        "label_mapping_counterbalanced": balanced,
        "mapping_count": len(MAPPINGS),
        "mapping_family": MAPPINGS,
        "per_semantic_physical_token_counts": counts,
        "basis_prompt_family_sha256": canonical_sha([p for _, _, p in BASIS_PROMPTS]),
        "mapping_family_sha256": canonical_sha(MAPPINGS),
        "calibration_family_sha256": canonical_sha([p for _, p in build_family(CALIBRATION_CASES)]),
        "holdout_family_sha256": canonical_sha([p for _, p in build_family(HOLDOUT_CASES)]),
        "basis_contains_output_option_labels": False,
        "basis_constructed_without_output_head": True,
        "scientific_claim_boundary": (
            "A positive result can support a counterbalanced semantic-direction intervention candidate; "
            "it does not by itself establish a unique internal representation, canonical truth, whole-HCU, "
            "training, or whole-product credit."
        ),
    }


def load_base_module():
    spec = importlib.util.spec_from_file_location("clay_trigger1_midlayer_base", BASE_EXECUTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_EXECUTOR_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_semantic_score_patch(base: Any) -> None:
    original_infer = base.RuntimeState.infer
    mapping_lock = threading.Lock()

    def semantic_infer(self: Any, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        mapping = parse_mapping(prompt)
        if mapping is None:
            return original_infer(self, payload)
        with mapping_lock:
            physical = dict(self.token_ids)
            self.token_ids = {
                "A": physical[mapping["INCREASE"]],
                "B": physical[mapping["DECREASE"]],
                "C": physical[mapping["SAME"]],
            }
            try:
                result = original_infer(self, payload)
            finally:
                self.token_ids = physical
        result["semantic_target"] = "INCREASE"
        result["semantic_to_physical_token"] = mapping
        result["metric_uses_output_tokens"] = True
        result["label_mapping_counterbalanced_family"] = True
        return result

    base.RuntimeState.infer = semantic_infer


def patch_base(base: Any) -> dict[str, Any]:
    receipt = balance_receipt()
    if receipt["label_mapping_counterbalanced"] is not True:
        raise RuntimeError("COUNTERBALANCE_BALANCE_INVARIANT_FAILED")
    base.BASIS_PROMPTS = BASIS_PROMPTS
    base.GAIN_CALIBRATION = build_family(CALIBRATION_CASES)
    base.HOLDOUT = build_family(HOLDOUT_CASES)
    install_semantic_score_patch(base)
    return receipt


def _output_dir_from_argv(argv: list[str]) -> Path:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--output-dir", required=True)
    ns, _ = ap.parse_known_args(argv[1:])
    return Path(ns.output_dir)


def postprocess_outputs(base: Any, out: Path, receipt: dict[str, Any]) -> None:
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        old_hash = result.pop("result_sha256", None)
        result["pre_counterbalance_base_result_sha256"] = old_hash
        result["semantic_counterbalance"] = receipt
        result["result_sha256"] = base.canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if candidate_path.is_file():
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate.setdefault("holdout", {}).update({
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
            "semantic_target": "INCREASE_VS_DECREASE_OR_SAME",
            "mapping_family_sha256": receipt["mapping_family_sha256"],
        })
        candidate.setdefault("calibration", {}).update({
            "label_mapping_counterbalanced": True,
            "semantic_target": "INCREASE_VS_DECREASE_OR_SAME",
            "mapping_family_sha256": receipt["mapping_family_sha256"],
        })
        candidate["semantic_counterbalance_receipt"] = receipt
        candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    out = _output_dir_from_argv(sys.argv)
    base = load_base_module()
    receipt = patch_base(base)
    rc = int(base.main())
    postprocess_outputs(base, out, receipt)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
