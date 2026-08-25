#!/usr/bin/env python3
"""Produce the hard label-free, lexically-disjoint Trigger-1 abstract-state case design.

The model-facing latent task is deliberately structural rather than decision/compliance
language.  Six opaque content items encode two directed edges plus a query pair.  The
three evaluator-side states are:

  AFFIRMATIVE -> a two-edge path exists from query source to query destination
  NEGATIVE    -> a two-edge path exists only in the reverse query direction
  NEUTRAL     -> neither two-edge query direction exists

Those names never enter model-facing text.  For a matched family the exact same three
single-token lexemes occur with the exact same multiplicities for every state; only their
order across structural slots changes.  BASIS, CALIBRATION and HOLDOUT receive disjoint
single-token lexeme pools selected from the exact tokenizer.json.  Evaluation code mapping
is Latin-square rotated across families.

This producer performs offline tokenizer work only; it does not load or execute the model.
Its output is directly consumable by trigger1_abstract_state_deconfound_gate_v1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from tokenizers import Tokenizer

import trigger1_abstract_state_deconfound_gate_v1 as gate

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_CASE_PRODUCER/v1"
TARGET_SEQUENCE = {
    # edge1 a->b, edge2 b->c, query a->c
    "AFFIRMATIVE": (0, 1, 1, 2, 0, 2),
    # same edges, reverse query c->a
    "NEGATIVE": (0, 1, 1, 2, 2, 0),
    # edges a->b and c->b, query a->c: neither query direction has a two-edge path
    "NEUTRAL": (0, 1, 2, 1, 0, 2),
}
FAMILY_COUNTS = {"BASIS": 6, "CALIBRATION": 3, "HOLDOUT": 3}
ROTATIONS = (
    {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
    {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
    {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
)
CLEAN_WORD = re.compile(r"[A-Za-z]{3,18}")


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokenizable_lexemes(tokenizer: Tokenizer) -> list[tuple[int, str, str]]:
    """Find stable leading-space single-token words in deterministic token-id order."""
    out: list[tuple[int, str, str]] = []
    seen_words: set[str] = set()
    for token_id in range(tokenizer.get_vocab_size(with_added_tokens=True)):
        decoded = tokenizer.decode([token_id], skip_special_tokens=True)
        word = decoded.strip()
        folded = word.casefold()
        if not CLEAN_WORD.fullmatch(word):
            continue
        if folded in seen_words or folded in gate.PROXY_LEXEMES or folded in gate.SCAFFOLD:
            continue
        surface = " " + word
        if tokenizer.encode(surface).ids != [token_id]:
            continue
        out.append((token_id, surface, folded))
        seen_words.add(folded)
    return out


def _sequence(group: tuple[tuple[int, str, str], ...], target: str) -> tuple[list[int], str]:
    order = TARGET_SEQUENCE[target]
    ids = [group[i][0] for i in order]
    text = "".join(group[i][1] for i in order)
    return ids, text


def select_groups(tokenizer: Tokenizer) -> list[tuple[tuple[int, str, str], ...]]:
    needed = sum(FAMILY_COUNTS.values())
    candidates = tokenizable_lexemes(tokenizer)
    groups: list[tuple[tuple[int, str, str], ...]] = []
    cursor = 0
    while len(groups) < needed and cursor + 2 < len(candidates):
        group = tuple(candidates[cursor : cursor + 3])
        cursor += 3
        valid = True
        for target in gate.TARGETS:
            ids, text = _sequence(group, target)
            if tokenizer.encode(text).ids != ids:
                valid = False
                break
            # Gate word normalization must see exactly the same lexeme multiset.
            if sorted(gate.content_words(text)) != sorted([group[0][2]] * 2 + [group[1][2]] * 2 + [group[2][2]] * 2):
                valid = False
                break
        if valid:
            groups.append(group)
    if len(groups) != needed:
        raise RuntimeError(f"INSUFFICIENT_STABLE_DISJOINT_SINGLE_TOKEN_LEXEMES:{len(groups)}:{needed}")
    return groups


def family_prompt(partition: str, family_index: int, target: str, content: str) -> str:
    protocol = (
        "/no_think\n"
        "Read six opaque content items by position: edge1-source, edge1-destination, "
        "edge2-source, edge2-destination, query-source, query-destination. "
        "Treat the edge relation as transitive across exactly two edges. "
        "Compute whether the two-edge path runs from query-source to query-destination, "
        "runs in the reverse query direction, or occurs in neither direction. "
    )
    if partition == "BASIS":
        tail = "Keep the resulting relation state internal; do not name a class."
    else:
        mapping = ROTATIONS[family_index % len(ROTATIONS)]
        tail = (
            "Opaque code table: forward-path=" + mapping["AFFIRMATIVE"]
            + "; reverse-path=" + mapping["NEGATIVE"]
            + "; neither-direction=" + mapping["NEUTRAL"]
            + ". Return only the code."
        )
    return protocol + tail + " Content stream:" + content


def produce(tokenizer_json: Path) -> dict[str, Any]:
    tokenizer_bytes = tokenizer_json.read_bytes()
    tokenizer = Tokenizer.from_file(str(tokenizer_json))
    groups = select_groups(tokenizer)
    partitions: dict[str, list[dict[str, Any]]] = {name: [] for name in gate.PARTITIONS}
    group_cursor = 0
    selected_lexemes: dict[str, list[dict[str, Any]]] = {name: [] for name in gate.PARTITIONS}

    for partition in gate.PARTITIONS:
        for family_index in range(FAMILY_COUNTS[partition]):
            group = groups[group_cursor]
            group_cursor += 1
            family_id = f"{partition.lower()}-abstract-relational-{family_index}"
            selected_lexemes[partition].append(
                {
                    "family_id": family_id,
                    "token_ids": [x[0] for x in group],
                    "lexemes": [x[2] for x in group],
                }
            )
            for target in gate.TARGETS:
                ids, content = _sequence(group, target)
                prompt = family_prompt(partition, family_index, target, content)
                # Defense-in-depth: producer itself refuses leakage before the gate sees it.
                leaked = set(gate.words(prompt)) & (set(x.casefold() for x in gate.TARGETS) | set(gate.PROXY_LEXEMES))
                if leaked:
                    raise RuntimeError("MODEL_FACING_PROXY_LEAK:" + ",".join(sorted(leaked)))
                if tokenizer.encode(content).ids != ids:
                    raise RuntimeError("CONTENT_TOKENIZATION_DRIFT")
                partitions[partition].append(
                    {
                        "row_id": f"{family_id}:{target.lower()}",
                        "family_id": family_id,
                        "semantic_target": target,
                        "output_code_identity": (
                            ROTATIONS[family_index % len(ROTATIONS)][target]
                            if partition in gate.EVAL_SPLITS
                            else None
                        ),
                        "prompt": prompt,
                        "prompt_sha256": sha_text(prompt),
                        "content_text": content,
                        "content_token_ids": ids,
                        "model_facing_target_identity_exposed": False,
                        "model_facing_explicit_semantic_labels": False,
                    }
                )

    payload = {
        "schema": gate.SCHEMA,
        "producer_schema": SCHEMA,
        "tokenizer_identity": {
            "tokenizer_json_sha256": hashlib.sha256(tokenizer_bytes).hexdigest(),
            "content_token_ids_recomputed_from_exact_tokenizer": True,
        },
        "partitions": partitions,
        "producer_metadata": {
            "latent_relation": "TWO_EDGE_QUERY_DIRECTION_TERNARY_STATE",
            "model_facing_canonical_semantic_labels": False,
            "basis_family_count": FAMILY_COUNTS["BASIS"],
            "calibration_family_count": FAMILY_COUNTS["CALIBRATION"],
            "holdout_family_count": FAMILY_COUNTS["HOLDOUT"],
            "selected_lexemes": selected_lexemes,
        },
    }
    receipt = gate.adjudicate(payload)
    if receipt.get("pass") is not True:
        raise RuntimeError("SELF_DECONFOUND_GATE_FAILED:" + "|".join(receipt.get("failures", [])))
    return {"payload": payload, "deconfound_receipt": receipt}


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
