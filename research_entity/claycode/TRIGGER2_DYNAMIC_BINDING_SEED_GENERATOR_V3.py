#!/usr/bin/env python3
"""Trigger-2 dynamic binding design-matrix generator v3.

This successor extends the existing 72-row S3 x class x template matrix with an
INDEPENDENT QUERY-POLARITY FACTOR required by supervisor 8.78's current J-Space
successor design law.

Scope is deliberately PRE-MATERIALIZATION / DESIGN-MATRIX ONLY:
- 4 training-template families
- all 6 S3 class->symbol mappings
- 3 semantic classes
- 2 query-polarity surfaces
= 144 rows

It is NOT a direct TRAIN split, not ABI-materialized data, not a sealed holdout,
and mints zero J-Space/model/training credit. Final materialization still requires
the exact accepted 46-atom inventory, exact tokenizer identity, family/provenance
split policy, and the current fail-closed binding gates.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_DYNAMIC_BINDING_DESIGN_MATRIX/v3"
GENERATOR = "TRIGGER2_DYNAMIC_BINDING_SEED_GENERATOR_V3"
SEED = 20260825

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SYMBOLS = ("A", "B", "C")  # logical placeholders only; never claim ABI admission
POLARITIES = ("DIRECT", "NEGATED")
TEMPLATES = (
    "T1_KV_PACKET",
    "T2_PROSE_CASE",
    "T3_TABLE_QUERY",
    "T4_CLAYCODE_COMPACT",
)
FROZEN_UNSEEN_TEMPLATE_ID = "T5_FROZEN_UNSEEN_TEMPLATE__BODY_NOT_PRESENT"
PERMUTATIONS = tuple(itertools.permutations(SYMBOLS))
CODEBOOK_ORDERS = tuple(itertools.permutations(CLASSES))

BANNED_OUTSIDE_CODEBOOK = re.compile(
    r"\b(?:allow|allowed|permit|permitted|deny|denied|reject|rejected|abstain|abstention)\b",
    re.IGNORECASE,
)

CASES = {
    "ALLOW": {
        "role": "coordinator", "lease_present": True, "lease_epoch": 47,
        "current_epoch": 47, "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha", "target": "S1",
    },
    "DENY": {
        "role": "coordinator", "lease_present": True, "lease_epoch": 46,
        "current_epoch": 47, "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha", "target": "S1",
    },
    "ABSTAIN": {
        "role": "coordinator", "lease_present": True, "lease_epoch": None,
        "current_epoch": 47, "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha", "target": "S1",
    },
}

CONDITIONS = {
    "ALLOW": "all required fields are present AND role=coordinator AND lease_present=true AND lease_epoch=current_epoch AND lease_scope=request_scope AND target=S1",
    "DENY": "all required fields are present AND the conjunction required by the first semantic class is false",
    "ABSTAIN": "one or more required fields are absent",
}

QUERY = {
    "DIRECT": "Return exactly the one codebook symbol assigned to the current case.",
    "NEGATED": "Return exactly the one codebook symbol that is not ruled out for the current case.",
}


def canonical_json(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def mapping_for(perm):
    return dict(zip(CLASSES, perm))


def codebook_order_id(template_i: int, perm_i: int, class_i: int, polarity_i: int) -> int:
    # Preregistered exact schedule found before matrix emission.
    # It gives every one of the 6 display orders exactly 24 rows across the 144-row
    # matrix, target line positions 48/48/48, and I(symbol; target_position)=0 and
    # I(class; target_position)=0. It is independent of prompt generation randomness.
    return (perm_i + 2 * class_i + 2 * polarity_i + 5 * template_i) % 6


def render_codebook(mapping, order):
    lines = ["CODEBOOK_BEGIN"]
    for cls in order:
        lines.append(f"{cls} => {mapping[cls]} :: {CONDITIONS[cls]}")
    lines.append("CODEBOOK_END")
    return "\n".join(lines)


def render_facts(template: str, facts: dict) -> str:
    if template == "T1_KV_PACKET":
        keys = ("target", "lease_scope", "current_epoch", "role", "request_scope", "lease_present", "lease_epoch")
        return "CASE_BEGIN\n" + "\n".join(f"{k}={json.dumps(facts[k], ensure_ascii=False)}" for k in keys) + "\nCASE_END"
    if template == "T2_PROSE_CASE":
        le = "The lease epoch field is absent." if facts["lease_epoch"] is None else f"The lease epoch is {facts['lease_epoch']}."
        return (f"The node role is {facts['role']}. A lease is present. {le} The current epoch is {facts['current_epoch']}. "
                f"The lease scope is {facts['lease_scope']} and the request scope is {facts['request_scope']}. The requested target is {facts['target']}.")
    if template == "T3_TABLE_QUERY":
        def value(v):
            return "<missing>" if v is None else str(v).lower() if isinstance(v, bool) else str(v)
        keys = ("lease_present", "request_scope", "lease_epoch", "target", "role", "current_epoch", "lease_scope")
        return "FIELDS\n" + "\n".join(f"| {k} | {value(facts[k])} |" for k in keys)
    if template == "T4_CLAYCODE_COMPACT":
        le = "_" if facts["lease_epoch"] is None else str(facts["lease_epoch"])
        return ("gate{" f"role:{facts['role']};lease:1;le:{le};ce:{facts['current_epoch']};"
                f"ls:{facts['lease_scope']};rs:{facts['request_scope']};dst:{facts['target']}" "}")
    raise ValueError(template)


def strip_codebook(prompt):
    return re.sub(r"CODEBOOK_BEGIN.*?CODEBOOK_END", "", prompt, flags=re.DOTALL)


def make_row(template_i, perm_i, class_i, polarity_i):
    template = TEMPLATES[template_i]
    cls = CLASSES[class_i]
    polarity = POLARITIES[polarity_i]
    mapping = mapping_for(PERMUTATIONS[perm_i])
    order_id = codebook_order_id(template_i, perm_i, class_i, polarity_i)
    order = CODEBOOK_ORDERS[order_id]
    prompt = (
        render_codebook(mapping, order) + "\n" +
        render_facts(template, dict(CASES[cls])) + "\n" +
        QUERY[polarity] + "\nOUTPUT: one codebook symbol only."
    )
    target = mapping[cls]
    row_id = f"bindv3-t{template_i+1}-p{perm_i}-{cls.lower()}-{polarity.lower()}"
    return {
        "schema": SCHEMA,
        "id": row_id,
        "status": "PRE_MATERIALIZATION_DESIGN_MATRIX_ONLY",
        "trainable": False,
        "split": "UNASSIGNED_PRE_MATERIALIZATION",
        "objective": ["A_CONTEXT_INVARIANT_BINDING", "B_DYNAMIC_CODEBOOK_BINDING"],
        "semantic_family": "COORDINATOR_LEASE_EPOCH_GATE_V1",
        "template_id": template,
        "mapping_id": f"S3_P{perm_i}",
        "mapping": mapping,
        "semantic_class": cls,
        "query_polarity": polarity,
        "codebook_order_id": f"O{order_id}",
        "codebook_order": list(order),
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": target},
        ],
        "target_symbol": target,
        "provenance": {
            "generator": GENERATOR,
            "generator_seed": SEED,
            "authority_epoch_at_design": "8.78",
            "current_main_observed_at_design": "4e9b58bdd1a017e4f25e61554016463a797c586d",
            "binding_evidence_source": "2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json",
            "polarity_evidence_source": "2026-08-25_FORSCHUNGSRUN_2_POLARITY_FACTORIAL_CORRECTION_GPT56SOL.json",
            "evidence_class": "METHOD_ONLY_PRE_MATERIALIZATION_DESIGN",
        },
        "credit_boundary": {
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "jspace_positive_label": False,
            "accepted_dataset_tokens": 0,
            "training_credit": 0,
        },
    }


def generate_rows():
    return [
        make_row(t, p, c, q)
        for t in range(len(TEMPLATES))
        for p in range(len(PERMUTATIONS))
        for c in range(len(CLASSES))
        for q in range(len(POLARITIES))
    ]


def mi(pairs):
    n = len(pairs)
    a = Counter(x for x, _ in pairs); b = Counter(y for _, y in pairs); j = Counter(pairs)
    return sum((v/n)*math.log2((v/n)/((a[x]/n)*(b[y]/n))) for (x,y),v in j.items()) if n else float("inf")


def audit(rows):
    errors=[]
    if len(rows) != 144: errors.append(f"row_count:{len(rows)}!=144")
    if any(r["trainable"] or r["split"] != "UNASSIGNED_PRE_MATERIALIZATION" for r in rows): errors.append("premature_train_or_split_assignment")

    realized = {tuple(r["mapping"][c] for c in CLASSES) for r in rows}
    if realized != set(PERMUTATIONS): errors.append("full_s3_not_realized")
    for r in rows:
        if r["target_symbol"] != r["mapping"][r["semantic_class"]]: errors.append("target_not_derived:"+r["id"])
        outside = strip_codebook(r["messages"][0]["content"])
        if BANNED_OUTSIDE_CODEBOOK.search(outside): errors.append("class_word_leak:"+r["id"])

    # Exact semantic-target x emitted-code x query-polarity factorial.
    cells = Counter((r["semantic_class"], r["target_symbol"], r["query_polarity"]) for r in rows)
    if len(cells)!=18 or set(cells.values())!={8}: errors.append("target_code_polarity_factorial_invalid")
    by_template = Counter((r["template_id"], r["semantic_class"], r["target_symbol"], r["query_polarity"]) for r in rows)
    if len(by_template)!=72 or set(by_template.values())!={2}: errors.append("template_target_code_polarity_factorial_invalid")

    perm_counts = Counter(r["mapping_id"] for r in rows)
    order_counts = Counter(r["codebook_order_id"] for r in rows)
    if set(perm_counts.values())!={24}: errors.append("s3_count_imbalance")
    if set(order_counts.values())!={24}: errors.append("codebook_order_imbalance")

    positions = Counter(r["codebook_order"].index(r["semantic_class"]) for r in rows)
    if positions != Counter({0:48,1:48,2:48}): errors.append("target_line_position_imbalance")

    metrics = {
        "class_symbol_mi_bits": mi([(r["semantic_class"],r["target_symbol"]) for r in rows]),
        "class_polarity_mi_bits": mi([(r["semantic_class"],r["query_polarity"]) for r in rows]),
        "symbol_polarity_mi_bits": mi([(r["target_symbol"],r["query_polarity"]) for r in rows]),
        "symbol_target_position_mi_bits": mi([(r["target_symbol"],r["codebook_order"].index(r["semantic_class"])) for r in rows]),
        "class_target_position_mi_bits": mi([(r["semantic_class"],r["codebook_order"].index(r["semantic_class"])) for r in rows]),
    }
    if any(abs(v)>1e-12 for v in metrics.values()): errors.append("nonzero_shortcut_mi:"+repr(metrics))

    rendered = "\n".join(canonical_json(r) for r in rows) + "\n"
    return {
        "schema":"CLAY_TRIGGER2_DYNAMIC_BINDING_DESIGN_MATRIX_AUDIT/v3",
        "status":"PASS" if not errors else "FAIL",
        "errors":errors,
        "row_count":len(rows),
        "factorial":"4_templates_x_6_S3_x_3_classes_x_2_query_polarities",
        "target_code_polarity_cell_count":dict(("|".join(k),v) for k,v in sorted(cells.items())),
        "permutation_counts":dict(sorted(perm_counts.items())),
        "codebook_order_counts":dict(sorted(order_counts.items())),
        "target_line_positions":dict(sorted(positions.items())),
        "mutual_information_bits":metrics,
        "frozen_unseen_template_id":FROZEN_UNSEEN_TEMPLATE_ID,
        "materialization_blockers":[
            "exact accepted 46-atom ABI inventory + manifest/member identity",
            "exact selected model/tokenizer identity and single-token atom verification",
            "predeclared family/provenance split policy and unseen-atom partition",
            "materialized post-split counterbalance/MI audit",
            "generic candidate gate + current specialized binding gate",
        ],
        "split_warning":"This full-S3 matrix is an upstream design oracle. It MUST NOT be labeled TRAIN if unseen-S3 evaluation is claimed; materialization/split reconciliation happens later over many accepted atom triplets.",
        "jsonl_sha256":hashlib.sha256(rendered.encode()).hexdigest(),
        "credit":"STATIC_PRE_MATERIALIZATION_DESIGN_VALIDATION_ONLY",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--jsonl",type=Path)
    ap.add_argument("--audit",type=Path)
    args=ap.parse_args()
    rows=generate_rows(); report=audit(rows)
    rendered="\n".join(canonical_json(r) for r in rows)+"\n"
    if args.jsonl: args.jsonl.write_text(rendered,encoding="utf-8")
    if args.audit: args.audit.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if report["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
