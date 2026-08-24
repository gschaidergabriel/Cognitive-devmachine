#!/usr/bin/env python3
"""Counterbalanced semantic successor for the Trigger-1 intermediate Qwen experiment.

The base experiment demonstrates an intermediate hidden-state intervention but its
calibration/holdout task currently maps every evaluated proposition to literal YES.
That permits a generic affirmative-token direction to look like a proposition-aware
effect. This successor keeps the same exact Qwen/runtime/vector machinery and changes
only the scientific discriminator:

* calibration and holdout contain true + false propositions;
* every proposition is evaluated under NORMAL and REVERSED yes/no label mappings;
* selection/adjudication operate on the expected-label-oriented margin rather than
  raw YES-minus-NO;
* a literal YES bias therefore cannot pass all paired cases;
* promotion metadata truthfully declares output-token use and counterbalancing.

No provider credential or paid route is introduced. A PASS remains a promotion
candidate only; canonical/J-Space/training/whole-product credit is not minted here.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import trigger1_local_qwen06_intermediate_api_execute as base

SCHEMA = "CLAY_TRIGGER1_INTERMEDIATE_SEMANTIC_BALANCE/v1"


def _case(seed: int, proposition_id: str, statement: str, truth: bool, mapping: str) -> dict[str, Any]:
    if mapping not in {"NORMAL", "REVERSED"}:
        raise ValueError("UNKNOWN_MAPPING")
    if mapping == "NORMAL":
        expected = "YES" if truth else "NO"
        code = "yes = the statement is true; no = the statement is false"
    else:
        expected = "NO" if truth else "YES"
        code = "no = the statement is true; yes = the statement is false"
    prompt = f"/no_think\nAnswer using only yes or no. Code: {code}. Statement: {statement}"
    return {
        "seed": seed,
        "proposition_id": proposition_id,
        "statement": statement,
        "semantic_truth": truth,
        "mapping": mapping,
        "expected_label": expected,
        "prompt": prompt,
    }


CALIBRATION_CASES = (
    _case(1801, "water-composition", "Water is made of hydrogen and oxygen.", True, "NORMAL"),
    _case(1802, "water-composition", "Water is made of hydrogen and oxygen.", True, "REVERSED"),
    _case(1803, "paris-germany", "Paris is located in Germany.", False, "NORMAL"),
    _case(1804, "paris-germany", "Paris is located in Germany.", False, "REVERSED"),
)

HOLDOUT_CASES = (
    _case(2801, "two-plus-two", "Two plus two equals four.", True, "NORMAL"),
    _case(2802, "two-plus-two", "Two plus two equals four.", True, "REVERSED"),
    _case(2803, "earth-star", "Earth is a star.", False, "NORMAL"),
    _case(2804, "earth-star", "Earth is a star.", False, "REVERSED"),
    _case(2805, "triangle-sides", "A triangle has three sides.", True, "NORMAL"),
    _case(2806, "triangle-sides", "A triangle has three sides.", True, "REVERSED"),
    _case(2807, "pacific-lake", "The Pacific Ocean is smaller than Lake Victoria.", False, "NORMAL"),
    _case(2808, "pacific-lake", "The Pacific Ocean is smaller than Lake Victoria.", False, "REVERSED"),
)

_CASE_BY_SEED = {int(c["seed"]): c for c in (*CALIBRATION_CASES, *HOLDOUT_CASES)}


def design_counterbalanced(cases: tuple[dict[str, Any], ...]) -> bool:
    if not cases:
        return False
    labels = {str(c["expected_label"]) for c in cases}
    truths = {bool(c["semantic_truth"]) for c in cases}
    if labels != {"YES", "NO"} or truths != {False, True}:
        return False
    by_prop: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_prop.setdefault(str(case["proposition_id"]), []).append(case)
    if not by_prop:
        return False
    for pair in by_prop.values():
        mappings = {str(c["mapping"]) for c in pair}
        expected = {str(c["expected_label"]) for c in pair}
        if mappings != {"NORMAL", "REVERSED"} or expected != {"YES", "NO"}:
            return False
    return True


def expected_sign(seed: int) -> float:
    case = _CASE_BY_SEED.get(int(seed))
    if case is None:
        raise KeyError(f"UNKNOWN_SEED:{seed}")
    return 1.0 if case["expected_label"] == "YES" else -1.0


def oriented_score(row: dict[str, Any]) -> float:
    return expected_sign(int(row["seed"])) * float(row["target_score"])


def select_config(rows: list[dict[str, Any]]) -> tuple[int, float] | None:
    """Select only a layer/gain that improves expected-label margin in every case."""
    ranked: list[tuple[float, float, int, float]] = []
    for layer in base.CANDIDATE_LAYERS:
        for gain in base.CALIBRATION_GAINS:
            by_seed: dict[int, dict[str, float]] = {}
            for row in rows:
                if int(row["layer"]) != layer or float(row["gain"]) != float(gain):
                    continue
                by_seed.setdefault(int(row["seed"]), {})[str(row["control"])] = oriented_score(row)
            plus_delta: list[float] = []
            sign_delta: list[float] = []
            for seed in sorted(by_seed):
                values = by_seed[seed]
                if all(k in values for k in ("BASELINE", "+VECTOR", "SIGN_FLIP")):
                    plus_delta.append(values["+VECTOR"] - values["BASELINE"])
                    sign_delta.append(values["BASELINE"] - values["SIGN_FLIP"])
            if len(plus_delta) != len(CALIBRATION_CASES):
                continue
            worst = min(min(plus_delta), min(sign_delta))
            mean = (sum(plus_delta) + sum(sign_delta)) / (len(plus_delta) + len(sign_delta))
            ranked.append((worst, mean, layer, float(gain)))
    ranked.sort(reverse=True)
    if not ranked or ranked[0][0] <= 0:
        return None
    return ranked[0][2], ranked[0][3]


def adjudicate(rows: list[dict[str, Any]], selected: tuple[int, float] | None) -> dict[str, Any]:
    if selected is None:
        return {
            "pass": False,
            "classification": "NO_COUNTERBALANCED_DIRECTIONAL_CALIBRATION_CONFIG",
            "semantic_counterbalance": True,
        }
    layer, gain = selected
    by_seed: dict[int, dict[str, float]] = {}
    for row in rows:
        by_seed.setdefault(int(row["seed"]), {})[str(row["control"])] = oriented_score(row)

    plus_delta: list[float] = []
    sign_delta: list[float] = []
    null_drift: list[float] = []
    orth_delta: list[float] = []
    perm_delta: list[float] = []
    for seed in sorted(by_seed):
        values = by_seed[seed]
        required = {"BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR", "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM"}
        if not required.issubset(values):
            continue
        base_score = values["BASELINE"]
        plus_delta.append(values["+VECTOR"] - base_score)
        sign_delta.append(base_score - values["SIGN_FLIP"])
        null_drift.append(abs(values["NULL_VECTOR"] - base_score))
        orth_delta.append(values["ORTHOGONAL_SAME_NORM"] - base_score)
        perm_delta.append(values["PERMUTED_SAME_NORM"] - base_score)

    expected_n = len(HOLDOUT_CASES)
    mean_plus = sum(plus_delta) / len(plus_delta) if plus_delta else float("-inf")
    best_nuisance = max(
        sum(orth_delta) / len(orth_delta) if orth_delta else float("inf"),
        sum(perm_delta) / len(perm_delta) if perm_delta else float("inf"),
    )
    passed = bool(
        design_counterbalanced(HOLDOUT_CASES)
        and len(plus_delta) == expected_n
        and min(plus_delta) > 0
        and min(sign_delta) > 0
        and max(null_drift) <= 1e-5
        and mean_plus > best_nuisance
        and all(int(r.get("hook_calls", 0)) > 0 for r in rows if r.get("control") != "BASELINE")
    )
    return {
        "pass": passed,
        "classification": (
            "COUNTERBALANCED_INTERMEDIATE_SEMANTIC_VECTOR_EFFECT_REPRODUCED"
            if passed
            else "COUNTERBALANCED_INTERMEDIATE_CONTROL_FAMILY_DID_NOT_ESTABLISH_SEMANTIC_EFFECT"
        ),
        "semantic_counterbalance": True,
        "selected_layer": layer,
        "selected_gain": gain,
        "holdout_cases": expected_n,
        "min_expected_margin_plus_vs_baseline": min(plus_delta) if plus_delta else None,
        "min_expected_margin_baseline_vs_sign_flip": min(sign_delta) if sign_delta else None,
        "max_null_drift": max(null_drift) if null_drift else None,
        "mean_expected_margin_plus_delta": mean_plus if plus_delta else None,
        "best_same_norm_nuisance_delta": best_nuisance if orth_delta and perm_delta else None,
        "strongest_counterexample_plus_delta": min(plus_delta) if plus_delta else None,
    }


def _git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", "-C", str(base.ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    return proc.returncode, proc.stdout.strip()


def source_snapshot() -> dict[str, Any]:
    rc_h, head = _git("rev-parse", "HEAD")
    rc_t, tree = _git("rev-parse", "HEAD^{tree}")
    rc_s, status = _git("status", "--porcelain=v1", "--untracked-files=all")
    wrapper_path = Path(__file__).resolve()
    base_path = Path(base.__file__).resolve()
    return {
        "repo_head": head if rc_h == 0 else None,
        "repo_tree": tree if rc_t == 0 else None,
        "worktree_clean": rc_s == 0 and status == "",
        "worktree_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest() if rc_s == 0 else None,
        "balanced_wrapper_sha256": base.sha256_file(wrapper_path),
        "base_executor_sha256": base.sha256_file(base_path),
    }


def _output_dir_from_argv() -> Path | None:
    for idx, item in enumerate(sys.argv[:-1]):
        if item == "--output-dir":
            return Path(sys.argv[idx + 1])
    return None


def _augment_result_and_candidate(out: Path, pre: dict[str, Any], post: dict[str, Any], rc: int) -> int:
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    mapping_spec = {
        "schema": SCHEMA,
        "metric": "expected-label-oriented YES-minus-NO logit margin",
        "normal_mapping": {"true": "YES", "false": "NO"},
        "reversed_mapping": {"true": "NO", "false": "YES"},
        "calibration_family": [
            {k: c[k] for k in ("seed", "proposition_id", "semantic_truth", "mapping", "expected_label")}
            for c in CALIBRATION_CASES
        ],
        "holdout_family": [
            {k: c[k] for k in ("seed", "proposition_id", "semantic_truth", "mapping", "expected_label")}
            for c in HOLDOUT_CASES
        ],
    }
    metric_sha = base.canonical_sha(mapping_spec)
    derivation_material = {
        "method": "intermediate residual activation contrast mean(positive anchors)-mean(negative anchors), normalized per layer",
        "uses_output_head_weights": False,
        "uses_holdout_data": False,
        "positive_anchor_family_sha256": base.canonical_sha(base.POSITIVE_ANCHORS),
        "negative_anchor_family_sha256": base.canonical_sha(base.NEGATIVE_ANCHORS),
        "candidate_layers": list(base.CANDIDATE_LAYERS),
    }
    derivation_family = base.canonical_sha({
        "positive": base.POSITIVE_ANCHORS,
        "negative": base.NEGATIVE_ANCHORS,
    })
    derivation_receipt = base.canonical_sha(derivation_material)
    stable = bool(
        pre.get("worktree_clean")
        and post.get("worktree_clean")
        and pre.get("repo_head") == post.get("repo_head")
        and pre.get("repo_tree") == post.get("repo_tree")
        and pre.get("balanced_wrapper_sha256") == post.get("balanced_wrapper_sha256")
        and pre.get("base_executor_sha256") == post.get("base_executor_sha256")
    )

    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["semantic_balance"] = {
            "schema": SCHEMA,
            "design_counterbalanced": design_counterbalanced(CALIBRATION_CASES) and design_counterbalanced(HOLDOUT_CASES),
            "metric_definition": mapping_spec,
            "metric_definition_sha256": metric_sha,
            "source_pre": pre,
            "source_post": post,
            "source_stable_and_clean": stable,
        }
        if not stable and result.get("status") == "PASS":
            result["status"] = "SOURCE_IDENTITY_DRIFT_OR_DIRTY"
        result.pop("result_sha256", None)
        result["result_sha256"] = base.canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    if candidate_path.is_file():
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["source_identity"].update({
            "repo_tree": post.get("repo_tree"),
            "worktree_clean": bool(post.get("worktree_clean")),
            "balanced_wrapper_sha256": post.get("balanced_wrapper_sha256"),
            "base_executor_sha256": post.get("base_executor_sha256"),
        })
        candidate["vector_derivation"] = {
            **derivation_material,
            "derivation_family_id": derivation_family,
            "derivation_receipt_sha256": derivation_receipt,
        }
        holdout = candidate.setdefault("holdout", {})
        holdout.update({
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": metric_sha,
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
            "semantic_truth_counterbalanced": True,
        })
        candidate["semantic_balance"] = {
            "schema": SCHEMA,
            "design_counterbalanced": True,
            "source_stable_and_clean": stable,
            "metric_definition_sha256": metric_sha,
        }
        if not stable:
            candidate_path.unlink()
            return 4
        candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    if not design_counterbalanced(CALIBRATION_CASES) or not design_counterbalanced(HOLDOUT_CASES):
        raise RuntimeError("SEMANTIC_BALANCE_DESIGN_INVALID")
    pre = source_snapshot()
    out = _output_dir_from_argv()
    if out is None:
        raise SystemExit("--output-dir is required")
    out.mkdir(parents=True, exist_ok=True)
    if not pre.get("worktree_clean"):
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_DIRTY_SOURCE_PRE_RUNTIME",
            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_pre": pre,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
        blocked["result_sha256"] = base.canonical_sha(blocked)
        (out / "trigger1_local_activation_api_result.json").write_text(
            json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return 4

    base.CALIBRATION = tuple((int(c["seed"]), str(c["prompt"])) for c in CALIBRATION_CASES)
    base.HOLDOUT = tuple((int(c["seed"]), str(c["prompt"])) for c in HOLDOUT_CASES)
    base.select_config = select_config
    base.adjudicate = adjudicate

    rc = base.main()
    post = source_snapshot()
    return _augment_result_and_candidate(out, pre, post, rc)


if __name__ == "__main__":
    raise SystemExit(main())
