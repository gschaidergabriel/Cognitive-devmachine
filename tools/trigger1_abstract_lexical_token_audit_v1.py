#!/usr/bin/env python3
"""Mechanically produce the lexical-audit evidence required by canonical Trigger-1 v11.

The canonical #1941 gate deliberately requires a frozen lexical audit but does not compute
one. This tool does. It rejects a design unless:

* AFFIRMATIVE/NEGATIVE/NEUTRAL and conservative semantic/compliance synonyms are absent
  from model-facing prompts;
* semantic target exists only as evaluator metadata;
* every matched family contains one row per target with exactly the same normalized-word
  multiset and exact tokenizer-token-id multiset (target information can only live in
  relation/order/structure);
* BASIS, CALIBRATION and HOLDOUT use disjoint content lexemes, content token IDs and family
  identities; and
* CALIBRATION and HOLDOUT independently implement an exact target x opaque-code Latin square.

This is source/deterministic design evidence only; it never runs a model or opens a holdout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any

INPUT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_LEXICAL_TOKEN_DESIGN/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_LEXICAL_AUDIT_RECEIPT/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
PARTITIONS = ("BASIS", "CALIBRATION", "HOLDOUT")
EVAL_PARTITIONS = ("CALIBRATION", "HOLDOUT")
CODES = ("A", "B", "C")
WORD_RE = re.compile(r"[A-Za-z0-9_]+")

SEMANTIC_PROXY_LEXICON = frozenset(
    {
        "affirmative", "negative", "neutral", "yes", "no", "agree", "agreement",
        "disagree", "disagreement", "approve", "approval", "approved", "accept",
        "accepted", "reject", "rejected", "refuse", "refused", "permit", "permission",
        "allow", "allowed", "deny", "denied", "grant", "granted", "proceed", "proceeding",
        "decline", "declining", "defer", "deferred", "endorse", "endorsing", "oppose",
        "opposing", "support", "supporting", "favor", "favour", "forbid", "forbidden",
        "mandatory", "compliant", "compliance", "violate", "violation", "pass", "fail",
        "pending", "undecided", "unresolved", "selection", "selecting", "adopt", "adoption",
    }
)
FIXED_SCAFFOLD = frozenset(
    {
        "no_think", "internally", "represent", "encode", "derive", "compute", "return",
        "output", "emit", "only", "one", "token", "code", "symbol", "the", "a", "an",
        "and", "or", "of", "to", "from", "with", "without", "in", "on", "for", "this",
        "that", "is", "are", "be", "being", "it", "its", "as", "by", "then", "now",
        "do", "not", "read", "six", "content", "items", "item", "position", "state",
    }
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def words(text: str) -> list[str]:
    return [x.casefold() for x in WORD_RE.findall(text)]


def content_words(text: str) -> list[str]:
    return [x for x in words(text) if x not in FIXED_SCAFFOLD and len(x) > 1]


def _fail(reason: str) -> dict[str, Any]:
    core = {
        "schema": RECEIPT_SCHEMA,
        "pass": False,
        "failures": [reason],
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def _normalize(raw: Any, partition: str, index: int) -> dict[str, Any]:
    p = f"{partition}_ROW_{index}"
    if not isinstance(raw, dict):
        raise ValueError(f"{p}_OBJECT_REQUIRED")
    row_id = raw.get("row_id")
    family_id = raw.get("family_id")
    target = str(raw.get("semantic_target") or "").upper()
    prompt = raw.get("prompt")
    content = raw.get("content_text")
    token_ids = raw.get("content_token_ids")
    if not isinstance(row_id, str) or not row_id:
        raise ValueError(f"{p}_ROW_ID_REQUIRED")
    if not isinstance(family_id, str) or not family_id:
        raise ValueError(f"{p}_FAMILY_ID_REQUIRED")
    if target not in TARGETS:
        raise ValueError(f"{p}_TARGET_INVALID")
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"{p}_PROMPT_REQUIRED")
    if not isinstance(content, str) or not content or content not in prompt:
        raise ValueError(f"{p}_CONTENT_TEXT_MUST_BE_PROMPT_SUBSTRING")
    if not isinstance(token_ids, list) or not token_ids or any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in token_ids):
        raise ValueError(f"{p}_CONTENT_TOKEN_IDS_REQUIRED")
    if raw.get("model_facing_target_identity_exposed") is not False:
        raise ValueError(f"{p}_TARGET_IDENTITY_MUST_BE_EVALUATOR_ONLY")
    if raw.get("model_facing_explicit_semantic_labels") is not False:
        raise ValueError(f"{p}_EXPLICIT_SEMANTIC_LABELS_MUST_BE_FALSE")
    if raw.get("prompt_sha256") != sha_text(prompt):
        raise ValueError(f"{p}_PROMPT_SHA256_MISMATCH")
    leaked = sorted(set(words(prompt)) & SEMANTIC_PROXY_LEXICON)
    if leaked:
        raise ValueError(f"{p}_SEMANTIC_PROXY_LEAK:" + ",".join(leaked))
    code = raw.get("output_code_identity")
    if partition in EVAL_PARTITIONS:
        code = str(code or "").upper()
        if code not in CODES:
            raise ValueError(f"{p}_OUTPUT_CODE_INVALID")
    elif code not in (None, ""):
        raise ValueError(f"{p}_BASIS_OUTPUT_CODE_MUST_BE_ABSENT")
    else:
        code = None
    cw = content_words(content)
    if not cw:
        raise ValueError(f"{p}_CONTENT_LEXEMES_REQUIRED")
    return {
        "row_id": row_id,
        "family_id": family_id,
        "semantic_target": target,
        "output_code_identity": code,
        "prompt_sha256": sha_text(prompt),
        "content_text_sha256": sha_text(content),
        "content_words": cw,
        "content_token_ids": list(token_ids),
        "content_token_ids_sha256": canonical_sha(token_ids),
    }


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        return _fail("INPUT_SCHEMA_INVALID")
    tokenizer = payload.get("tokenizer_identity")
    if not isinstance(tokenizer, dict) or not is_sha(tokenizer.get("tokenizer_json_sha256")):
        return _fail("EXACT_TOKENIZER_JSON_SHA256_REQUIRED")
    if tokenizer.get("content_token_ids_recomputed_from_exact_tokenizer") is not True:
        return _fail("TOKENIZER_RECOMPUTATION_ATTESTATION_REQUIRED")
    if payload.get("frozen_before_holdout") is not True:
        return _fail("LEXICAL_AUDIT_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    raw_parts = payload.get("partitions")
    if not isinstance(raw_parts, dict) or set(raw_parts) != set(PARTITIONS):
        return _fail("EXACT_PARTITION_SET_REQUIRED")

    try:
        rows = {
            part: [_normalize(x, part, i) for i, x in enumerate(raw_parts[part])]
            for part in PARTITIONS
        }
    except (TypeError, ValueError) as exc:
        return _fail(str(exc))

    failures: list[str] = []
    summaries: dict[str, dict[str, Any]] = {}
    for part in PARTITIONS:
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows[part]:
            by_family[row["family_id"]].append(row)
        minimum = 6 if part == "BASIS" else 3
        if len(by_family) < minimum:
            failures.append(f"{part}_MIN_MATCHED_FAMILIES_REQUIRED:{minimum}")
        for family, family_rows in sorted(by_family.items()):
            if len(family_rows) != 3 or {x["semantic_target"] for x in family_rows} != set(TARGETS):
                failures.append(f"{part}_FAMILY_NOT_EXACT_TARGET_TRIPLET:{family}")
                continue
            wc = [Counter(x["content_words"]) for x in family_rows]
            tc = [Counter(x["content_token_ids"]) for x in family_rows]
            if len({tuple(sorted(x.items())) for x in wc}) != 1:
                failures.append(f"{part}_FAMILY_WORD_MULTISET_NOT_COUNTERBALANCED:{family}")
            if len({tuple(sorted(x.items())) for x in tc}) != 1:
                failures.append(f"{part}_FAMILY_TOKEN_MULTISET_NOT_COUNTERBALANCED:{family}")
            if len({tuple(x["content_token_ids"]) for x in family_rows}) != 3:
                failures.append(f"{part}_FAMILY_TARGET_SEQUENCES_NOT_DISTINCT:{family}")
            if part in EVAL_PARTITIONS and {x["output_code_identity"] for x in family_rows} != set(CODES):
                failures.append(f"{part}_FAMILY_CODE_ROTATION_INVALID:{family}")
        if part in EVAL_PARTITIONS:
            grid = Counter((x["semantic_target"], x["output_code_identity"]) for x in rows[part])
            expected = {(t, c) for t in TARGETS for c in CODES}
            if set(grid) != expected or len(set(grid.values())) != 1:
                failures.append(f"{part}_TARGET_X_OUTPUT_CODE_NOT_BALANCED")
        summaries[part] = {
            "row_count": len(rows[part]),
            "family_count": len(by_family),
            "family_ids": sorted(by_family),
            "word_set": sorted({w for x in rows[part] for w in x["content_words"]}),
            "token_set": sorted({tid for x in rows[part] for tid in x["content_token_ids"]}),
            "rows_sha256": canonical_sha(
                [
                    {k: x[k] for k in ("row_id", "family_id", "semantic_target", "output_code_identity", "prompt_sha256", "content_text_sha256", "content_token_ids_sha256")}
                    for x in sorted(rows[part], key=lambda z: z["row_id"])
                ]
            ),
        }

    for i, left in enumerate(PARTITIONS):
        for right in PARTITIONS[i + 1 :]:
            if set(summaries[left]["word_set"]) & set(summaries[right]["word_set"]):
                failures.append(f"{left}_{right}_CONTENT_LEXEME_OVERLAP")
            if set(summaries[left]["token_set"]) & set(summaries[right]["token_set"]):
                failures.append(f"{left}_{right}_CONTENT_TOKEN_OVERLAP")
            if set(summaries[left]["family_ids"]) & set(summaries[right]["family_ids"]):
                failures.append(f"{left}_{right}_SCENARIO_FAMILY_OVERLAP")

    lexical_disjoint = not any("CONTENT_LEXEME_OVERLAP" in x or "CONTENT_TOKEN_OVERLAP" in x for x in failures)
    scenario_disjoint = not any("SCENARIO_FAMILY_OVERLAP" in x for x in failures)
    latin = not any("OUTPUT_CODE" in x or "CODE_ROTATION" in x for x in failures)
    multiset = not any("MULTISET_NOT_COUNTERBALANCED" in x for x in failures)
    core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "tokenizer_json_sha256": tokenizer["tokenizer_json_sha256"],
        "semantic_proxy_lexicon_sha256": canonical_sha(sorted(SEMANTIC_PROXY_LEXICON)),
        "fixed_scaffold_sha256": canonical_sha(sorted(FIXED_SCAFFOLD)),
        "partition_receipts": {
            p: {k: v for k, v in summaries[p].items() if k not in ("word_set", "token_set", "family_ids")}
            for p in PARTITIONS
        },
        "basis_model_facing_canonical_labels_absent": True,
        "holdout_model_facing_canonical_labels_absent": True,
        "basis_holdout_lexically_disjoint": lexical_disjoint,
        "basis_holdout_scenario_disjoint": scenario_disjoint,
        "semantic_synonym_lexicon_disjoint": not any("SEMANTIC_PROXY_LEAK" in x for x in failures),
        "semantic_target_evaluator_metadata_only": True,
        "full_three_by_three_target_x_output_code": latin,
        "per_scenario_target_and_code_rotation": latin,
        "within_family_word_and_token_multiset_counterbalanced": multiset,
        "lexical_audit_frozen_before_holdout": True,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "evidence_boundary": "Deterministic tokenizer-bound lexical/scenario/code audit only; no model or holdout execution.",
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = audit(payload)
    except (OSError, json.JSONDecodeError) as exc:
        receipt = _fail(f"INPUT_FILE_INVALID:{type(exc).__name__}")
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
