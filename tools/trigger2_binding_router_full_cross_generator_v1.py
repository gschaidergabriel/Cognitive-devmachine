#!/usr/bin/env python3
"""Trigger-2 dynamic binding factorial generator v4.

METHOD_ONLY / CANDIDATE_ONLY.

v4 is a separately versioned successor to the quarantined v3 schedule. Its key
change is structural: every model-visible codebook display order is fully
crossed with semantic state, query polarity and S3 mapping. Display order is
never derived from target-generating factors.

The generator remains non-training-admissible. It can render placeholders or
ABI-bound symbol candidates, but all rows stay training_eligible=False until
separate tokenizer, family-split, evidence-admission and model/runtime gates
promote a later artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "ENTITYOS_HCU_BINDING_FACTORIAL_CANDIDATE/v4"
AUDIT_SCHEMA = "CLAY_TRIGGER2_BINDING_FACTORIAL_V4_AUDIT/v1"
ANCESTRY = "trigger2-20260826-dynamic-binding-factorial-v4-full-cross"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SLOTS = {"ALLOW": "K0", "DENY": "K1", "ABSTAIN": "K2"}
FLIP = {"ALLOW": "DENY", "DENY": "ALLOW", "ABSTAIN": "ABSTAIN"}
POLARITIES = ("DIRECT", "INVERTED")

TRAIN_TEMPLATES = {
    "T1_GATE": {
        "ALLOW": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match=1.",
        "DENY": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match=0.",
        "ABSTAIN": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match is unobserved.",
        "direct": "Does the evidence support opening the gate?",
        "inverted": "Does the evidence support keeping the gate closed?",
    },
    "T2_LEDGER": {
        "ALLOW": "Release requires every mandatory clause confirmed. The ledger has all mandatory clauses confirmed, contradictions=0, unresolved=0.",
        "DENY": "Release requires every mandatory clause confirmed. The ledger has one mandatory clause falsified, contradictions=1, unresolved=0.",
        "ABSTAIN": "Release requires every mandatory clause confirmed. The ledger lacks one mandatory observation, contradictions=0, unresolved=1.",
        "direct": "Does the evidence support release?",
        "inverted": "Does the evidence support withholding release?",
    },
    "T3_NESTED": {
        "ALLOW": "Authorization requires x=1 and y=1. State={x:1,y:1,faults:[],unknown:[]}.",
        "DENY": "Authorization requires x=1 and y=1. State={x:1,y:0,faults:[y],unknown:[]}.",
        "ABSTAIN": "Authorization requires x=1 and y=1. State={x:1,y:null,faults:[],unknown:[y]}.",
        "direct": "Does the state support authorization?",
        "inverted": "Does the state support rejecting authorization?",
    },
    "T4_FIRST_PERSON": {
        "ALLOW": "I may enter only if my slot is booked and my badge is active. My slot is booked and my badge is active.",
        "DENY": "I may enter only if my slot is booked and my badge is active. My slot is booked and my badge is inactive.",
        "ABSTAIN": "I may enter only if my slot is booked and my badge is active. My slot is booked; my badge status has not been checked.",
        "direct": "Does the evidence support my entry?",
        "inverted": "Does the evidence support refusing my entry?",
    },
}
OOD_TEMPLATES = {
    "T5_DIALOGUE": {
        "ALLOW": "Witness A confirms criterion p. Witness B confirms criterion q. No discrepancy is recorded.",
        "DENY": "Witness A confirms criterion p. Witness B contradicts criterion q. One discrepancy is recorded.",
        "ABSTAIN": "Witness A confirms criterion p. No observation exists for criterion q. The record is incomplete.",
        "direct": "Does this support the requested action?",
        "inverted": "Does this support blocking the requested action?",
    },
    "T6_CLAYLIKE": {
        "ALLOW": "obs{req.a=1;req.b=1;viol=0;unk=0}",
        "DENY": "obs{req.a=1;req.b=0;viol=1;unk=0}",
        "ABSTAIN": "obs{req.a=1;req.b=?;viol=0;unk=1}",
        "direct": "judge{claim=execute}",
        "inverted": "judge{claim=block}",
    },
}
BLUEPRINT_POOLS = {
    "TRAIN_SYMBOLS": ("<ABI_TRAIN_A>", "<ABI_TRAIN_B>", "<ABI_TRAIN_C>"),
    "HOLDOUT_SYMBOLS": ("<ABI_HOLDOUT_A>", "<ABI_HOLDOUT_B>", "<ABI_HOLDOUT_C>"),
}

def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _digest(obj):
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()

def load_atom_manifest(path):
    if path is None:
        return dict(BLUEPRINT_POOLS), {"mode":"BLUEPRINT_PLACEHOLDER","training_eligible":False,"reason":"EXACT_ABI_ATOM_MANIFEST_NOT_SUPPLIED"}
    raw = path.read_bytes(); doc = json.loads(raw)
    if doc.get("abi_manifest_sha256") != ABI_MANIFEST_SHA256:
        raise ValueError("atom manifest ABI hash mismatch")
    if doc.get("single_token_verification") is not True:
        raise ValueError("atom manifest must attest single_token_verification=true")
    parts = doc.get("partitions") or {}; train = tuple(parts.get("TRAIN", ())); holdout = tuple(parts.get("HOLDOUT", ()))
    if len(train) < 3 or len(holdout) < 3: raise ValueError("atom manifest needs >=3 TRAIN and >=3 HOLDOUT atoms")
    if set(train) & set(holdout): raise ValueError("TRAIN/HOLDOUT atom partitions overlap")
    return {"TRAIN_SYMBOLS": tuple(train[:3]), "HOLDOUT_SYMBOLS": tuple(holdout[:3])}, {
        "mode":"ABI_RENDERED_CANDIDATE","training_eligible":False,
        "reason":"FULL_CROSS_PASSED_BUT_TOKEN_POSITION_FAMILY_EVIDENCE_AND_RUNTIME_GATES_STILL_REQUIRED",
        "atom_manifest_file_sha256": hashlib.sha256(raw).hexdigest(), "tokenizer_identity": doc.get("tokenizer_identity")}

def decision_class(base_state, polarity):
    return base_state if polarity == "DIRECT" else FLIP[base_state]

def codebook(mapping, order):
    return " | ".join(f"{c} => {mapping[c]}" for c in order)

def row_common(split, phase, symbol_partition, render):
    return {"schema":SCHEMA,"evidence_class":"METHOD_ONLY","reality_level":"R2","provenance_ancestry_id":ANCESTRY,
        "canonical_truth_allowed":False,"direct_effect_authority":False,"selected_using_holdout":False,"split":split,
        "split_unit":"FAMILY_DISJOINT_DIAGNOSTIC_CELL_CANDIDATE","curriculum_phase":phase,"symbol_partition":symbol_partition,
        "abi_manifest_sha256":ABI_MANIFEST_SHA256,"render_mode":render["mode"],"training_eligible":False,
        "positive_jspace_label":False,"display_order_schedule":"FULL_CROSS_6_ORDERS"}

def p0_rows(pool_name, symbols, split, render):
    slots=("K0","K1","K2")
    for mapping_id, perm in enumerate(itertools.permutations(symbols)):
        slot_map=dict(zip(slots,perm))
        for slot in slots:
            for order_id, order in enumerate(itertools.permutations(slots)):
                r=row_common(split,"P0_ROUTER_ONLY",pool_name,render)
                r.update({"family_id":f"BIND_V4_P0_{pool_name}_{slot}","s3_mapping_id":f"M{mapping_id}","display_order_id":f"O{order_id}",
                    "semantic_slot_model_visible":slot,"realized_mapping":slot_map,"codebook_entry_order":list(order),
                    "prompt":f"ROUTE: {' | '.join(f'{k} => {slot_map[k]}' for k in order)}\nSLOT: {slot}\nReturn exactly the bound code token.",
                    "target":slot_map[slot],"counterfactual_group_id":f"P0|{pool_name}|{slot}|ALL_S3_ALL_ORDER"})
                yield r

def p1_rows(template_partition, templates, pool_name, symbols, split, render):
    for tid,spec in templates.items():
        for polarity in POLARITIES:
            for mapping_id,perm in enumerate(itertools.permutations(symbols)):
                mapping=dict(zip(CLASSES,perm))
                for order_id,order in enumerate(itertools.permutations(CLASSES)):
                    for base in CLASSES:
                        decided=decision_class(base,polarity)
                        r=row_common(split,"P1_SEMANTIC_TO_ROUTER",pool_name,render)
                        r.update({"family_id":f"BIND_V4_{template_partition}_{tid}_{polarity}","template_partition":template_partition,"template_id":tid,
                            "base_semantic_state_metadata_only":base,"query_polarity":polarity,"decision_class_metadata_only":decided,
                            "semantic_slot_metadata_only":SLOTS[decided],"s3_mapping_id":f"M{mapping_id}","display_order_id":f"O{order_id}",
                            "realized_mapping":mapping,"codebook_entry_order":list(order),
                            "prompt":f"CODEBOOK: {codebook(mapping,order)}\nSCENE: {spec[base]}\nQUERY: {spec['direct' if polarity=='DIRECT' else 'inverted']}\nReturn exactly one code token.",
                            "semantic_ablated_prompt":f"CODEBOOK: {codebook(mapping,order)}\nSCENE: <SEMANTIC_EVIDENCE_MASKED>\nQUERY: {spec['direct' if polarity=='DIRECT' else 'inverted']}\nReturn exactly one code token.",
                            "target":mapping[decided],
                            "counterfactual_group_id":f"P1|{template_partition}|{tid}|{pool_name}|{polarity}|M{mapping_id}|O{order_id}|SEMANTIC_STATES",
                            "display_cross_group_id":f"P1|{template_partition}|{tid}|{pool_name}|{base}|{polarity}|M{mapping_id}|ALL_ORDER"})
                        yield r

def generate(pools, render):
    rows=[]
    rows += list(p0_rows("TRAIN_SYMBOLS",pools["TRAIN_SYMBOLS"],"TRAIN",render))
    rows += list(p0_rows("HOLDOUT_SYMBOLS",pools["HOLDOUT_SYMBOLS"],"DIAG_SYMBOL_OOD",render))
    rows += list(p1_rows("TRAIN_TEMPLATE",TRAIN_TEMPLATES,"TRAIN_SYMBOLS",pools["TRAIN_SYMBOLS"],"TRAIN",render))
    rows += list(p1_rows("TRAIN_TEMPLATE",TRAIN_TEMPLATES,"HOLDOUT_SYMBOLS",pools["HOLDOUT_SYMBOLS"],"DIAG_SYMBOL_OOD",render))
    rows += list(p1_rows("OOD_TEMPLATE",OOD_TEMPLATES,"TRAIN_SYMBOLS",pools["TRAIN_SYMBOLS"],"DIAG_TEMPLATE_OOD",render))
    rows += list(p1_rows("OOD_TEMPLATE",OOD_TEMPLATES,"HOLDOUT_SYMBOLS",pools["HOLDOUT_SYMBOLS"],"DIAG_JOINT_OOD",render))
    return rows

def _conditional_mi(groups):
    # Measure leakage of the semantic target class, not opaque token identity.
    # Token alphabets are intentionally disjoint across TRAIN/HOLDOUT partitions,
    # so global token MI would mostly measure the explicit split/pool identity.
    all_rows=[r for members in groups.values() for r in members]; total=len(all_rows); y_counts=Counter(r["decision_class_metadata_only"] for r in all_rows)
    p_y={y:n/total for y,n in y_counts.items()}; mi=0.0; correct=0
    for members in groups.values():
        n_g=len(members); counts=Counter(r["decision_class_metadata_only"] for r in members); correct += max(counts.values()); p_g=n_g/total
        for y,n in counts.items():
            p_yg=n/n_g
            if p_yg>0 and p_y[y]>0: mi += p_g*p_yg*math.log2(p_yg/p_y[y])
    return mi, correct/total

def audit(rows,pools,render):
    failures=[]; expected={"TRAIN":972,"DIAG_SYMBOL_OOD":972,"DIAG_TEMPLATE_OOD":432,"DIAG_JOINT_OOD":432}; split_counts=Counter(r["split"] for r in rows)
    if dict(split_counts)!=expected: failures.append(f"SPLIT_COUNTS:{dict(split_counts)}!=EXPECTED:{expected}")
    if any(r.get("training_eligible") is not False for r in rows): failures.append("TRAINING_ELIGIBLE_MUST_REMAIN_FALSE")
    if set(pools["TRAIN_SYMBOLS"]) & set(pools["HOLDOUT_SYMBOLS"]): failures.append("SYMBOL_PARTITION_OVERLAP")
    p1=[r for r in rows if r["curriculum_phase"]=="P1_SEMANTIC_TO_ROUTER"]
    cross=defaultdict(list)
    for r in p1: cross[r["display_cross_group_id"]].append(r)
    for gid,members in cross.items():
        orders={tuple(r["codebook_entry_order"]) for r in members}
        if len(members)!=6 or len(orders)!=6: failures.append(f"DISPLAY_ORDER_NOT_FULLY_CROSSED:{gid}:{len(members)}:{len(orders)}")
    nuisance=defaultdict(list)
    for r in p1:
        sig=_digest({"split":r["split"],"symbol_partition":r["symbol_partition"],"template_partition":r["template_partition"],"template_id":r["template_id"],
            "query_polarity":r["query_polarity"],"realized_mapping":r["realized_mapping"],"codebook_entry_order":r["codebook_entry_order"],"semantic_ablated_prompt":r["semantic_ablated_prompt"]})
        nuisance[sig].append(r)
    single=0
    for sig,members in nuisance.items():
        targets={r["target"] for r in members}; slots={r["semantic_slot_metadata_only"] for r in members}; bases={r["base_semantic_state_metadata_only"] for r in members}
        if len(targets)==1: single += 1
        if len(members)!=3 or len(targets)!=3 or slots!={"K0","K1","K2"} or bases!=set(CLASSES):
            failures.append(f"NUISANCE_SIGNATURE_NOT_TARGET_SLOT_COMPLETE:{sig}:n={len(members)} targets={len(targets)} slots={sorted(slots)} bases={sorted(bases)}")
    mi,lookup=_conditional_mi(nuisance)
    if abs(mi)>1e-12: failures.append(f"CONDITIONAL_MI_TARGET_CLASS_NONZERO:{mi}")
    if abs(lookup-(1/3))>1e-12: failures.append(f"NUISANCE_LOOKUP_NOT_CHANCE:{lookup}")
    for i,r in enumerate(rows):
        key=r["semantic_slot_model_visible"] if r["curriculum_phase"]=="P0_ROUTER_ONLY" else r["decision_class_metadata_only"]
        if r["realized_mapping"].get(key)!=r["target"]: failures.append(f"TARGET_NOT_FROM_EPISODE_MAPPING:{i}")
    cf=defaultdict(list)
    for r in p1: cf[r["counterfactual_group_id"]].append(r)
    for gid,members in cf.items():
        if len(members)!=3 or len({r["target"] for r in members})!=3: failures.append(f"SEMANTIC_COUNTERFACTUAL_GROUP_INVALID:{gid}")
    return {"schema":AUDIT_SCHEMA,"pass":not failures,"failures":failures,"rows":len(rows),"split_counts":dict(split_counts),"p1_rows":len(p1),
        "display_cross_groups":len(cross),"nuisance_signatures":len(nuisance),"nuisance_signature_single_target_groups":single,
        "required_targets_per_nuisance_signature":3,"required_slots_per_nuisance_signature":3,"conditional_mi_target_class_bits":mi,
        "nuisance_exact_lookup_accuracy":lookup,"chance_accuracy":1/3,"render":render,
        "credit_boundary":{"accepted_dataset_tokens":0,"training_credit":0,"checkpoint_selection_credit":0,"jspace_model_credit":0,"whole_hcu_runtime_credit":0,"whole_entityos_runtime_credit":0}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--atom-manifest",type=Path); ap.add_argument("--output",type=Path); ap.add_argument("--audit-output",type=Path); ap.add_argument("--audit-only",action="store_true"); args=ap.parse_args()
    pools,render=load_atom_manifest(args.atom_manifest); rows=generate(pools,render); report=audit(rows,pools,render)
    if args.output and not args.audit_only:
        with args.output.open("w",encoding="utf-8") as fh:
            for row in rows: fh.write(_canon(row)+"\n")
    if args.audit_output: args.audit_output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True)); return 0 if report["pass"] else 2
if __name__=="__main__": raise SystemExit(main())
