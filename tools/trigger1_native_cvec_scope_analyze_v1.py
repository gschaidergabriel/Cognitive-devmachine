#!/usr/bin/env python3
"""Analyze native llama.cpp cvec BROADCAST versus LAST_TOKEN_ONLY scope.

The strongest intended use is NOT to force the two interventions to be called causally
identical.  Instead:

* prove that LAST_TOKEN_ONLY really prefills the prefix before any cvec is installed;
* test immediate layer-(il+1) actuator parity against BROADCAST on the same final token;
* measure, but do not assume, later downstream/logit parity.

A downstream difference is scientifically informative rather than a failure of the
localized actuator: BROADCAST has also changed earlier prompt-token states above the
injection layer.  Semantic promotion can therefore use LAST_TOKEN_ONLY as the scope-matched
native intervention and keep BROADCAST as a distinct operational variant.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_NATIVE_CVEC_SCOPE_ANALYSIS/v1"
HEADER = "CLAY_LLAMA_CPP_CVEC_SCOPE_PROBE_HEADER/v1"
ROW = "CLAY_LLAMA_CPP_CVEC_SCOPE_PROBE_OBSERVATION/v1"
MODES = ("BASELINE", "BROADCAST", "LAST_TOKEN_ONLY")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _vector(value: Any, prefix: str, failures: list[str]) -> list[float] | None:
    if not isinstance(value, list) or not value:
        failures.append(f"{prefix}_VECTOR_REQUIRED")
        return None
    out: list[float] = []
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)):
            failures.append(f"{prefix}_NONFINITE:{index}")
            return None
        out.append(float(item))
    return out


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def _norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def _cosine(a: list[float], b: list[float]) -> float | None:
    na = _norm(a)
    nb = _norm(b)
    if na <= 1e-12 or nb <= 1e-12:
        return None
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def _relative_difference(a: list[float], b: list[float]) -> float | None:
    denom = max(_norm(a), _norm(b))
    if denom <= 1e-12:
        return None
    return _norm(_sub(a, b)) / denom


def _logit_vector(row: dict[str, Any], prefix: str, failures: list[str]) -> list[float] | None:
    logits = row.get("token_logits")
    if not isinstance(logits, dict):
        failures.append(f"{prefix}_TOKEN_LOGITS_REQUIRED")
        return None
    out: list[float] = []
    for key in ("A", "B", "C"):
        value = logits.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
            failures.append(f"{prefix}_TOKEN_LOGIT_INVALID:{key}")
            return None
        out.append(float(value))
    return out


def analyze(payload: Any, *, immediate_cosine_min: float = 0.9999, immediate_relative_difference_max: float = 1e-3) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(payload, list) or not payload:
        return {
            "schema": SCHEMA,
            "pass": False,
            "localized_native_scope_pass": False,
            "immediate_actuator_equivalence_pass": False,
            "failures": ["JSONL_ROWS_REQUIRED"],
            "canonical_credit_minted": False,
        }

    header = payload[0] if isinstance(payload[0], dict) else {}
    if header.get("schema") != HEADER:
        failures.append("SCOPE_PROBE_HEADER_INVALID")
    if header.get("native_api") != "llama_set_adapter_cvec":
        failures.append("NATIVE_API_MISMATCH")

    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for index, raw in enumerate(payload[1:]):
        prefix = f"ROW_{index}"
        if not isinstance(raw, dict) or raw.get("schema") != ROW:
            failures.append(f"{prefix}_SCHEMA_INVALID")
            continue
        case_id = raw.get("case_id")
        mode = raw.get("mode")
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
            continue
        if mode not in MODES:
            failures.append(f"{prefix}_MODE_INVALID")
            continue
        if mode in grouped.setdefault(case_id, {}):
            failures.append(f"{prefix}_DUPLICATE_MODE:{case_id}:{mode}")
            continue
        grouped[case_id][str(mode)] = raw

    if not grouped:
        failures.append("NO_SCOPE_CASES")

    cases: list[dict[str, Any]] = []
    all_localized = True
    all_immediate = True
    for case_id in sorted(grouped):
        rows = grouped[case_id]
        missing = [mode for mode in MODES if mode not in rows]
        if missing:
            failures.append(f"CASE_MODES_MISSING:{case_id}:{','.join(missing)}")
            all_localized = False
            all_immediate = False
            continue
        baseline = rows["BASELINE"]
        broad = rows["BROADCAST"]
        local = rows["LAST_TOKEN_ONLY"]

        prompt_counts = {row.get("prompt_tokens") for row in rows.values()}
        layer_pairs = {(row.get("primary_layer_inp"), row.get("downstream_layer_inp")) for row in rows.values()}
        if len(prompt_counts) != 1:
            failures.append(f"PROMPT_TOKEN_COUNT_MISMATCH:{case_id}")
        if len(layer_pairs) != 1:
            failures.append(f"CAPTURE_LAYER_MISMATCH:{case_id}")

        local_scope_ok = bool(
            local.get("token_scope") == "LAST_TOKEN_DECODE_ONLY"
            and local.get("cvec_set_before_prefix") is False
            and local.get("cvec_set_after_prefix") is True
            and local.get("final_decode_tokens") == 1
            and isinstance(local.get("prompt_tokens"), int)
            and local.get("prefix_decode_tokens") == local.get("prompt_tokens") - 1
            and broad.get("token_scope") == "ALL_PROMPT_TOKENS"
            and broad.get("cvec_set_before_prefix") is True
            and broad.get("cvec_set_after_prefix") is False
            and baseline.get("token_scope") == "NO_INTERVENTION"
            and baseline.get("cvec_set_before_prefix") is False
            and baseline.get("cvec_set_after_prefix") is False
        )
        if not local_scope_ok:
            failures.append(f"LOCALIZED_SCOPE_PROOF_FAILED:{case_id}")
            all_localized = False

        b0 = _vector(baseline.get("primary_activation"), f"{case_id}_BASE_PRIMARY", failures)
        bb = _vector(broad.get("primary_activation"), f"{case_id}_BROAD_PRIMARY", failures)
        bl = _vector(local.get("primary_activation"), f"{case_id}_LOCAL_PRIMARY", failures)
        d0 = _vector(baseline.get("downstream_activation"), f"{case_id}_BASE_DOWNSTREAM", failures)
        db = _vector(broad.get("downstream_activation"), f"{case_id}_BROAD_DOWNSTREAM", failures)
        dl = _vector(local.get("downstream_activation"), f"{case_id}_LOCAL_DOWNSTREAM", failures)
        logits0 = _logit_vector(baseline, f"{case_id}_BASE", failures)
        logitsb = _logit_vector(broad, f"{case_id}_BROAD", failures)
        logitsl = _logit_vector(local, f"{case_id}_LOCAL", failures)

        immediate_cos = None
        immediate_rel = None
        downstream_cos = None
        downstream_rel = None
        logit_effect_cos = None
        logit_effect_rel = None
        if b0 is not None and bb is not None and bl is not None:
            if len({len(b0), len(bb), len(bl)}) != 1:
                failures.append(f"PRIMARY_DIMENSION_MISMATCH:{case_id}")
                all_immediate = False
            else:
                broad_effect = _sub(bb, b0)
                local_effect = _sub(bl, b0)
                immediate_cos = _cosine(broad_effect, local_effect)
                immediate_rel = _relative_difference(broad_effect, local_effect)
                immediate_ok = bool(
                    immediate_cos is not None
                    and immediate_rel is not None
                    and immediate_cos >= immediate_cosine_min
                    and immediate_rel <= immediate_relative_difference_max
                )
                if not immediate_ok:
                    failures.append(f"IMMEDIATE_ACTUATOR_PARITY_FAILED:{case_id}")
                    all_immediate = False
        else:
            all_immediate = False

        if d0 is not None and db is not None and dl is not None and len({len(d0), len(db), len(dl)}) == 1:
            downstream_cos = _cosine(_sub(db, d0), _sub(dl, d0))
            downstream_rel = _relative_difference(_sub(db, d0), _sub(dl, d0))

        if logits0 is not None and logitsb is not None and logitsl is not None:
            logit_effect_cos = _cosine(_sub(logitsb, logits0), _sub(logitsl, logits0))
            logit_effect_rel = _relative_difference(_sub(logitsb, logits0), _sub(logitsl, logits0))

        cases.append(
            {
                "case_id": case_id,
                "localized_scope_pass": local_scope_ok,
                "immediate_effect_cosine": immediate_cos,
                "immediate_effect_relative_difference": immediate_rel,
                "downstream_effect_cosine_diagnostic_only": downstream_cos,
                "downstream_effect_relative_difference_diagnostic_only": downstream_rel,
                "abc_logit_effect_cosine_diagnostic_only": logit_effect_cos,
                "abc_logit_effect_relative_difference_diagnostic_only": logit_effect_rel,
            }
        )

    localized_pass = bool(grouped and all_localized and not any("LOCALIZED_SCOPE_PROOF_FAILED" in f for f in failures))
    immediate_pass = bool(grouped and all_immediate and not any("IMMEDIATE_ACTUATOR_PARITY_FAILED" in f for f in failures))
    structural_failures = [
        f for f in failures
        if not f.startswith("IMMEDIATE_ACTUATOR_PARITY_FAILED")
    ]
    result_core = {
        "schema": SCHEMA,
        "localized_native_scope_pass": localized_pass,
        "immediate_actuator_equivalence_pass": immediate_pass,
        "pass": localized_pass and immediate_pass and not structural_failures,
        "case_count": len(cases),
        "cases": cases,
        "immediate_cosine_min": immediate_cosine_min,
        "immediate_relative_difference_max": immediate_relative_difference_max,
        "broadcast_full_causal_identity_claimed": False,
        "downstream_and_behavioral_parity_are_diagnostics_not_assumptions": True,
        "failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "evidence_boundary": (
            "PASS proves the native LAST_TOKEN_ONLY decode contract and immediate post-injection actuator parity "
            "against BROADCAST for the observed cases. It intentionally does not declare the broader BROADCAST "
            "intervention causally identical downstream, because BROADCAST also perturbs earlier prompt-token states."
        ),
    }
    result_core["analysis_sha256"] = canonical_sha(result_core)
    return result_core


def load_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSONL_DECODE_FAILED:{line_no}") from exc
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(load_jsonl(args.observations))
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
