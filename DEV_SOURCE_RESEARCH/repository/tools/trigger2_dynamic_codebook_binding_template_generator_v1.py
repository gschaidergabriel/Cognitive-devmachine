#!/usr/bin/env python3
"""Trigger-2 dynamic codebook binding template generator v1.

Generates the 72-row fully crossed METHOD_ONLY template seed:
4 surface families x 6 realized S3 mappings x 3 semantic classes.

ATOM_A/B/C are placeholders. This tool intentionally does not invent ABI atoms.
A later evidence-bound materializer must replace them with three distinct accepted
atoms from the exact ABI inventory and preserve split/provenance constraints.

No output from this tool is accepted dataset/model/J-Space/HCU/EntityOS credit.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

CLASSES=("ALLOW","DENY","ABSTAIN")
ATOMS=("ATOM_A","ATOM_B","ATOM_C")
S3=tuple(permutations(ATOMS))

SCENARIOS={
    "ALLOW":"Facts: p=true; q=true. Rule condition: p AND q.",
    "DENY":"Facts: p=true; q=false. Rule condition: p AND q.",
    "ABSTAIN":"Facts: p=true; q=UNKNOWN. Rule condition: p AND q.",
}

def mapping_for(i:int):
    return dict(zip(CLASSES,S3[i]))

def display_order(template_i:int, perm_i:int, class_i:int):
    orders=tuple(permutations(CLASSES))
    return orders[(perm_i + 2*class_i + 3*template_i) % len(orders)]

def codebook(mapping, order, style):
    if style=="lines":
        return "\n".join(f"{c} -> {mapping[c]}" for c in order)
    if style=="table":
        return " ".join(f"[{c} | {mapping[c]}]" for c in order)
    return "; ".join(f"{c} means {mapping[c]}" for c in order)

def prompt_for(template, mapping, order, scenario):
    if template=="T1_CODEBOOK_THEN_CASE":
        return (
            "Codebook:\n"+codebook(mapping,order,"lines")+
            "\n\nCase:\n"+scenario+
            "\n\nReturn exactly one codebook symbol."
        )
    if template=="T2_CASE_THEN_CODEBOOK":
        return (
            "Case:\n"+scenario+
            "\n\nEpisode codebook:\n"+codebook(mapping,order,"lines")+
            "\n\nReturn exactly one codebook symbol."
        )
    if template=="T3_TABLE_STYLE_CODEBOOK":
        return (
            "Episode mapping table: "+codebook(mapping,order,"table")+
            "\nObservation: "+scenario+
            "\nOutput one mapped symbol only."
        )
    if template=="T4_DIALOGUE_STYLE_EPISODE":
        return (
            "Operator: For this episode, "+codebook(mapping,order,"dialogue")+".\n"
            "Analyst: "+scenario+"\n"
            "Operator: Reply with one symbol only."
        )
    raise ValueError(template)

def build_rows():
    templates=(
        "T1_CODEBOOK_THEN_CASE",
        "T2_CASE_THEN_CODEBOOK",
        "T3_TABLE_STYLE_CODEBOOK",
        "T4_DIALOGUE_STYLE_EPISODE",
    )
    rows=[]
    for ti,t in enumerate(templates):
        for pi in range(6):
            mapping=mapping_for(pi)
            for ci,c in enumerate(CLASSES):
                order=display_order(ti,pi,ci)
                target=mapping[c]
                rows.append({
                    "schema":"TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE/v1",
                    "evidence_class":"METHOD_ONLY",
                    "reality_level":"R2",
                    "family_id":f"DYNAMIC_CODEBOOK_BINDING_{t}",
                    "episode_group_id":f"{t}:{c}",
                    "permutation_id":f"P{pi}",
                    "provenance_ancestry_id":"claude-xeno-vector-evidence:a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c",
                    "split":"TRAIN_TEMPLATE_ONLY",
                    "selected_using_holdout":False,
                    "class_word_policy":"CODEBOOK_ONLY_ALLOWED_CANDIDATE",
                    "model_visible_prompt_template":prompt_for(t,mapping,order,SCENARIOS[c]),
                    "target_template":target,
                    "materialization_required":True,
                    "materializer_private":{
                        "hidden_class":c,
                        "realized_mapping":mapping,
                        "display_order":order,
                        "target_symbol_slot":target,
                        "symbol_source_requirement":"EXACT_ACCEPTED_46_ABI_ATOMS_EXCLUDING_REJECTED_OR",
                        "distinct_symbols_required":True,
                    },
                    "canonical_truth_allowed":False,
                    "direct_effect_authority":False,
                    "positive_jspace_label":False,
                })
    return rows

def validate(rows):
    if len(rows)!=72:
        raise AssertionError(f"rows={len(rows)} expected=72")
    perms=Counter(); fams=Counter(); cs=Counter(); cp=Counter(); groups=defaultdict(set)
    for r in rows:
        if r["evidence_class"]!="METHOD_ONLY" or r["positive_jspace_label"] is not False:
            raise AssertionError("evidence boundary")
        if r["materialization_required"] is not True:
            raise AssertionError("must remain unmaterialized")
        priv=r["materializer_private"]; c=priv["hidden_class"]; m=priv["realized_mapping"]
        if set(m)!=set(CLASSES) or sorted(m.values())!=sorted(ATOMS):
            raise AssertionError("realized mapping is not S3 bijection")
        if r["target_template"]!=m[c]:
            raise AssertionError("target not derived from realized mapping")
        visible=r["model_visible_prompt_template"]
        if "permutation_id" in visible or "hidden_class" in visible or "realized_mapping" in visible:
            raise AssertionError("private metadata leak")
        perms[r["permutation_id"]]+=1; fams[r["family_id"]]+=1
        cs[(c,m[c])]+=1
        cp[(c,tuple(priv["display_order"]).index(c))]+=1
        groups[r["episode_group_id"]].add(m[c])
    if sorted(perms.values())!=[12]*6: raise AssertionError(f"perm counts {perms}")
    if sorted(fams.values())!=[18]*4: raise AssertionError(f"family counts {fams}")
    if len(cs)!=9 or any(v!=8 for v in cs.values()): raise AssertionError(f"class-symbol {cs}")
    if len(cp)!=9 or any(v!=8 for v in cp.values()): raise AssertionError(f"class-position {cp}")
    if any(len(v)!=3 for v in groups.values()): raise AssertionError("counterfactual mapping coverage")
    return {
        "schema":"TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE_SELFTEST/v1",
        "status":"PASS",
        "scope":"SOURCE_TEMPLATE_ONLY_NO_ACCEPTED_DATASET_OR_RUNTIME_CREDIT",
        "rows":72,
        "families":4,
        "s3_permutations":6,
        "rows_per_permutation":12,
        "rows_per_family":18,
        "class_symbol_exact_balance":True,
        "class_codebook_position_exact_balance":True,
        "same_semantic_scenario_spans_all_three_symbol_slots":True,
        "positive_jspace_labels":0,
        "materialization_required":True,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    rows=build_rows()
    report=validate(rows)
    if args.output:
        args.output.write_text("".join(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n" for r in rows),encoding="utf-8")
    if args.self_test or not args.output:
        print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
