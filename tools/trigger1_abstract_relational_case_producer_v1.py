#!/usr/bin/env python3
"""Generate tokenizer-bound structural ternary cases for the hard Trigger-1 abstraction test.

Six opaque content tokens encode two directed edges and one query pair. The exact same token
and word multiset is used for all three evaluator-side target states; only slot order changes:

  evaluator AFFIRMATIVE: edge1 a->b, edge2 b->c, query a->c
  evaluator NEGATIVE:    edge1 a->b, edge2 b->c, query c->a
  evaluator NEUTRAL:     edge1 a->b, edge2 c->b, query a->c

The canonical class names never enter model-facing text. Evaluation code mappings rotate as a
Latin square. BASIS/CALIBRATION/HOLDOUT receive disjoint stable single-token lexeme pools from
the exact tokenizer.json. The result self-audits through trigger1_abstract_lexical_token_audit_v1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import trigger1_abstract_lexical_token_audit_v1 as audit

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_CASE_PRODUCER/v1"
FAMILY_COUNTS = {"BASIS": 6, "CALIBRATION": 3, "HOLDOUT": 3}
SEQUENCES = {
    "AFFIRMATIVE": (0, 1, 1, 2, 0, 2),
    "NEGATIVE": (0, 1, 1, 2, 2, 0),
    "NEUTRAL": (0, 1, 2, 1, 0, 2),
}
ROTATIONS = (
    {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
    {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
    {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
)
CLEAN = re.compile(r"[A-Za-z]{3,18}")


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_single_token_lexemes(tok: Tokenizer) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for token_id in range(tok.get_vocab_size(with_added_tokens=True)):
        decoded = tok.decode([token_id], skip_special_tokens=True)
        word = decoded.strip()
        folded = word.casefold()
        if not CLEAN.fullmatch(word) or folded in seen:
            continue
        if folded in audit.SEMANTIC_PROXY_LEXICON or folded in audit.FIXED_SCAFFOLD:
            continue
        surface = " " + word
        if tok.encode(surface).ids != [token_id]:
            continue
        rows.append((token_id, surface, folded))
        seen.add(folded)
    return rows


def seq(group: tuple[tuple[int, str, str], ...], target: str) -> tuple[list[int], str]:
    order = SEQUENCES[target]
    return [group[i][0] for i in order], "".join(group[i][1] for i in order)


def select_groups(tok: Tokenizer) -> list[tuple[tuple[int, str, str], ...]]:
    needed = sum(FAMILY_COUNTS.values())
    candidates = stable_single_token_lexemes(tok)
    groups: list[tuple[tuple[int, str, str], ...]] = []
    cursor = 0
    while len(groups) < needed and cursor + 2 < len(candidates):
        group = tuple(candidates[cursor : cursor + 3])
        cursor += 3
        good = True
        for target in audit.TARGETS:
            ids, text = seq(group, target)
            if tok.encode(text).ids != ids:
                good = False
                break
            if CounterLike(audit.content_words(text)) != CounterLike([group[0][2]] * 2 + [group[1][2]] * 2 + [group[2][2]] * 2):
                good = False
                break
        if good:
            groups.append(group)
    if len(groups) != needed:
        raise RuntimeError(f"INSUFFICIENT_STABLE_LEXEME_GROUPS:{len(groups)}:{needed}")
    return groups


def CounterLike(items: list[str]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return tuple(sorted(counts.items()))


def prompt(partition: str, family_index: int, content: str) -> str:
    protocol = (
        "/no_think\nRead six opaque content items by position: first-edge source, first-edge destination, "
        "second-edge source, second-edge destination, query source, query destination. "
        "Treat the edge relation as transitive across exactly two edges. Determine whether a two-edge path "
        "runs from query source to query destination, runs in the reverse query direction, or occurs in neither direction. "
    )
    if partition == "BASIS":
        tail = "Keep the resulting relation state internal; do not name a class."
    else:
        r = ROTATIONS[family_index % 3]
        tail = (
            f"Opaque code table: forward-path={r['AFFIRMATIVE']}; reverse-path={r['NEGATIVE']}; "
            f"neither-direction={r['NEUTRAL']}. Return only the code."
        )
    return protocol + tail + " Content stream:" + content


def produce(tokenizer_json: Path) -> dict[str, Any]:
    tok_bytes = tokenizer_json.read_bytes()
    tok = Tokenizer.from_file(str(tokenizer_json))
    groups = select_groups(tok)
    partitions: dict[str, list[dict[str, Any]]] = {p: [] for p in audit.PARTITIONS}
    selected: dict[str, list[dict[str, Any]]] = {p: [] for p in audit.PARTITIONS}
    cursor = 0
    for partition in audit.PARTITIONS:
        for family_index in range(FAMILY_COUNTS[partition]):
            group = groups[cursor]
            cursor += 1
            family_id = f"{partition.lower()}-structural-{family_index}"
            selected[partition].append({"family_id": family_id, "token_ids": [x[0] for x in group], "lexemes": [x[2] for x in group]})
            for target in audit.TARGETS:
                ids, content = seq(group, target)
                model_prompt = prompt(partition, family_index, content)
                leaked = set(audit.words(model_prompt)) & audit.SEMANTIC_PROXY_LEXICON
                if leaked:
                    raise RuntimeError("MODEL_FACING_PROXY_LEAK:" + ",".join(sorted(leaked)))
                if tok.encode(content).ids != ids:
                    raise RuntimeError("CONTENT_TOKENIZATION_DRIFT")
                partitions[partition].append(
                    {
                        "row_id": f"{family_id}:{target.lower()}",
                        "family_id": family_id,
                        "semantic_target": target,
                        "output_code_identity": ROTATIONS[family_index % 3][target] if partition in audit.EVAL_PARTITIONS else None,
                        "prompt": model_prompt,
                        "prompt_sha256": sha_text(model_prompt),
                        "content_text": content,
                        "content_token_ids": ids,
                        "model_facing_target_identity_exposed": False,
                        "model_facing_explicit_semantic_labels": False,
                    }
                )
    design = {
        "schema": audit.INPUT_SCHEMA,
        "producer_schema": SCHEMA,
        "frozen_before_holdout": True,
        "tokenizer_identity": {
            "tokenizer_json_sha256": hashlib.sha256(tok_bytes).hexdigest(),
            "content_token_ids_recomputed_from_exact_tokenizer": True,
        },
        "partitions": partitions,
        "producer_metadata": {
            "latent_task": "TWO_EDGE_QUERY_DIRECTION_TERNARY_RELATION_STATE",
            "target_carrier": "RELATION_SLOT_ORDER_NOT_LEXEME_IDENTITY",
            "selected_lexemes": selected,
        },
    }
    receipt = audit.audit(design)
    if receipt.get("pass") is not True:
        raise RuntimeError("SELF_LEXICAL_AUDIT_FAILED:" + "|".join(receipt.get("failures", [])))
    return {"schema": SCHEMA, "design": design, "lexical_audit_receipt": receipt}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-json", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = produce(args.tokenizer_json)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
