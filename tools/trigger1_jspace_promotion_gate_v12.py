#!/usr/bin/env python3
"""Row-level hard successor for Trigger-1 semantic J-Space promotion.

v12 does not replace merged v11; it makes its two remaining scientific assertions
executable at exact case level:

* source-frozen 6-family x 3-state calibration/holdout plan with evaluator-only labels,
  exact within-family lexical-multiset matching, target/marker/output-code counterbalance,
  and calibration/holdout content-lexicon disjointness; and
* native llama.cpp cvec temporal decomposition using BASELINE_{SINGLE,SPLIT},
  BROADCAST_{SINGLE,SPLIT}, LAST_TOKEN_ONLY and PREFIX_ONLY on the same per-target cvec.

Positive v12 status requires target-selective internal + behavioral effects in all six
holdout families and bounded last-token mediation/equivalence. Strict microscopic
mechanistic identity is never claimed. This adjudicator executes no model and mints no
canonical/runtime/HCU/EntityOS/training/effect credit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from tools import trigger1_jspace_promotion_gate_v11 as v11
from tools import trigger1_abstract_state_case_plan_v1 as case_plan

SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12"
ABSTRACT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_EVIDENCE/v1"
TEMPORAL_SCHEMA = "CLAY_TRIGGER1_NATIVE_CVEC_TEMPORAL_SCOPE_EVIDENCE/v1"
NATIVE_API = "llama_set_adapter_cvec"
EXPECTED_PLAN_SHA = "f15bd5ac4ea7cf51ec7cd2ffa92787ce5a3c7204f54b5099f918516ba66e5289"
EXPECTED_PLAN_SOURCE_SHA = "01b861da74b45a1fe6697a7ad2e2a69c64bda59102e554f0f80584567584edac"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
ABSTRACT_ARMS = ("BASELINE", "CVEC_AFFIRMATIVE", "CVEC_NEGATIVE", "CVEC_NEUTRAL")
TEMPORAL_ARMS = (
    "BASELINE_SINGLE", "BASELINE_SPLIT", "BROADCAST_SINGLE",
    "BROADCAST_SPLIT", "LAST_TOKEN_ONLY", "PREFIX_ONLY",
)
CUE_TERMS = {
    "affirmative", "negative", "neutral", "yes", "no", "agree", "disagree",
    "approve", "disapprove", "accept", "reject", "allow", "deny", "permit",
    "forbid", "proceed", "decline", "defer", "pending", "abstain", "support",
    "oppose", "refuse", "true", "false", "unknown", "undetermined", "uncertain",
}
TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


def sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def is_sha(x: Any) -> bool:
    if not isinstance(x, str) or len(x) != 64: return False
    try: int(x, 16)
    except ValueError: return False
    return x == x.lower()


def finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


# Compatibility names used by deterministic source-level tests.
canonical_sha = sha

def _tokens(prompt: str, scaffold: set[str]) -> list[str]:
    prompt = prompt.lower().replace("/no_think", " ")
    out = []
    for token in TOKEN_RE.findall(prompt):
        token = "<num>" if token.isdigit() else token
        if token not in scaffold:
            out.append(token)
    return out


def source_plan() -> tuple[dict[str, Any], list[str]]:
    fail: list[str] = []
    try:
        source_bytes = Path(case_plan.__file__).read_bytes()
        plan = case_plan.build_plan()
    except Exception as exc:
        return {}, [f"FROZEN_PLAN_UNAVAILABLE:{type(exc).__name__}"]
    if hashlib.sha256(source_bytes).hexdigest() != EXPECTED_PLAN_SOURCE_SHA:
        fail.append("FROZEN_PLAN_SOURCE_SHA_MISMATCH")
    if plan.get("plan_sha256") != EXPECTED_PLAN_SHA:
        fail.append("FROZEN_PLAN_SHA_MISMATCH")
    if plan.get("model_executed") is not False or plan.get("holdout_opened_for_model_execution") is not False:
        fail.append("FROZEN_PLAN_MUST_BE_PRERUNTIME")
    return plan, fail


def plan_invariants(plan: dict[str, Any]) -> list[str]:
    fail: list[str] = []
    scaffold = set(plan.get("fixed_scaffold_tokens") or [])
    split_vocab: dict[str, set[str]] = {}
    for split, key in (("CAL", "calibration_case_rows"), ("HOLD", "holdout_case_rows")):
        rows = plan.get(key)
        if not isinstance(rows, list) or len(rows) != 18:
            fail.append(f"{split}_EXACT_18_CASES_REQUIRED"); continue
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        tc = Counter(); ts = Counter(); vocab: set[str] = set()
        for row in rows:
            prompt = str(row.get("prompt") or "")
            if hashlib.sha256(prompt.encode()).hexdigest() != row.get("prompt_sha256"):
                fail.append(f"{split}_PROMPT_SHA_MISMATCH:{row.get('case_id')}")
            observed = set(TOKEN_RE.findall(prompt.lower().replace("/no_think", " ")))
            hits = observed & CUE_TERMS
            if hits: fail.append(f"{split}_DIRECT_CUE:{row.get('case_id')}:{','.join(sorted(hits))}")
            target, code = row.get("semantic_target"), row.get("output_code_identity")
            tc[(target, code)] += 1; ts[(target, row.get("marker_slot"))] += 1
            by_family[str(row.get("scenario_family_sha256"))].append(row)
            vocab.update(case_plan.content_tokens(prompt))
        if set(tc.values()) != {2} or len(tc) != 9: fail.append(f"{split}_TARGET_CODE_COUNTERBALANCE_REQUIRED")
        if set(ts.values()) != {2} or len(ts) != 9: fail.append(f"{split}_TARGET_SLOT_COUNTERBALANCE_REQUIRED")
        if len(by_family) != 6: fail.append(f"{split}_SIX_FAMILIES_REQUIRED")
        for family, fr in by_family.items():
            if len(fr) != 3 or {r.get("semantic_target") for r in fr} != set(TARGETS) or {r.get("output_code_identity") for r in fr} != set(CODES):
                fail.append(f"{split}_FAMILY_FACTORIAL_REQUIRED:{family}"); continue
            bags = [Counter(case_plan.content_tokens(str(r.get("prompt") or ""))) for r in fr]
            if not (bags[0] == bags[1] == bags[2]): fail.append(f"{split}_FAMILY_LEXICAL_MULTISET_MISMATCH:{family}")
        split_vocab[split] = vocab
    if split_vocab.get("CAL", set()) & split_vocab.get("HOLD", set()): fail.append("CAL_HOLD_CONTENT_LEXICON_MUST_BE_DISJOINT")
    return sorted(set(fail))


def frozen_holdout(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(r["case_id"]): r for r in plan.get("holdout_case_rows", [])}


def emission_map(candidate: dict[str, Any], fail: list[str]) -> dict[str, str]:
    e = candidate.get("native_q8_target_cvec_emission")
    if not isinstance(e, dict) or not is_sha(e.get("emission_receipt_sha256")):
        fail.append("TARGET_CVEC_EMISSION_RECEIPT_REQUIRED"); return {}
    out = {}
    rows = e.get("target_cvecs") if isinstance(e.get("target_cvecs"), dict) else {}
    for t in TARGETS:
        row = rows.get(t) if isinstance(rows.get(t), dict) else {}
        d = row.get("cvec_sha256")
        if not is_sha(d): fail.append(f"TARGET_CVEC_SHA_REQUIRED:{t}")
        else: out[t] = d
    return out


def bind_row(row: dict[str, Any], frozen: dict[str, Any], prefix: str, fail: list[str]) -> None:
    for f in ("case_id", "prompt_sha256", "scenario_family_sha256", "semantic_target", "output_code_identity"):
        if row.get(f) != frozen.get(f): fail.append(f"{prefix}_FROZEN_FIELD_MISMATCH:{f}")


def projection(obs: dict[str, Any], rank: int, prefix: str, fail: list[str]) -> tuple[list[float] | None, float | None]:
    p = obs.get("downstream_projection"); b = obs.get("behavior_target_margin")
    if not isinstance(p, list) or len(p) != rank or not all(finite(x) for x in p): fail.append(f"{prefix}_PROJECTION_INVALID"); p = None
    if not finite(b): fail.append(f"{prefix}_BEHAVIOR_MARGIN_INVALID"); b = None
    if not is_sha(obs.get("runtime_receipt_sha256")): fail.append(f"{prefix}_RUNTIME_RECEIPT_REQUIRED")
    return ([float(x) for x in p] if p is not None else None, float(b) if b is not None else None)


def score(p: list[float], c: list[float]) -> float:
    return -sum((a - b) ** 2 for a, b in zip(p, c))


def abstract_gate(candidate: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    fail = plan_invariants(plan)
    e = candidate.get("abstract_state_evidence")
    if not isinstance(e, dict) or e.get("schema") != ABSTRACT_SCHEMA:
        return {"pass": False, "failures": sorted(set(fail + ["ABSTRACT_STATE_EVIDENCE_REQUIRED"]))}
    if e.get("case_plan_sha256") != EXPECTED_PLAN_SHA: fail.append("ABSTRACT_PLAN_SHA_BINDING_REQUIRED")
    if e.get("case_plan_source_sha256") != EXPECTED_PLAN_SOURCE_SHA: fail.append("ABSTRACT_PLAN_SOURCE_SHA_BINDING_REQUIRED")
    geometry = candidate.get("native_carrier_geometry") if isinstance(candidate.get("native_carrier_geometry"), dict) else {}
    rank_e = candidate.get("semantic_simplex_rank") if isinstance(candidate.get("semantic_simplex_rank"), dict) else {}
    if not is_sha(e.get("native_geometry_receipt_sha256")) or e.get("native_geometry_receipt_sha256") != geometry.get("geometry_receipt_sha256"):
        fail.append("ABSTRACT_NATIVE_GEOMETRY_BINDING_REQUIRED")
    if not is_sha(e.get("rank_analysis_receipt_sha256")) or e.get("rank_analysis_receipt_sha256") != rank_e.get("analysis_receipt_sha256"):
        fail.append("ABSTRACT_RANK_BINDING_REQUIRED")
    if not is_sha(e.get("calibration_centroid_receipt_sha256")): fail.append("CALIBRATION_CENTROID_RECEIPT_REQUIRED")
    cvec = emission_map(candidate, fail)
    rank = e.get("representation_rank")
    if rank not in (1, 2): fail.append("REPRESENTATION_RANK_1_OR_2_REQUIRED"); rank = 1
    cent = e.get("target_centroids") if isinstance(e.get("target_centroids"), dict) else {}
    centroids: dict[str, list[float]] = {}
    for t in TARGETS:
        v = cent.get(t)
        if not isinstance(v, list) or len(v) != rank or not all(finite(x) for x in v): fail.append(f"CENTROID_INVALID:{t}")
        else: centroids[t] = [float(x) for x in v]
    if len(centroids) == 3 and any(math.dist(centroids[a], centroids[b]) <= 1e-9 for i,a in enumerate(TARGETS) for b in TARGETS[i+1:]):
        fail.append("CENTROIDS_MUST_BE_DISTINCT")
    frozen = frozen_holdout(plan); rows = e.get("holdout_runtime_rows")
    if not isinstance(rows, list): rows = []; fail.append("ABSTRACT_RUNTIME_ROWS_REQUIRED")
    seen = set(); fi: dict[str,list[float]] = defaultdict(list); fb: dict[str,list[float]] = defaultdict(list); fg: dict[str,list[float]] = defaultdict(list)
    for i,row in enumerate(rows):
        if not isinstance(row, dict): fail.append(f"ABSTRACT_ROW_{i}_INVALID"); continue
        cid = str(row.get("case_id") or "")
        if cid not in frozen or cid in seen: fail.append(f"ABSTRACT_ROW_CASE_INVALID:{cid}"); continue
        seen.add(cid); fr = frozen[cid]; bind_row(row, fr, f"ABSTRACT_{cid}", fail)
        arms = row.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ABSTRACT_ARMS): fail.append(f"ABSTRACT_ARM_SET_INVALID:{cid}"); continue
        parsed = {}
        for arm in ABSTRACT_ARMS:
            o = arms[arm]; p,b = projection(o, rank, f"ABSTRACT_{cid}_{arm}", fail)
            expected = None if arm == "BASELINE" else cvec.get(arm.removeprefix("CVEC_"))
            if o.get("cvec_sha256") not in ((None, "") if expected is None else (expected,)): fail.append(f"ABSTRACT_CVEC_IDENTITY_MISMATCH:{cid}:{arm}")
            if p is not None and b is not None: parsed[arm] = (p,b)
        t = fr["semantic_target"]; fam = fr["scenario_family_sha256"]; matched = f"CVEC_{t}"; others = [f"CVEC_{x}" for x in TARGETS if x != t]
        if matched in parsed and all(x in parsed for x in others) and "BASELINE" in parsed and t in centroids:
            m = score(parsed[matched][0], centroids[t]); om = sum(score(parsed[x][0], centroids[t]) for x in others)/2
            di = m - om
            db = parsed[matched][1] - sum(parsed[x][1] for x in others)/2
            dg = parsed[matched][1] - parsed["BASELINE"][1]
            fi[fam].append(di); fb[fam].append(db); fg[fam].append(dg)
            # No family-average rescue: every frozen holdout cell must itself be
            # internally target-selective, behaviorally target-selective, and beat baseline.
            if di <= 0 or db <= 0 or dg <= 0:
                fail.append(f"ABSTRACT_CASE_NOT_TARGET_SELECTIVE:{cid}")
    if seen != set(frozen): fail.append("ABSTRACT_RUNTIME_CASE_UNIVERSE_MISMATCH")
    summaries = {}
    for fam in sorted({r["scenario_family_sha256"] for r in frozen.values()}):
        if not (len(fi[fam]) == len(fb[fam]) == len(fg[fam]) == 3): fail.append(f"ABSTRACT_FAMILY_INCOMPLETE:{fam}"); continue
        vals = (sum(fi[fam])/3, sum(fb[fam])/3, sum(fg[fam])/3); summaries[fam] = vals
        if any(x <= 0 for x in vals): fail.append(f"ABSTRACT_FAMILY_NOT_TARGET_SELECTIVE:{fam}")
    if len(summaries) != 6: fail.append("ABSTRACT_SIX_COMPLETE_FAMILIES_REQUIRED")
    core = {k:v for k,v in e.items() if k != "evidence_receipt_sha256"}
    if e.get("evidence_receipt_sha256") != sha(core): fail.append("ABSTRACT_EVIDENCE_RECEIPT_MISMATCH")
    return {"pass": not fail, "failures": sorted(set(fail)), "family_selectivity": summaries, "exact_two_sided_sign_p_if_all_six_positive": 0.03125}


def temporal_gate(candidate: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    fail: list[str] = []; e = candidate.get("temporal_scope_evidence")
    if not isinstance(e, dict) or e.get("schema") != TEMPORAL_SCHEMA: return {"pass":False,"failures":["TEMPORAL_SCOPE_EVIDENCE_REQUIRED"]}
    if e.get("native_api") != "llama_set_adapter_cvec": fail.append("NATIVE_CVEC_API_REQUIRED")
    for key in ("same_vector_layer_gain_across_scope_arms","prefix_kv_computed_before_last_token_arm","cvec_clear_uses_null_data_api"):
        if e.get(key) is not True: fail.append(f"TEMPORAL_ATTESTATION_REQUIRED:{key}")
    if not is_sha(e.get("harness_source_sha256")): fail.append("TEMPORAL_HARNESS_SHA_REQUIRED")
    cvec = emission_map(candidate, fail); declared = e.get("target_cvec_sha256")
    if declared != cvec: fail.append("TEMPORAL_TARGET_CVEC_MAP_MUST_MATCH_EMISSION")
    th = e.get("preregistered_thresholds") if isinstance(e.get("preregistered_thresholds"),dict) else {}
    min_rec, max_dev, max_pre, max_batch = (th.get("min_last_token_recovery_fraction"), th.get("max_last_token_recovery_deviation"), th.get("max_prefix_only_fraction"), th.get("max_batch_partition_fraction"))
    if not finite(min_rec) or not 0.75 <= float(min_rec) <= 1: fail.append("MIN_RECOVERY_THRESHOLD_INVALID")
    if not finite(max_dev) or not 0 <= float(max_dev) <= .25: fail.append("MAX_RECOVERY_DEVIATION_INVALID")
    if not finite(max_pre) or not 0 <= float(max_pre) <= .25: fail.append("MAX_PREFIX_THRESHOLD_INVALID")
    if not finite(max_batch) or not 0 <= float(max_batch) <= .10: fail.append("MAX_BATCH_THRESHOLD_INVALID")
    min_rec=float(min_rec or .75); max_dev=float(max_dev or .25); max_pre=float(max_pre or .25); max_batch=float(max_batch or .10)
    a = candidate.get("abstract_state_evidence") if isinstance(candidate.get("abstract_state_evidence"),dict) else {}; rank=a.get("representation_rank"); cent=a.get("target_centroids") if isinstance(a.get("target_centroids"),dict) else {}
    if rank not in (1,2): rank=1; fail.append("TEMPORAL_ABSTRACT_RANK_REQUIRED")
    frozen=frozen_holdout(plan); rows=e.get("rows") if isinstance(e.get("rows"),list) else []; seen=set(); famvals:dict[str,list[tuple[dict[str,float],dict[str,float]]]]=defaultdict(list)
    def metrics(v:dict[str,float]) -> dict[str,float] | None:
        if set(v) != set(TEMPORAL_ARMS): return None
        full=v["BROADCAST_SPLIT"]-v["BASELINE_SPLIT"]
        if full <= 1e-12: return {"full":full,"rec":-math.inf,"pre":math.inf,"base_batch":math.inf,"broad_batch":math.inf}
        return {"full":full,"rec":(v["LAST_TOKEN_ONLY"]-v["BASELINE_SPLIT"])/full,"pre":abs(v["PREFIX_ONLY"]-v["BASELINE_SPLIT"])/full,"base_batch":abs(v["BASELINE_SPLIT"]-v["BASELINE_SINGLE"])/full,"broad_batch":abs(v["BROADCAST_SPLIT"]-v["BROADCAST_SINGLE"])/full}
    for i,row in enumerate(rows):
        if not isinstance(row,dict): fail.append(f"TEMPORAL_ROW_{i}_INVALID"); continue
        cid=str(row.get("case_id") or "")
        if cid not in frozen or cid in seen: fail.append(f"TEMPORAL_CASE_INVALID:{cid}"); continue
        seen.add(cid); fr=frozen[cid]; bind_row(row,fr,f"TEMPORAL_{cid}",fail); arms=row.get("arms")
        if not isinstance(arms,dict) or set(arms)!=set(TEMPORAL_ARMS): fail.append(f"TEMPORAL_ARM_SET_INVALID:{cid}"); continue
        bv={}; iv={}; t=fr["semantic_target"]; center=cent.get(t)
        if not isinstance(center,list) or len(center)!=rank or not all(finite(x) for x in center): fail.append(f"TEMPORAL_CENTROID_INVALID:{t}"); continue
        center=[float(x) for x in center]
        for arm in TEMPORAL_ARMS:
            o=arms[arm]; p,b=projection(o,rank,f"TEMPORAL_{cid}_{arm}",fail); expected=None if arm.startswith("BASELINE") else cvec.get(t)
            if o.get("cvec_sha256") not in ((None,"") if expected is None else (expected,)): fail.append(f"TEMPORAL_CVEC_IDENTITY_MISMATCH:{cid}:{arm}")
            if b is not None: bv[arm]=b
            if p is not None: iv[arm]=score(p,center)
        bm,im=metrics(bv),metrics(iv)
        if bm is not None and im is not None:
            # No averaging loophole: each case must satisfy the frozen temporal mediation
            # limits for both behavioral and internal-state readouts.
            for name,m in (("behavior",bm),("internal",im)):
                if m["full"] <= 0:
                    fail.append(f"TEMPORAL_CASE_BROADCAST_EFFECT_REQUIRED:{cid}:{name}")
                if m["rec"] < min_rec or abs(m["rec"] - 1) > max_dev:
                    fail.append(f"TEMPORAL_CASE_LAST_TOKEN_EQUIVALENCE_FAIL:{cid}:{name}")
                if m["pre"] > max_pre:
                    fail.append(f"TEMPORAL_CASE_PREFIX_EFFECT_TOO_LARGE:{cid}:{name}")
                if m["base_batch"] > max_batch or m["broad_batch"] > max_batch:
                    fail.append(f"TEMPORAL_CASE_BATCH_DRIFT_TOO_LARGE:{cid}:{name}")
            famvals[fr["scenario_family_sha256"]].append((bm,im))
    if seen != set(frozen): fail.append("TEMPORAL_CASE_UNIVERSE_MISMATCH")
    summaries={}
    for fam in sorted({r["scenario_family_sha256"] for r in frozen.values()}):
        xs=famvals[fam]
        if len(xs)!=3: fail.append(f"TEMPORAL_FAMILY_INCOMPLETE:{fam}"); continue
        b={k:sum(pair[0][k] for pair in xs)/3 for k in ("full","rec","pre","base_batch","broad_batch")}; q={k:sum(pair[1][k] for pair in xs)/3 for k in ("full","rec","pre","base_batch","broad_batch")}
        summaries[fam]={"behavior":b,"internal":q}
        for name,m in (("behavior",b),("internal",q)):
            if m["full"]<=0: fail.append(f"TEMPORAL_BROADCAST_EFFECT_REQUIRED:{fam}:{name}")
            if m["rec"]<min_rec or abs(m["rec"]-1)>max_dev: fail.append(f"TEMPORAL_LAST_TOKEN_EQUIVALENCE_FAIL:{fam}:{name}")
            if m["pre"]>max_pre: fail.append(f"TEMPORAL_PREFIX_EFFECT_TOO_LARGE:{fam}:{name}")
            if m["base_batch"]>max_batch or m["broad_batch"]>max_batch: fail.append(f"TEMPORAL_BATCH_DRIFT_TOO_LARGE:{fam}:{name}")
    if len(summaries)!=6: fail.append("TEMPORAL_SIX_COMPLETE_FAMILIES_REQUIRED")
    core={k:v for k,v in e.items() if k!="evidence_receipt_sha256"}
    if e.get("evidence_receipt_sha256")!=sha(core): fail.append("TEMPORAL_EVIDENCE_RECEIPT_MISMATCH")
    return {"pass":not fail,"failures":sorted(set(fail)),"family_summary":summaries}


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    plan,pfail=source_plan(); base=v11.adjudicate(candidate); a=abstract_gate(candidate,plan) if plan else {"pass":False,"failures":pfail}; t=temporal_gate(candidate,plan) if plan else {"pass":False,"failures":pfail}
    hard=not pfail and a.get("pass") is True and t.get("pass") is True; upstream=base.get("abstract_native_semantic_jspace_candidate") is True; promoted=bool(upstream and hard)
    failures=sorted(set(list(base.get("v11_failures",[]))+pfail+list(a.get("failures",[]))+list(t.get("failures",[]))))
    return {**base,"schema":SCHEMA,"source_frozen_abstract_state_evidence_pass":a.get("pass") is True,"native_temporal_scope_mediation_pass":t.get("pass") is True,"source_frozen_abstract_native_semantic_jspace_candidate":promoted,"native_last_token_mediated_scope_equivalence_candidate":promoted,"strict_micro_mechanistic_identity_candidate":False,"v12_failures":failures,"v12_abstract_metrics":a,"v12_temporal_metrics":t,"canonical_credit_minted":False,"canonical_semantics_promotion":False,"jspace_model_runtime_credit":False,"whole_hcu_credit":False,"whole_entityos_hcu_credit":False,"training_credit":False,"evidence_boundary":"v12 requires merged v11 plus exact source-frozen six-family row-level abstract-state and native temporal-scope evidence. LAST_TOKEN_ONLY must lie inside the preregistered broadcast-effect equivalence band, PREFIX_ONLY and batch partition must remain bounded, and matched target cvecs must be internally and behaviorally selective in all six lexically disjoint holdout families. Strict microscopic identity is never inferred; adjudication mints no runtime/canonical/system/training/effect credit."}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("candidate",type=Path); args=ap.parse_args()
    try: obj=json.loads(args.candidate.read_text())
    except Exception as exc: out={"schema":SCHEMA,"source_frozen_abstract_native_semantic_jspace_candidate":False,"v12_failures":[f"CANDIDATE_INVALID:{type(exc).__name__}"]}
    else: out=adjudicate(obj if isinstance(obj,dict) else {})
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__": raise SystemExit(main())
