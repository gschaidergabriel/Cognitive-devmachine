#!/usr/bin/env python3
"""Deterministic logical audit-seed generator for Trigger-2 dynamic codebook binding.

This does NOT emit train-ready tokens. It emits ABI atom-row references only and fails closed
until a separate verified renderer resolves those rows through the exact XENO vector ABI,
model snapshot and tokenizer.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, re, sys
from collections import Counter

SCHEMA = "TRIGGER2_DYNAMIC_BINDING_LOGICAL_ROW/v1"
STATUS = "LOGICAL_AUDIT_SEED_NOT_TRAINABLE_UNTIL_ABI_RENDER"
SOURCE_MAIN_SHA = "0edcc2ca0dba28fa0536bc5834fe6ede05a46e96"
MODEL_ID = "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MODEL_SNAPSHOT = "591852bda6e1979f59e4b0f5ee2919697b12e936"
EXPECTED_JSONL_SHA256 = "8debff4cf0723cd49cc46d586806c9aad0ac68cdc6542e76bf83c4ffa84c1ccc"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
PERMS = tuple(itertools.permutations(range(3)))

FAMILIES = (
    ("T_BIND_RULE_V1", (0, 1, 2), {
        "ALLOW": "Every required condition is satisfied, and no conflicting condition is active.",
        "DENY": "An active constraint directly conflicts with the requested operation.",
        "ABSTAIN": "The record lacks the facts needed to determine whether the operation meets the constraints.",
    }, "Return only the episode codebook symbol for this case."),
    ("T_BIND_CAPABILITY_V1", (3, 4, 5), {
        "ALLOW": "The capability token is valid for the requested scope and the current epoch.",
        "DENY": "The capability token is outside the permitted scope for the requested operation.",
        "ABSTAIN": "The token provenance is incomplete, so scope validity cannot be established.",
    }, "Resolve the case through the local codebook and emit only its symbol."),
    ("T_BIND_EVIDENCE_V1", (6, 7, 8), {
        "ALLOW": "Independent receipts support the candidate at the same identity, with no verified counterreceipt.",
        "DENY": "A verified counterreceipt contradicts the candidate at the same identity.",
        "ABSTAIN": "Available receipts remain in conflict and no discriminator has resolved the disagreement.",
    }, "Use the episode mapping and output exactly one mapped symbol."),
    ("T_BIND_ENGINE_V1", (9, 10, 11), {
        "ALLOW": "The selected route matches the admitted engine identity and the required capability scope.",
        "DENY": "The selected route resolves to an engine identity that conflicts with the admission.",
        "ABSTAIN": "The route is known, but the bytes actually consumed by the engine have not been attested.",
    }, "Map the inferred class through this episode's codebook and emit only the symbol."),
)

def generate_rows():
    rows = []
    for fam_i, (template, triplet, situations, query) in enumerate(FAMILIES):
        for pidx, perm in enumerate(PERMS):
            mapping = {CLASSES[i]: triplet[perm[i]] for i in range(3)}
            for tidx, target in enumerate(CLASSES):
                cb_order = PERMS[(pidx + tidx * 2) % 6]
                codebook = [
                    {"class": CLASSES[i], "symbol_atom_row": mapping[CLASSES[i]]}
                    for i in cb_order
                ]
                rows.append({
                    "schema": SCHEMA,
                    "status": STATUS,
                    "row_id": f"bind-{fam_i+1:02d}-{pidx:02d}-{tidx:02d}",
                    "task_family": "DYNAMIC_CODEBOOK_BINDING",
                    "template_id": template,
                    "semantic_target_metadata_only": target,
                    "codebook_s3_permutation_id": pidx,
                    "codebook_entries": codebook,
                    "situation": situations[target],
                    "query": query,
                    "target_symbol_atom_row": mapping[target],
                    "render_contract": {
                        "class_labels_allowed_only_in_codebook": True,
                        "replace_symbol_atom_row_with_exact_abi_token": True,
                        "abi_required": "XENO_VECTOR_ABI/v0.1_OR_VERSIONED_SUCCESSOR",
                        "output_exactly_one_abi_symbol_token": True,
                    },
                    "provenance": {
                        "source_main_sha": SOURCE_MAIN_SHA,
                        "evidence_ingest": "research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json",
                        "target_model": MODEL_ID,
                        "target_model_snapshot": MODEL_SNAPSHOT,
                    },
                })
    return rows

def encode(rows):
    return "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows).encode()

def audit(rows, payload):
    assert len(rows) == 72
    assert Counter(r["template_id"] for r in rows) == Counter({x[0]: 18 for x in FAMILIES})
    assert Counter(r["semantic_target_metadata_only"] for r in rows) == Counter({c: 24 for c in CLASSES})
    assert Counter(r["codebook_s3_permutation_id"] for r in rows) == Counter({i: 12 for i in range(6)})
    for template, triplet, _, _ in FAMILIES:
        c = Counter()
        for r in rows:
            if r["template_id"] == template:
                c[(r["semantic_target_metadata_only"], triplet.index(r["target_symbol_atom_row"]))] += 1
        assert all(c[(cl, pos)] == 2 for cl in CLASSES for pos in range(3))
    pos = Counter()
    for r in rows:
        for i, e in enumerate(r["codebook_entries"]):
            pos[(e["class"], i)] += 1
        outside = (r["situation"] + " " + r["query"]).upper()
        assert not any(re.search(r"\\b" + cl + r"\\b", outside) for cl in CLASSES)
    assert all(pos[(cl, i)] == 24 for cl in CLASSES for i in range(3))
    digest = hashlib.sha256(payload).hexdigest()
    assert digest == EXPECTED_JSONL_SHA256, (digest, EXPECTED_JSONL_SHA256)
    return digest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="-")
    args = ap.parse_args()
    rows = generate_rows()
    payload = encode(rows)
    digest = audit(rows, payload)
    if args.out == "-":
        sys.stdout.buffer.write(payload)
    else:
        with open(args.out, "wb") as f:
            f.write(payload)
        print(json.dumps({"rows": len(rows), "sha256": digest, "status": STATUS}))

if __name__ == "__main__":
    main()
