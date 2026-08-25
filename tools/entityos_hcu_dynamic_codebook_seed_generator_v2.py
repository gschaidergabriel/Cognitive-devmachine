#!/usr/bin/env python3
"""Deterministic Trigger-2 pre-materialization generator for dynamic codebook binding.

The output deliberately contains accepted-atom INDEX placeholders rather than real ABI
atom strings. Rows remain model_consumable=false until a separately verified materializer
binds the exact 46-atom ABI alphabet and exact measured tokenizer identity.

This generator trains the *binding problem shape* only:
semantic situation -> episode-local codebook -> selected opaque output symbol.
It does not mint J-Space causal labels, canonical truth, effect authority or training credit.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
PERMS = list(itertools.permutations(range(3)))
MATERIALIZATION_STATUS = "AWAITING_VERIFIED_ABI_ATOM_TABLE_AND_EXACT_TOKENIZER_CHECK"

TEMPLATES = [
    {
        "id":"T1_RULE_STATUS","split":"TRAIN","family":"DYNBIND_T1_RULE_STATUS_F01",
        "prov":"trigger2-v2-dynbind-t1-rule-status","atoms":[0,1,2],
        "cases":{
            "ALLOW":("every mandatory condition is satisfied and no blocker is present",["mandatory","condition","satisfied","blocker"]),
            "DENY":("a mandatory condition is violated and a blocker is present",["mandatory","condition","violated","blocker"]),
            "ABSTAIN":("a required condition cannot be determined from the available evidence",["required","condition","determined","evidence"]),
        },
    },
    {
        "id":"T2_AUDIT_OUTCOME","split":"TRAIN","family":"DYNBIND_T2_AUDIT_OUTCOME_F01",
        "prov":"trigger2-v2-dynbind-t2-audit-outcome","atoms":[3,4,5],
        "cases":{
            "ALLOW":("the audit found full compliance with all active requirements",["audit","compliance","requirements"]),
            "DENY":("the audit found a disqualifying breach of an active requirement",["audit","disqualifying","breach","requirement"]),
            "ABSTAIN":("the audit lacks a required observation needed for a decision",["audit","observation","decision"]),
        },
    },
    {
        "id":"T3_GATE_STATE","split":"TRAIN","family":"DYNBIND_T3_GATE_STATE_F01",
        "prov":"trigger2-v2-dynbind-t3-gate-state","atoms":[6,7,8],
        "cases":{
            "ALLOW":("the gate has all needed inputs and none of its stop conditions fire",["gate","inputs","stop","conditions"]),
            "DENY":("the gate has a confirmed stop condition that blocks passage",["gate","stop","condition","passage"]),
            "ABSTAIN":("the gate is missing an input needed to determine whether passage is justified",["gate","input","passage","determine"]),
        },
    },
    {
        "id":"T4_EVIDENCE_DECISION","split":"TRAIN","family":"DYNBIND_T4_EVIDENCE_DECISION_F01",
        "prov":"trigger2-v2-dynbind-t4-evidence-decision","atoms":[9,10,11],
        "cases":{
            "ALLOW":("the record supports proceeding under the stated constraints with no unresolved blocker",["record","proceeding","constraints","blocker"]),
            "DENY":("the record establishes a constraint failure that requires stopping",["record","constraint","failure","stopping"]),
            "ABSTAIN":("the record leaves a decision critical premise unresolved",["record","decision","premise","unresolved"]),
        },
    },
    {
        "id":"T5_CALIBRATION_DOSSIER","split":"VALIDATION","family":"DYNBIND_T5_CALIBRATION_DOSSIER_F01",
        "prov":"trigger2-v2-dynbind-t5-calibration-dossier","atoms":[30,31,32],
        "cases":{
            "ALLOW":("the dossier conforms to the charter and is obstacle free",["dossier","conforms","charter","obstacle"]),
            "DENY":("the dossier contains an exception that conflicts with the charter",["dossier","exception","conflicts","charter"]),
            "ABSTAIN":("the dossier lacks a decisive signal so the verdict remains pending",["dossier","decisive","signal","verdict","pending"]),
        },
    },
    {
        "id":"T6_FROZEN_UNSEEN_INSPECTOR","split":"HOLDOUT","family":"DYNBIND_T6_FROZEN_UNSEEN_INSPECTOR_F01",
        "prov":"trigger2-v2-dynbind-t6-frozen-unseen-inspector","atoms":[38,39,40],
        "cases":{
            "ALLOW":("the examiner cleared every prerequisite and found no veto",["examiner","cleared","prerequisite","veto"]),
            "DENY":("the examiner confirmed a fatal veto",["examiner","confirmed","fatal","veto"]),
            "ABSTAIN":("the examiner reports that a key prerequisite remains unknown",["examiner","key","prerequisite","unknown"]),
        },
    },
]

def generate_rows():
    rows = []
    for template in TEMPLATES:
        for pidx, perm in enumerate(PERMS):
            mapping = {CLASSES[ci]: template["atoms"][perm[ci]] for ci in range(3)}
            entry_perm = PERMS[(pidx + 2) % 6]
            entry_order = [CLASSES[i] for i in entry_perm]
            codebook_lines = [f"{c}=>{{{{ABI:{mapping[c]:02d}}}}}" for c in entry_order]
            codebook = "[CODEBOOK]\n" + "\n".join(codebook_lines) + "\n[/CODEBOOK]"
            for target_class in CLASSES:
                case_text, semantic_lexemes = template["cases"][target_class]
                semantic_lexemes = sorted(set(semantic_lexemes))
                lex_hash = hashlib.sha256("\n".join(semantic_lexemes).encode("utf-8")).hexdigest()
                prompt = (
                    f"{codebook}\n"
                    f"[CASE]\n{case_text}.\n[/CASE]\n"
                    "[QUERY]\nEmit exactly one code from the codebook.\n[/QUERY]"
                )
                target_index = mapping[target_class]
                rows.append({
                    "schema":"ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
                    "evidence_class":"METHOD_ONLY",
                    "reality_level":"R2",
                    "family_id":template["family"],
                    "provenance_ancestry_id":template["prov"],
                    "canonical_truth_allowed":False,
                    "direct_effect_authority":False,
                    "fact_status":"NOT_APPLICABLE",
                    "target_type":"DYNAMIC_CODEBOOK_BINDING_METHOD",
                    "split":template["split"],
                    "split_unit":"CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                    "selected_using_holdout":False,
                    "model_consumable":False,
                    "materialization_status":MATERIALIZATION_STATUS,
                    "template_id":template["id"],
                    "semantic_lexical_family_id":template["id"]+"_LEX",
                    "semantic_bearing_lexemes":semantic_lexemes,
                    "semantic_lexeme_inventory_sha256":lex_hash,
                    "s3_permutation_id":f"S3_{pidx}",
                    "mapping_class_to_accepted_atom_index":mapping,
                    "codebook_entry_order":entry_order,
                    "target_class_hidden_metadata":target_class,
                    "target_accepted_atom_index":target_index,
                    "prompt":prompt,
                    "target":f"{{{{ABI:{target_index:02d}}}}}",
                })
    return rows

def serialize(rows):
    return "\n".join(json.dumps(r, ensure_ascii=False, separators=(",",":")) for r in rows) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ns = ap.parse_args()
    rows = generate_rows()
    Path(ns.output).write_text(serialize(rows), encoding="utf-8")
    print(json.dumps({
        "schema":"ENTITYOS_HCU_DYNAMIC_CODEBOOK_SEED_GENERATOR_RESULT/v2",
        "rows":len(rows),
        "train":sum(r["split"]=="TRAIN" for r in rows),
        "validation":sum(r["split"]=="VALIDATION" for r in rows),
        "holdout":sum(r["split"]=="HOLDOUT" for r in rows),
        "model_consumable":False,
        "output_sha256":hashlib.sha256(serialize(rows).encode("utf-8")).hexdigest(),
    }, sort_keys=True))

if __name__ == "__main__":
    main()
