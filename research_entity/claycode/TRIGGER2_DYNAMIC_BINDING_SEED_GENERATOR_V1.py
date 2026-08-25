#!/usr/bin/env python3
"""Trigger-2 dynamic codebook-binding seed generator v1.

Purpose
-------
Generate a SMALL, AUDITABLE candidate family for the measured failure mode:
semantic decision is available, but episode-local codebook binding to the exact output
identifier is weak/context-dependent.

This is CANDIDATE_DATA only. It is deliberately NOT a training-upload artifact.
It does not claim Qwen3.5 model runtime evidence, positive J-Space causality, or ABI-atom
compatibility. The logical symbol surfaces A/B/C must be replaced or explicitly admitted
against the exact frozen tokenizer/ABI before any train-file promotion.

The design directly closes the critical generator defect identified in the 2026-08-25
Claude XENO evidence ingest: the selected S3 permutation constructs the ACTUAL mapping,
not metadata only.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_DYNAMIC_BINDING_SEED/v1"
GENERATOR = "TRIGGER2_DYNAMIC_BINDING_SEED_GENERATOR_V1"
SEED = 20260825

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SYMBOLS = ("A", "B", "C")  # logical opaque placeholders; tokenizer/ABI admission still required
PERMUTATIONS = tuple(itertools.permutations(SYMBOLS))
TEMPLATES = (
    "T1_KV_PACKET",
    "T2_PROSE_CASE",
    "T3_TABLE_QUERY",
    "T4_CLAYCODE_COMPACT",
)
FROZEN_UNSEEN_TEMPLATE_ID = "T5_FROZEN_UNSEEN_TEMPLATE__BODY_NOT_IN_THIS_GENERATOR"

# Pre-registered resolution of the source-spec tension:
# class labels may occur only inside the episode-local codebook. Outside that span,
# neither exact labels nor obvious shortcut synonyms are allowed.
BANNED_OUTSIDE_CODEBOOK = re.compile(
    r"\b(?:allow|allowed|permit|permitted|deny|denied|reject|rejected|abstain|abstention)\b",
    re.IGNORECASE,
)

# One deliberately narrow semantic family. It is useful for generator/mechanism audit,
# but MUST NOT be split across train/validation as if it were independent semantic evidence.
CASES = {
    "ALLOW": {
        "role": "coordinator",
        "lease_present": True,
        "lease_epoch": 47,
        "current_epoch": 47,
        "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha",
        "target": "S1",
    },
    "DENY": {
        "role": "coordinator",
        "lease_present": True,
        "lease_epoch": 46,
        "current_epoch": 47,
        "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha",
        "target": "S1",
    },
    "ABSTAIN": {
        "role": "coordinator",
        "lease_present": True,
        "lease_epoch": None,
        "current_epoch": 47,
        "lease_scope": "workspace:alpha",
        "request_scope": "workspace:alpha",
        "target": "S1",
    },
}


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def mapping_for(permutation):
    # Causal construction: permutation directly defines class -> symbol.
    return dict(zip(CLASSES, permutation))


def codebook(mapping: dict[str, str], rng: random.Random) -> str:
    conditions = {
        "ALLOW": (
            "all required fields are present AND role=coordinator AND lease_present=true "
            "AND lease_epoch=current_epoch AND lease_scope=request_scope AND target=S1"
        ),
        "DENY": (
            "all required fields are present AND the conjunction required by the first semantic class is false"
        ),
        "ABSTAIN": "one or more required fields are absent",
    }
    order = list(CLASSES)
    rng.shuffle(order)
    lines = ["CODEBOOK_BEGIN"]
    for cls in order:
        lines.append(f"{cls} => {mapping[cls]} :: {conditions[cls]}")
    lines.append("CODEBOOK_END")
    return "\n".join(lines)


def render_facts(template: str, facts: dict, rng: random.Random) -> str:
    # Render the same latent state through four materially different surfaces.
    if template == "T1_KV_PACKET":
        items = list(facts.items())
        rng.shuffle(items)
        return "CASE_BEGIN\n" + "\n".join(
            f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in items
        ) + "\nCASE_END"

    if template == "T2_PROSE_CASE":
        epoch_phrase = (
            "The lease epoch field is absent."
            if facts["lease_epoch"] is None
            else f"The lease epoch is {facts['lease_epoch']}."
        )
        return (
            f"The node role is {facts['role']}. A lease is present. {epoch_phrase} "
            f"The current epoch is {facts['current_epoch']}. The lease scope is {facts['lease_scope']} "
            f"and the request scope is {facts['request_scope']}. The requested target is {facts['target']}."
        )

    if template == "T3_TABLE_QUERY":
        value = lambda v: "<missing>" if v is None else str(v).lower() if isinstance(v, bool) else str(v)
        rows = [
            ("role", facts["role"]),
            ("lease_present", facts["lease_present"]),
            ("lease_epoch", facts["lease_epoch"]),
            ("current_epoch", facts["current_epoch"]),
            ("lease_scope", facts["lease_scope"]),
            ("request_scope", facts["request_scope"]),
            ("target", facts["target"]),
        ]
        rng.shuffle(rows)
        return "FIELDS\n" + "\n".join(f"| {k} | {value(v)} |" for k, v in rows)

    if template == "T4_CLAYCODE_COMPACT":
        lease_epoch = "_" if facts["lease_epoch"] is None else str(facts["lease_epoch"])
        return (
            "gate{"
            f"role:{facts['role']};lease:1;le:{lease_epoch};ce:{facts['current_epoch']};"
            f"ls:{facts['lease_scope']};rs:{facts['request_scope']};dst:{facts['target']}"
            "}"
        )

    raise ValueError(template)


def strip_codebook(prompt: str) -> str:
    return re.sub(r"CODEBOOK_BEGIN.*?CODEBOOK_END", "", prompt, flags=re.DOTALL)


def make_row(pi: int, permutation, cls: str, template: str) -> dict:
    mapping = mapping_for(permutation)
    # Row-specific RNG gives stable order independent of iteration/refactoring.
    row_seed_material = f"{SEED}|{pi}|{cls}|{template}".encode()
    row_seed = int.from_bytes(hashlib.sha256(row_seed_material).digest()[:8], "big")
    rng = random.Random(row_seed)
    cb = codebook(mapping, rng)
    fact_text = render_facts(template, dict(CASES[cls]), rng)
    prompt = (
        cb
        + "\n"
        + fact_text
        + "\nReturn exactly one codebook symbol and no explanation."
    )
    row_id = f"bind-p{pi}-{cls.lower()}-{template.lower()}"
    return {
        "schema": SCHEMA,
        "id": row_id,
        "status": "CANDIDATE_DATA_NOT_TRAIN_UPLOAD_READY",
        "objective": ["A_CONTEXT_INVARIANT_BINDING", "B_DYNAMIC_CODEBOOK_BINDING"],
        "semantic_family": "COORDINATOR_LEASE_EPOCH_GATE_V1",
        "mapping_id": f"S3_P{pi}",
        "mapping": mapping,
        "semantic_class": cls,
        "template_id": template,
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": mapping[cls]},
        ],
        "target_symbol": mapping[cls],
        "provenance": {
            "generator": GENERATOR,
            "generator_seed": SEED,
            "evidence_source": "2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json",
            "evidence_class": "C_DETERMINISTIC_ARCHITECTURE_PROTOCOL_TEACHING_PLUS_MEASURED_FAILURE_TARGET",
        },
    }


def generate_rows() -> list[dict]:
    rows = []
    # Full factorial: every S3 mapping x every semantic class x every admitted training template.
    # 6 * 3 * 4 = 72 rows.
    for pi, perm in enumerate(PERMUTATIONS):
        for cls in CLASSES:
            for template in TEMPLATES:
                rows.append(make_row(pi, perm, cls, template))
    return rows


def mutual_information_class_symbol(rows) -> float:
    n = len(rows)
    joint = Counter((r["semantic_class"], r["target_symbol"]) for r in rows)
    pc = Counter(r["semantic_class"] for r in rows)
    ps = Counter(r["target_symbol"] for r in rows)
    mi = 0.0
    for (c, s), count in joint.items():
        pxy = count / n
        px = pc[c] / n
        py = ps[s] / n
        mi += pxy * math.log2(pxy / (px * py))
    return mi


def audit(rows: list[dict]) -> dict:
    errors = []
    expected_n = len(PERMUTATIONS) * len(CLASSES) * len(TEMPLATES)
    if len(rows) != expected_n:
        errors.append(f"row_count:{len(rows)}!={expected_n}")

    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_row_id")

    # Exact S3 realization, not metadata-only.
    realized = {tuple(r["mapping"][c] for c in CLASSES) for r in rows}
    expected = set(PERMUTATIONS)
    if realized != expected:
        errors.append(f"s3_realized_mismatch:{sorted(realized)}")

    # Every template independently gets exact class-symbol counterbalance:
    # six permutations x each class -> each class-symbol cell exactly 2 times.
    template_cell_counts = {}
    for t in TEMPLATES:
        sub = [r for r in rows if r["template_id"] == t]
        cc = Counter((r["semantic_class"], r["target_symbol"]) for r in sub)
        template_cell_counts[t] = {f"{c}->{s}": cc[(c, s)] for c in CLASSES for s in SYMBOLS}
        if any(cc[(c, s)] != 2 for c in CLASSES for s in SYMBOLS):
            errors.append(f"template_counterbalance:{t}")

    global_cells = Counter((r["semantic_class"], r["target_symbol"]) for r in rows)
    if any(global_cells[(c, s)] != 8 for c in CLASSES for s in SYMBOLS):
        errors.append("global_counterbalance")

    # Verify the selected permutation is actually used to derive the answer.
    for r in rows:
        if r["target_symbol"] != r["mapping"][r["semantic_class"]]:
            errors.append(f"target_not_causally_mapped:{r['id']}")

    # Labels/obvious synonyms are allowed only in the delimited local codebook.
    leak_rows = []
    for r in rows:
        outside = strip_codebook(r["messages"][0]["content"])
        if BANNED_OUTSIDE_CODEBOOK.search(outside):
            leak_rows.append(r["id"])
    if leak_rows:
        errors.append(f"class_word_leak:{leak_rows[:5]}")

    # Output must be exactly one logical symbol. Tokenizer-level single-token admission is separate.
    if any(r["messages"][1]["content"] not in SYMBOLS for r in rows):
        errors.append("bad_output_surface")

    mi = mutual_information_class_symbol(rows)
    if abs(mi) > 1e-12:
        errors.append(f"class_symbol_mi_nonzero:{mi}")

    rendered = "\n".join(canonical_json(r) for r in rows) + "\n"
    return {
        "schema": "CLAY_TRIGGER2_DYNAMIC_BINDING_SEED_AUDIT/v1",
        "generator": GENERATOR,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "row_count": len(rows),
        "full_factorial": "6_S3_PERMUTATIONS_x_3_CLASSES_x_4_TEMPLATES",
        "realized_s3_count": len(realized),
        "class_symbol_mutual_information_bits": mi,
        "global_class_symbol_cell_counts": {
            f"{c}->{s}": global_cells[(c, s)] for c in CLASSES for s in SYMBOLS
        },
        "template_class_symbol_cell_counts": template_cell_counts,
        "class_word_leak_rows": leak_rows,
        "frozen_unseen_template_id": FROZEN_UNSEEN_TEMPLATE_ID,
        "family_split_warning": (
            "All 72 rows are one semantic family and MUST remain together for future family-level splitting; "
            "this seed is generator/mechanism QA, not an independent train/validation/holdout population."
        ),
        "promotion_blockers": [
            "Replace/admit logical A/B/C surfaces against the exact selected Qwen3.5 tokenizer and 46-atom ABI policy.",
            "Add independent semantic families before any family-level train/validation/holdout split.",
            "Keep the frozen unseen-template body outside train and validation generation.",
            "Run independent shortcut/leakage review before scale-up.",
            "Do not treat this deterministic protocol family as positive Qwen3.5 J-Space causal evidence.",
        ],
        "jsonl_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=Path)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    rows = generate_rows()
    report = audit(rows)
    rendered = "\n".join(canonical_json(r) for r in rows) + "\n"

    if args.jsonl:
        args.jsonl.write_text(rendered, encoding="utf-8")
    if args.audit:
        args.audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.stdout:
        print(rendered, end="")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
