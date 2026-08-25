#!/usr/bin/env python3
"""Raw-evidence-bound successor promotion gate for Trigger-1 J-Space claims.

v12 composes v11 with a raw-evidence recomputation layer. v11's deconfound/scope
attestation remains necessary, but its declaration/receipt fields are no longer sufficient:
the candidate must also provide raw prompt spans, held-out internal scores, native matched
causal rows and opaque-code logits that independently reconstruct the claimed invariants.

v12 also masks every inherited promotion boolean. No v10/v11 owner/scientific/modular
flag can remain true when the abstract-state raw gate is absent or negative.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v11 as v11
import trigger1_abstract_raw_evidence_gate_v1 as raw_gate

VERDICT_SCHEMA="CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12"
BATCH_SCHEMA="CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v12"


def adjudicate(candidate:dict[str,Any])->dict[str,Any]:
    base=v11.adjudicate(candidate)
    raw=raw_gate.adjudicate(candidate.get("abstract_state_raw_evidence"))
    v11_native=base.get("abstract_native_semantic_jspace_candidate") is True
    raw_ok=raw.get("raw_abstract_state_evidence_pass") is True
    abstract_ok=bool(v11_native and raw_ok)
    scientific=bool(base.get("scientifically_independent_vector_candidate") is True and abstract_ok)
    owner=bool(base.get("owner_trigger1_goal_credit_candidate") is True and abstract_ok)
    modular=bool(base.get("modular_hcu_jspace_control_candidate") is True and abstract_ok)
    cross_scope=bool(abstract_ok and base.get("cross_scope_causal_effect_equivalence_candidate") is True)
    failures=sorted(set(list(base.get("v11_failures",[]))+list(raw.get("failures",[]))))
    return {
        **base,
        "schema":VERDICT_SCHEMA,
        "v11_abstract_native_semantic_jspace_candidate":v11_native,
        "raw_abstract_state_evidence_pass":raw_ok,
        "raw_abstract_state_failures":list(raw.get("failures",[])),
        "raw_abstract_state_metrics":{"readout":raw.get("readout"),"native_causal":raw.get("native_causal"),"opaque_code":raw.get("opaque_code")},
        "abstract_native_semantic_jspace_candidate":abstract_ok,
        "scientifically_independent_vector_candidate":scientific,
        "owner_trigger1_goal_credit_candidate":owner,
        "owner_trigger1_direct_free_api_model_credit_candidate":owner,
        "modular_hcu_jspace_control_candidate":modular,
        "cross_scope_causal_effect_equivalence_candidate":cross_scope,
        "strict_micro_mechanistic_identity_candidate":False,
        "v12_failures":failures,
        "canonical_credit_minted":False,
        "canonical_semantics_promotion":False,
        "jspace_model_runtime_credit":False,
        "whole_hcu_credit":False,
        "whole_entityos_hcu_credit":False,
        "training_credit":False,
        "evidence_boundary":("v12 requires v11 plus raw recomputation of label firewalling, split-disjoint state-varying lexemes, balanced held-out internal decoding, native target/null/shuffled/sign-flip causal effects and opaque-code counterbalance. All inherited promotion booleans are masked by this conjunction. Native ALL_PROMPT_TOKENS abstract-state evidence remains distinct from LAST_TOKEN_ONLY transfer evidence; optional cross-scope effect equivalence never establishes microscopic mechanistic identity. This gate is non-minting."),
    }


def adjudicate_file(path:Path)->dict[str,Any]:
    try: candidate=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        return {"schema":VERDICT_SCHEMA,"abstract_native_semantic_jspace_candidate":False,"scientifically_independent_vector_candidate":False,"owner_trigger1_goal_credit_candidate":False,"modular_hcu_jspace_control_candidate":False,"raw_abstract_state_evidence_pass":False,"canonical_credit_minted":False,"v12_failures":[f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"]}
    if not isinstance(candidate,dict):
        return {"schema":VERDICT_SCHEMA,"abstract_native_semantic_jspace_candidate":False,"scientifically_independent_vector_candidate":False,"owner_trigger1_goal_credit_candidate":False,"modular_hcu_jspace_control_candidate":False,"raw_abstract_state_evidence_pass":False,"canonical_credit_minted":False,"v12_failures":["CANDIDATE_OBJECT_REQUIRED"]}
    result=adjudicate(candidate); result["candidate_path"]=str(path); result["candidate_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest(); return result


def scan_batch(batch_dir:Path)->dict[str,Any]:
    paths=sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json")); verdicts=[adjudicate_file(p) for p in paths]
    positives=[x for x in verdicts if x.get("owner_trigger1_goal_credit_candidate") is True]
    return {"schema":BATCH_SCHEMA,"candidate_files_seen":len(paths),"fully_raw_abstract_positive_files":len(positives),"abstract_native_semantic_jspace_candidate":bool(positives),"owner_trigger1_goal_credit_candidate":bool(positives),"cross_scope_causal_effect_equivalence_candidate":any(x.get("cross_scope_causal_effect_equivalence_candidate") is True for x in positives),"strict_micro_mechanistic_identity_candidate":False,"canonical_credit_minted":False,"verdicts":verdicts}


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); g=ap.add_mutually_exclusive_group(required=True); g.add_argument("--candidate"); g.add_argument("--batch-dir"); a=ap.parse_args(); out=adjudicate_file(Path(a.candidate)) if a.candidate else scan_batch(Path(a.batch_dir)); print(json.dumps(out,sort_keys=True,ensure_ascii=False)); return 0

if __name__=="__main__": raise SystemExit(main())
