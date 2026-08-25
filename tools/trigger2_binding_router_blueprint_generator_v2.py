#!/usr/bin/env python3
"""Generate Trigger-2 dynamic-codebook binding blueprint v2.

Synthetic METHOD_ONLY candidates. Placeholders MUST be rebound to verified accepted
ABI atoms and tokenizer checked before any training eligibility or dataset credit.
"""
import argparse, itertools, json
from pathlib import Path

CLASSES=("ALLOW","DENY","ABSTAIN")
ABI_MANIFEST_SHA256="0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_INGEST="research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json"
TEMPLATES={
"TRAIN_T1_CHECK_MATRIX":("TRAIN",("<ABI_TR_T1_A>","<ABI_TR_T1_B>","<ABI_TR_T1_C>"),{
"ALLOW":"Check matrix: required_1=true; required_2=true; conflict_count=0; missing_count=0.",
"DENY":"Check matrix: required_1=true; required_2=false; conflict_count=1; missing_count=0.",
"ABSTAIN":"Check matrix: required_1=true; required_2=unknown; conflict_count=0; missing_count=1."}),
"TRAIN_T2_EVIDENCE_LEDGER":("TRAIN",("<ABI_TR_T2_A>","<ABI_TR_T2_B>","<ABI_TR_T2_C>"),{
"ALLOW":"Evidence ledger: every mandatory clause has a confirming record; contradictions=0; unresolved_records=0.",
"DENY":"Evidence ledger: one mandatory clause has a falsifying record; contradictions=1; unresolved_records=0.",
"ABSTAIN":"Evidence ledger: one mandatory clause lacks an observation; contradictions=0; unresolved_records=1."}),
"TRAIN_T3_SENSOR_REPORT":("TRAIN",("<ABI_TR_T3_A>","<ABI_TR_T3_B>","<ABI_TR_T3_C>"),{
"ALLOW":"Sensor report: gate_alpha=1; gate_beta=1; anomaly=0; unread_channel=0.",
"DENY":"Sensor report: gate_alpha=1; gate_beta=0; anomaly=1; unread_channel=0.",
"ABSTAIN":"Sensor report: gate_alpha=1; gate_beta=?; anomaly=0; unread_channel=1."}),
"TRAIN_T4_NESTED_STATE":("TRAIN",("<ABI_TR_T4_A>","<ABI_TR_T4_B>","<ABI_TR_T4_C>"),{
"ALLOW":'State object: {"must":{"x":1,"y":1},"faults":[],"unknown":[]}.',
"DENY":'State object: {"must":{"x":1,"y":0},"faults":["y"],"unknown":[]}.',
"ABSTAIN":'State object: {"must":{"x":1,"y":null},"faults":[],"unknown":["y"]}.'}),
"VALIDATION_T5_DIALOGUE":("VALIDATION",("<ABI_VA_T5_A>","<ABI_VA_T5_B>","<ABI_VA_T5_C>"),{
"ALLOW":"Witness dialogue: first witness confirms criterion p; second witness confirms criterion q; no discrepancy is recorded.",
"DENY":"Witness dialogue: first witness confirms criterion p; second witness contradicts criterion q; one discrepancy is recorded.",
"ABSTAIN":"Witness dialogue: first witness confirms criterion p; no observation exists for criterion q; the record is incomplete."}),
"HOLDOUT_T6_CLAYCODE":("HOLDOUT",("<ABI_HO_T6_A>","<ABI_HO_T6_B>","<ABI_HO_T6_C>"),{
"ALLOW":"obs{req.a=1;req.b=1;viol=0;unk=0}",
"DENY":"obs{req.a=1;req.b=0;viol=1;unk=0}",
"ABSTAIN":"obs{req.a=1;req.b=?;viol=0;unk=1}"})}

def rows():
    for tid,(split,pool,scenes) in TEMPLATES.items():
        for semantic_class in CLASSES:
            family=f"BIND_{tid}_{semantic_class}_F01"
            ancestry=f"trigger2-v2-binding-{tid.lower()}-{semantic_class.lower()}"
            for pid,perm in enumerate(itertools.permutations(range(3))):
                mapping={cls:pool[perm[i]] for i,cls in enumerate(CLASSES)}
                target=mapping[semantic_class]
                prompt=("CODEBOOK\n"+f"ALLOW -> {mapping['ALLOW']}\nDENY -> {mapping['DENY']}\nABSTAIN -> {mapping['ABSTAIN']}\n"
                        +"END_CODEBOOK\n"+f"SCENE\n{scenes[semantic_class]}\nEND_SCENE\n"
                        +"Return only the atom selected by the episode-local codebook.")
                yield {
                    "schema":"ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
                    "evidence_class":"METHOD_ONLY","reality_level":"R2",
                    "family_id":family,"provenance_ancestry_id":ancestry,
                    "canonical_truth_allowed":False,"direct_effect_authority":False,
                    "fact_status":"NOT_APPLICABLE","target_type":"DYNAMIC_CODEBOOK_BINDING_BLUEPRINT",
                    "split":split,"split_unit":"CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                    "selected_using_holdout":False,"training_eligible":False,
                    "render_status":"ABI_ATOM_RENDER_REQUIRED",
                    "class_label_visibility_rule":"CLASS_LABELS_ALLOWED_ONLY_INSIDE_CODEBOOK",
                    "template_id":tid,"s3_permutation_id":f"P{pid}","realized_mapping":mapping,
                    "audit_semantic_class":semantic_class,
                    "audit_semantic_class_visibility":"EXCLUDED_FROM_MODEL_INPUT",
                    "target_atom_placeholder":target,"abi_manifest_sha256":ABI_MANIFEST_SHA256,
                    "source_evidence_ingest":SOURCE_INGEST,"prompt":prompt,"target":target,
                }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("output",type=Path); args=ap.parse_args()
    text="\n".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows())+"\n"
    args.output.write_text(text,encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
