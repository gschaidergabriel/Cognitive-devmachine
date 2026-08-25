#!/usr/bin/env python3
"""Prospective strict post-runtime adjudicator for the frozen structural-native Trigger-1 run.

This tool is intentionally separate from the frozen executor. It must be fixed before the
held-out runtime result is observed. It re-derives causal quantities from persisted raw bytes
and can only grant a bounded structural-native diagnostic candidate; it never promotes
canonical semantics, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_NATIVE_POSTHOC_GATE/v1"
RESULT_SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_NATIVE_ABSTRACT_RUNTIME/v1"
LOGIT_SCHEMA = "CLAY_LLAMA_CPP_CVEC_LOGIT_OBSERVATION/v1"
CAPTURE_SCHEMA = "CLAY_LLAMA_CPP_LAYER_CAPTURE_OBSERVATION/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
CONTROLS = ("null", "orth", "perm", "nuis")
REQUIRED_FILES = (
    "manifest.json",
    "trigger1_structural_native_abstract_result.json",
    "structural_case_bundle.json",
    "residualized_layer24.json",
    "holdout.logits.stdout.jsonl",
    "holdout.capture.stdout.jsonl",
)
FROZEN_GIT_BLOBS = {
    "tools/trigger1_structural_label_free_cases.py": "66bb2f5cfccad602ee9c759961a369ab2c61be41",
    "tools/trigger1_structural_native_abstract_execute.py": "0711e07609c2f402db9762cf9495c31cae7888e8",
    "tools/trigger1_nuisance_residualize.py": "aeec098dfa26b93d3edc376ec69fd846220184d7",
    "tools/trigger1_native_llamacpp_layer_capture.cpp": "bfe014a67e6c5420c1e20a94f2da37616dcf94ed",
    "tools/trigger1_native_llamacpp_cvec_logits.cpp": "c9f649b8a803ff999b07e9c40c90f5f92e08c86d",
    ".github/workflows/clay-trigger1-structural-native-abstract-run.yml": "25f24c8dd99790390b5c31e44b692ae18230a596",
}


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"OBJECT_REQUIRED:{path.name}")
    return value


def _parse_jsonl(path: Path, row_schema: str) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"EMPTY_JSONL:{path.name}")
    out: dict[str, dict[str, Any]] = {}
    for row in rows[1:]:
        if row.get("schema") != row_schema:
            raise ValueError(f"ROW_SCHEMA_MISMATCH:{path.name}:{row.get('schema')}")
        cid = str(row.get("case_id") or "")
        if not cid or cid in out:
            raise ValueError(f"CASE_ID_INVALID_OR_DUPLICATE:{path.name}:{cid}")
        out[cid] = row
    return out


def _margin(row: dict[str, Any], code: str) -> float:
    logits = row.get("token_logits")
    if not isinstance(logits, dict) or any(c not in logits for c in CODES):
        raise ValueError("TOKEN_LOGITS_A_B_C_REQUIRED")
    other = [c for c in CODES if c != code]
    return float(logits[code]) - 0.5 * (float(logits[other[0]]) + float(logits[other[1]]))


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("NONEMPTY_VALUES_REQUIRED")
    return sum(values) / len(values)


def _dot(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("VECTOR_DIMENSION_MISMATCH")
    return sum(float(x) * float(y) for x, y in zip(a, b))


def _sub(a: list[float], b: list[float]) -> list[float]:
    if len(a) != len(b) or not a:
        raise ValueError("VECTOR_DIMENSION_MISMATCH")
    return [float(x) - float(y) for x, y in zip(a, b)]


def _manifest_integrity(runtime_dir: Path, failures: list[str]) -> bool:
    try:
        manifest = _load_json(runtime_dir / "manifest.json")
    except Exception as exc:
        failures.append(f"MANIFEST_INVALID:{type(exc).__name__}")
        return False
    entries = manifest.get("files")
    if not isinstance(entries, list):
        failures.append("MANIFEST_FILES_REQUIRED")
        return False
    by_name = {str(x.get("name")): x for x in entries if isinstance(x, dict)}
    ok = True
    for name in REQUIRED_FILES:
        if name == "manifest.json":
            continue
        path = runtime_dir / name
        row = by_name.get(name)
        if not path.is_file() or not isinstance(row, dict):
            failures.append(f"MANIFEST_REQUIRED_FILE_MISSING:{name}")
            ok = False
            continue
        if row.get("sha256") != _sha_file(path) or row.get("bytes") != path.stat().st_size:
            failures.append(f"MANIFEST_FILE_BINDING_MISMATCH:{name}")
            ok = False
    return ok


def _result_integrity(result: dict[str, Any], failures: list[str]) -> bool:
    ok = True
    if result.get("schema") != RESULT_SCHEMA:
        failures.append("RESULT_SCHEMA_MISMATCH")
        ok = False
    claimed = result.get("result_sha256")
    core = dict(result)
    core.pop("result_sha256", None)
    if claimed != _canonical_sha(core):
        failures.append("RESULT_CANONICAL_SHA256_MISMATCH")
        ok = False
    if result.get("native_token_scope") != "ALL_PROMPT_TOKENS":
        failures.append("NATIVE_SCOPE_NOT_ALL_PROMPT_TOKENS")
        ok = False
    if result.get("external_provider_used") is not False:
        failures.append("EXTERNAL_PROVIDER_USED_OR_UNKNOWN")
        ok = False
    expected_identity = {
        "model": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
        "gguf_sha256": "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
        "llama_cpp_commit": "bb4caa7540188872173c44d161602d9271386413",
        "native_api": "llama_set_adapter_cvec",
        "injection_layer": 20,
        "primary_layer_input": 21,
        "downstream_layer_input": 24,
    }
    for field, expected in expected_identity.items():
        if result.get(field) != expected:
            failures.append(f"RUNTIME_IDENTITY_MISMATCH:{field}")
            ok = False
    return ok


def _frozen_source_integrity(repo_root: Path | None, source_head: str, failures: list[str]) -> bool:
    if repo_root is None:
        failures.append("FROZEN_SOURCE_GIT_BINDING_NOT_CHECKED")
        return False
    if len(source_head) != 40 or any(c not in "0123456789abcdef" for c in source_head):
        failures.append("SOURCE_HEAD_INVALID")
        return False
    ok = True
    for path, expected in FROZEN_GIT_BLOBS.items():
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", f"{source_head}:{path}"],
            capture_output=True, text=True, check=False,
        )
        got = proc.stdout.strip() if proc.returncode == 0 else ""
        if got != expected:
            failures.append(f"FROZEN_SOURCE_BLOB_MISMATCH:{path}")
            ok = False
    return ok


def _bundle_cases(bundle: dict[str, Any], result: dict[str, Any], failures: list[str]) -> list[dict[str, Any]]:
    if bundle.get("bundle_sha256") != result.get("case_bundle_sha256"):
        failures.append("CASE_BUNDLE_RESULT_BINDING_MISMATCH")
    core = dict(bundle)
    claimed = core.pop("bundle_sha256", None)
    if claimed != _canonical_sha(core):
        failures.append("CASE_BUNDLE_CANONICAL_SHA256_MISMATCH")
    audit = bundle.get("lexical_disjointness_audit")
    if not isinstance(audit, dict) or audit.get("basis_holdout_lexically_disjoint") is not True or audit.get("content_overlap_count") != 0:
        failures.append("LEXICAL_DISJOINTNESS_FAILED")
    hold = bundle.get("holdout", {}).get("cases") if isinstance(bundle.get("holdout"), dict) else None
    if not isinstance(hold, list) or len(hold) != 9:
        failures.append("EXACT_NINE_HOLDOUT_CASES_REQUIRED")
        return []
    cells = {(x.get("semantic_target"), x.get("output_code_identity")) for x in hold if isinstance(x, dict)}
    if cells != {(t, c) for t in CLASSES for c in CODES}:
        failures.append("HOLDOUT_THREE_BY_THREE_FACTORIAL_REQUIRED")
    return [x for x in hold if isinstance(x, dict)]


def _rederive_behavior(hold: list[dict[str, Any]], logits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_target: dict[str, Any] = {}
    all_matched: list[float] = []
    all_sign: list[float] = []
    for target in CLASSES:
        cases = [c for c in hold if c.get("semantic_target") == target]
        matched: list[float] = []
        sign: list[float] = []
        controls = {name: [] for name in CONTROLS}
        diag: list[float] = []
        off: list[float] = []
        for case in cases:
            cid = str(case["case_id"])
            code = str(case["output_code_identity"])
            base = _margin(logits[f"h:{cid}:base"], code)
            for intervention in CLASSES:
                delta = _margin(logits[f"h:{cid}:sem:{intervention}"], code) - base
                (diag if intervention == target else off).append(delta)
            matched.append(_margin(logits[f"h:{cid}:sem:{target}"], code) - base)
            sign.append(_margin(logits[f"h:{cid}:sign"], code) - base)
            for ctrl in CONTROLS:
                controls[ctrl].append(_margin(logits[f"h:{cid}:{ctrl}"], code) - base)
        matched_mean = _mean(matched)
        sign_mean = _mean(sign)
        control_abs_means = {name: _mean([abs(x) for x in values]) for name, values in controls.items()}
        target_diag_advantage = _mean(diag) - _mean(off)
        per_target[target] = {
            "case_count": len(cases),
            "matched_mean_delta": matched_mean,
            "matched_each_case_positive": all(x > 0.0 for x in matched),
            "signflip_mean_delta": sign_mean,
            "signflip_each_case_negative": all(x < 0.0 for x in sign),
            "control_abs_mean_by_family": control_abs_means,
            "matched_above_each_control_abs_mean": all(matched_mean > x for x in control_abs_means.values()),
            "target_diagonal_advantage": target_diag_advantage,
            "target_diagonal_advantage_positive": target_diag_advantage > 0.0,
        }
        all_matched.extend(matched)
        all_sign.extend(sign)
    strict = all(
        row["matched_mean_delta"] > 0.0
        and row["matched_each_case_positive"]
        and row["signflip_mean_delta"] < 0.0
        and row["signflip_each_case_negative"]
        and row["matched_above_each_control_abs_mean"]
        and row["target_diagonal_advantage_positive"]
        for row in per_target.values()
    )
    return {
        "per_target": per_target,
        "aggregate_matched_mean_delta": _mean(all_matched),
        "aggregate_signflip_mean_delta": _mean(all_sign),
        "strict_behavioral_diagnostic_pass": strict,
    }


def _rederive_transport(hold: list[dict[str, Any]], captures: dict[str, dict[str, Any]], layer24: dict[str, Any]) -> dict[str, Any]:
    vectors = layer24.get("projected_semantic_unit_vectors")
    if not isinstance(vectors, dict) or any(c not in vectors for c in CLASSES):
        raise ValueError("LAYER24_SEMANTIC_VECTORS_REQUIRED")
    per_target: dict[str, Any] = {}
    for target in CLASSES:
        cases = [c for c in hold if c.get("semantic_target") == target]
        matched_target: list[float] = []
        sign_target: list[float] = []
        offaxis_abs: list[float] = []
        control_abs: list[float] = []
        for case in cases:
            cid = str(case["case_id"])
            base = [float(x) for x in captures[f"h:{cid}:base"]["downstream_activation"]]
            matched = [float(x) for x in captures[f"h:{cid}:sem:{target}"]["downstream_activation"]]
            sign = [float(x) for x in captures[f"h:{cid}:sign"]["downstream_activation"]]
            dmatch = _sub(matched, base)
            dsign = _sub(sign, base)
            matched_target.append(_dot(dmatch, vectors[target]))
            sign_target.append(_dot(dsign, vectors[target]))
            for other in CLASSES:
                if other != target:
                    offaxis_abs.append(abs(_dot(dmatch, vectors[other])))
            for ctrl in CONTROLS:
                dctrl = _sub([float(x) for x in captures[f"h:{cid}:{ctrl}"]["downstream_activation"]], base)
                control_abs.append(abs(_dot(dctrl, vectors[target])))
        mt = _mean(matched_target)
        st = _mean(sign_target)
        per_target[target] = {
            "case_count": len(cases),
            "matched_target_coordinate_mean": mt,
            "matched_each_case_positive": all(x > 0.0 for x in matched_target),
            "signflip_target_coordinate_mean": st,
            "signflip_each_case_negative": all(x < 0.0 for x in sign_target),
            "matched_offaxis_abs_mean": _mean(offaxis_abs),
            "control_target_coordinate_abs_mean": _mean(control_abs),
            "matched_dominates_offaxis_and_controls": mt > _mean(offaxis_abs) and mt > _mean(control_abs),
        }
    strict = all(
        row["matched_target_coordinate_mean"] > 0.0
        and row["matched_each_case_positive"]
        and row["signflip_target_coordinate_mean"] < 0.0
        and row["signflip_each_case_negative"]
        and row["matched_dominates_offaxis_and_controls"]
        for row in per_target.values()
    )
    return {"per_target": per_target, "strict_downstream_diagnostic_pass": strict}


def adjudicate(runtime_dir: Path, repo_root: Path | None = None) -> dict[str, Any]:
    failures: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (runtime_dir / name).is_file()]
    if missing:
        return {
            "schema": SCHEMA,
            "status": "BLOCKED_INCOMPLETE_RUNTIME_ARTIFACT",
            "failures": [f"REQUIRED_FILE_MISSING:{x}" for x in missing],
            "bounded_strict_structural_native_candidate": False,
            "canonical_credit_minted": False,
        }
    try:
        manifest_ok = _manifest_integrity(runtime_dir, failures)
        result = _load_json(runtime_dir / "trigger1_structural_native_abstract_result.json")
        result_ok = _result_integrity(result, failures)
        source_ok = _frozen_source_integrity(repo_root, str(result.get("source_head") or ""), failures)
        bundle = _load_json(runtime_dir / "structural_case_bundle.json")
        hold = _bundle_cases(bundle, result, failures)
        logits = _parse_jsonl(runtime_dir / "holdout.logits.stdout.jsonl", LOGIT_SCHEMA)
        captures = _parse_jsonl(runtime_dir / "holdout.capture.stdout.jsonl", CAPTURE_SCHEMA)
        layer24 = _load_json(runtime_dir / "residualized_layer24.json")
        behavior = _rederive_behavior(hold, logits)
        transport = _rederive_transport(hold, captures, layer24)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        failures.append(f"ADJUDICATION_EXCEPTION:{type(exc).__name__}:{exc}")
        return {
            "schema": SCHEMA,
            "status": "BLOCKED_INVALID_RUNTIME_ARTIFACT",
            "failures": sorted(set(failures)),
            "bounded_strict_structural_native_candidate": False,
            "canonical_credit_minted": False,
        }
    bounded = bool(
        manifest_ok
        and result_ok
        and source_ok
        and not failures
        and result.get("status") == "PASS_ABSTRACT_NATIVE_DISCRIMINATOR"
        and behavior["strict_behavioral_diagnostic_pass"]
        and transport["strict_downstream_diagnostic_pass"]
    )
    promotion_blockers = [
        "GAIN_PROTOCOL_CALIBRATION_TUNED_NOT_RUN1_FIXED_32",
        "RUN1_GEOMETRIC_COHERENCE_PERMUTATION_NULL_NOT_EXECUTED",
        "RUN1_OFF_TARGET_REGRESSION_NOT_EXECUTED",
        "SINGLE_SYNTHETIC_TASK_GRAMMAR_ONLY",
        "ONE_OBSERVATION_PER_TARGET_X_CODE_CELL",
        "NOT_V12_SIX_FAMILY_ABSTRACT_CHALLENGE_RUNTIME_BINDING",
    ]
    return {
        "schema": SCHEMA,
        "status": "PASS_BOUNDED_STRICT_DIAGNOSTIC" if bounded else "FAIL_OR_BLOCKED_BOUNDED_STRICT_DIAGNOSTIC",
        "runtime_manifest_integrity_pass": manifest_ok,
        "result_integrity_pass": result_ok,
        "frozen_source_git_binding_pass": source_ok,
        "source_head": result.get("source_head"),
        "executor_status": result.get("status"),
        "selected_gain": result.get("selected_gain_calibration_only"),
        "behavior_rederived_from_raw_logs": behavior,
        "downstream_rederived_from_raw_captures": transport,
        "bounded_strict_structural_native_candidate": bounded,
        "promotion_blockers": promotion_blockers,
        "failures": sorted(set(failures)),
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": 0,
        "whole_hcu_credit": 0,
        "whole_entityos_hcu_credit": 0,
        "training_credit": 0,
        "canonical_credit_minted": False,
        "evidence_boundary": (
            "Prospectively frozen post-runtime reanalysis of the already-dispatched single-grammar structural native run. "
            "A PASS strengthens only bounded Qwen3-0.6B structural-native causal component evidence and cannot close the "
            "missing geometry, off-target, cross-task-family, replication, v12 binding, global J-Space, HCU, EntityOS, or training gates."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime-dir", required=True)
    ap.add_argument("--repo-root")
    args = ap.parse_args()
    out = adjudicate(Path(args.runtime_dir), Path(args.repo_root) if args.repo_root else None)
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
