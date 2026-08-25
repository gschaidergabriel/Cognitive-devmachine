#!/usr/bin/env python3
"""Fail-closed abstraction/deconfound gate for Trigger-1 semantic J-Space claims.

This gate is intentionally stricter than "the words AFFIRMATIVE/NEGATIVE/NEUTRAL do not
appear in the prompt".  A semantic-state candidate is only deconfounded when the frozen
model-facing design makes simple lexical/compliance shortcuts unavailable:

* canonical class names and a conservative compliance/decision proxy lexicon are absent;
* every matched family contains all three evaluator-side targets;
* within each family, the *same lexical multiset* and the *same model-token multiset* are
  used for all three targets (only relation/order/structure may differ);
* BASIS, CALIBRATION and HOLDOUT use mutually disjoint content vocabularies at both the
  normalized-word and exact-token-id levels;
* CALIBRATION and HOLDOUT independently counterbalance target -> opaque output code as an
  exact 3x3 factorial; and
* all text/token/family identities are digest-bound for later runtime/preregistration joins.

The class label is evaluator metadata only.  This module never runs a model and cannot
mint J-Space/model/HCU/EntityOS/training/canonical-semantics credit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_DECONFOUND_INPUT/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_DECONFOUND_RECEIPT/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
EVAL_SPLITS = ("CALIBRATION", "HOLDOUT")
PARTITIONS = ("BASIS", "CALIBRATION", "HOLDOUT")
CODES = ("A", "B", "C")

# This is deliberately broader than canonical labels.  The point is to reject the exact
# shortcut family that motivated the current blocker, not to pretend a finite synonym list
# can prove semantics by itself.  The stronger multiset/cross-split invariants below do the
# main causal deconfounding work.
PROXY_LEXEMES = frozenset(
    {
        "affirmative", "negative", "neutral", "yes", "no", "agree", "agreement",
        "disagree", "disagreement", "approve", "approval", "approved", "disapprove",
        "accept", "accepted", "accepting", "reject", "rejected", "rejecting", "refuse",
        "refused", "refusing", "permit", "permission", "allow", "allowed", "disallow",
        "deny", "denied", "grant", "granted", "proceed", "proceeding", "decline",
        "declining", "defer", "deferred", "abstain", "abstention", "endorse", "endorsing",
        "oppose", "opposing", "support", "supporting", "favor", "favour", "forbid",
        "forbidden", "mandatory", "compliant", "compliance", "violate", "violation",
        "pass", "fail", "pending", "undecided", "unresolved", "commitment", "commit",
        "selection", "selecting", "adopt", "adoption", "apply", "applying",
    }
)

# Fixed protocol/function-word scaffold may occur in all partitions.  Content deconfounding
# is computed after this code-owned list, not a caller-controlled stop list, is removed.
SCAFFOLD = frozenset(
    {
        "no_think", "internally", "represent", "encode", "derive", "return", "output",
        "emit", "only", "one", "token", "code", "symbol", "the", "a", "an", "and", "or",
        "of", "to", "from", "with", "without", "in", "on", "for", "this", "that", "is",
        "are", "be", "being", "it", "its", "as", "by", "then", "now", "do", "not",
    }
)
WORD_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


class DeconfoundError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def words(text: str) -> list[str]:
    return [w.casefold() for w in WORD_RE.findall(text)]


def content_words(text: str) -> list[str]:
    return [w for w in words(text) if w not in SCAFFOLD and len(w) > 1]


def _normalize_row(raw: Any, partition: str, index: int) -> dict[str, Any]:
    prefix = f"{partition}_ROW_{index}"
    if not isinstance(raw, dict):
        raise DeconfoundError(f"{prefix}_OBJECT_REQUIRED")
    row_id = raw.get("row_id")
    family_id = raw.get("family_id")
    target = str(raw.get("semantic_target") or "").strip().upper()
    prompt = raw.get("prompt")
    content_text = raw.get("content_text")
    token_ids = raw.get("content_token_ids")
    if not isinstance(row_id, str) or not row_id:
        raise DeconfoundError(f"{prefix}_ROW_ID_REQUIRED")
    if not isinstance(family_id, str) or not family_id:
        raise DeconfoundError(f"{prefix}_FAMILY_ID_REQUIRED")
    if target not in TARGETS:
        raise DeconfoundError(f"{prefix}_TARGET_INVALID")
    if not isinstance(prompt, str) or not prompt.strip():
        raise DeconfoundError(f"{prefix}_PROMPT_REQUIRED")
    if not isinstance(content_text, str) or not content_text.strip() or content_text not in prompt:
        raise DeconfoundError(f"{prefix}_CONTENT_TEXT_MUST_BE_NONEMPTY_PROMPT_SUBSTRING")
    if not isinstance(token_ids, list) or not token_ids or any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in token_ids):
        raise DeconfoundError(f"{prefix}_CONTENT_TOKEN_IDS_REQUIRED")
    if raw.get("model_facing_target_identity_exposed") is not False:
        raise DeconfoundError(f"{prefix}_TARGET_IDENTITY_EXPOSURE_MUST_BE_FALSE")
    if raw.get("model_facing_explicit_semantic_labels") is not False:
        raise DeconfoundError(f"{prefix}_EXPLICIT_SEMANTIC_LABELS_MUST_BE_FALSE")
    declared = raw.get("prompt_sha256")
    if declared is not None and declared != sha_text(prompt):
        raise DeconfoundError(f"{prefix}_PROMPT_SHA256_MISMATCH")

    all_words = set(words(prompt))
    leaked = sorted(all_words & (set(x.casefold() for x in TARGETS) | set(PROXY_LEXEMES)))
    if leaked:
        raise DeconfoundError(f"{prefix}_SEMANTIC_OR_COMPLIANCE_PROXY_LEAK:{','.join(leaked)}")

    output_code = raw.get("output_code_identity")
    if partition in EVAL_SPLITS:
        output_code = str(output_code or "").strip().upper()
        if output_code not in CODES:
            raise DeconfoundError(f"{prefix}_OUTPUT_CODE_INVALID")
    elif output_code not in (None, ""):
        raise DeconfoundError(f"{prefix}_BASIS_MUST_NOT_BIND_OUTPUT_CODE")
    else:
        output_code = None

    cw = content_words(content_text)
    if not cw:
        raise DeconfoundError(f"{prefix}_NO_CONTENT_LEXEMES_AFTER_FIXED_SCAFFOLD")
    return {
        "row_id": row_id,
        "family_id": family_id,
        "semantic_target": target,
        "output_code_identity": output_code,
        "prompt": prompt,
        "prompt_sha256": sha_text(prompt),
        "content_text": content_text,
        "content_text_sha256": sha_text(content_text),
        "content_words": cw,
        "content_token_ids": list(token_ids),
        "content_token_ids_sha256": canonical_sha(token_ids),
        "model_facing_target_identity_exposed": False,
        "model_facing_explicit_semantic_labels": False,
    }


def _partition_checks(partition: str, rows: list[dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    if len(rows) < 9 or len(rows) % 3:
        failures.append(f"{partition}_ROW_COUNT_MUST_BE_MULTIPLE_OF_THREE_AND_AT_LEAST_NINE")
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[row["family_id"]].append(row)
    if len(by_family) < 3:
        failures.append(f"{partition}_AT_LEAST_THREE_MATCHED_FAMILIES_REQUIRED")

    family_receipts: list[dict[str, Any]] = []
    for family_id, family_rows in sorted(by_family.items()):
        if len(family_rows) != 3 or {r["semantic_target"] for r in family_rows} != set(TARGETS):
            failures.append(f"{partition}_FAMILY_NOT_EXACT_TARGET_TRIPLET:{family_id}")
            continue
        word_counts = {r["semantic_target"]: Counter(r["content_words"]) for r in family_rows}
        token_counts = {r["semantic_target"]: Counter(r["content_token_ids"]) for r in family_rows}
        if len({tuple(sorted(c.items())) for c in word_counts.values()}) != 1:
            failures.append(f"{partition}_FAMILY_LEXICAL_MULTISET_NOT_COUNTERBALANCED:{family_id}")
        if len({tuple(sorted(c.items())) for c in token_counts.values()}) != 1:
            failures.append(f"{partition}_FAMILY_MODEL_TOKEN_MULTISET_NOT_COUNTERBALANCED:{family_id}")
        # Identical sequences would carry no target-specific structural information at all.
        if len({tuple(r["content_token_ids"]) for r in family_rows}) != 3:
            failures.append(f"{partition}_FAMILY_TARGET_SEQUENCES_MUST_BE_DISTINCT:{family_id}")
        if partition in EVAL_SPLITS:
            codes = {r["output_code_identity"] for r in family_rows}
            if codes != set(CODES):
                failures.append(f"{partition}_FAMILY_OUTPUT_CODE_ROTATION_INVALID:{family_id}")
        family_receipts.append(
            {
                "family_id": family_id,
                "row_ids": sorted(r["row_id"] for r in family_rows),
                "word_multiset_sha256": canonical_sha(sorted(Counter(family_rows[0]["content_words"]).items())),
                "token_multiset_sha256": canonical_sha(sorted(Counter(family_rows[0]["content_token_ids"]).items())),
            }
        )

    if partition in EVAL_SPLITS:
        observed = Counter((r["semantic_target"], r["output_code_identity"]) for r in rows)
        counts = list(observed.values())
        expected_cells = {(t, c) for t in TARGETS for c in CODES}
        if set(observed) != expected_cells or not counts or len(set(counts)) != 1:
            failures.append(f"{partition}_TARGET_X_OUTPUT_CODE_NOT_EXACTLY_BALANCED")

    return {
        "partition": partition,
        "row_count": len(rows),
        "family_count": len(by_family),
        "family_receipts": family_receipts,
        "content_word_set": sorted({w for r in rows for w in r["content_words"]}),
        "content_token_id_set": sorted({x for r in rows for x in r["content_token_ids"]}),
        "rows_sha256": canonical_sha(
            [
                {
                    "row_id": r["row_id"],
                    "family_id": r["family_id"],
                    "semantic_target": r["semantic_target"],
                    "output_code_identity": r["output_code_identity"],
                    "prompt_sha256": r["prompt_sha256"],
                    "content_text_sha256": r["content_text_sha256"],
                    "content_token_ids_sha256": r["content_token_ids_sha256"],
                }
                for r in sorted(rows, key=lambda x: x["row_id"])
            ]
        ),
    }


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return _failure("INPUT_SCHEMA_INVALID")
    tokenizer = payload.get("tokenizer_identity")
    if not isinstance(tokenizer, dict) or not is_sha(tokenizer.get("tokenizer_json_sha256")):
        return _failure("EXACT_TOKENIZER_JSON_SHA256_REQUIRED")
    if tokenizer.get("content_token_ids_recomputed_from_exact_tokenizer") is not True:
        return _failure("EXACT_TOKENIZER_RECOMPUTATION_ATTESTATION_REQUIRED")

    raw_parts = payload.get("partitions")
    if not isinstance(raw_parts, dict) or set(raw_parts) != set(PARTITIONS):
        return _failure("EXACT_BASIS_CALIBRATION_HOLDOUT_PARTITIONS_REQUIRED")

    normalized: dict[str, list[dict[str, Any]]] = {}
    try:
        for partition in PARTITIONS:
            raw_rows = raw_parts[partition]
            if not isinstance(raw_rows, list):
                raise DeconfoundError(f"{partition}_ROWS_LIST_REQUIRED")
            normalized[partition] = [_normalize_row(row, partition, i) for i, row in enumerate(raw_rows)]
    except DeconfoundError as exc:
        return _failure(str(exc))

    summaries = {p: _partition_checks(p, normalized[p], failures) for p in PARTITIONS}

    # Strong lexical disjointness across derivation, calibration and unopened/fresh holdout.
    for i, left in enumerate(PARTITIONS):
        for right in PARTITIONS[i + 1 :]:
            w_overlap = set(summaries[left]["content_word_set"]) & set(summaries[right]["content_word_set"])
            t_overlap = set(summaries[left]["content_token_id_set"]) & set(summaries[right]["content_token_id_set"])
            if w_overlap:
                failures.append(f"{left}_{right}_CONTENT_LEXEME_OVERLAP:" + ",".join(sorted(w_overlap)[:12]))
            if t_overlap:
                failures.append(f"{left}_{right}_MODEL_TOKEN_ID_OVERLAP:" + ",".join(map(str, sorted(t_overlap)[:12])))

    # Family identities cannot cross partitions either; this closes a simple family-id proxy.
    family_sets = {p: {r["family_id"] for r in normalized[p]} for p in PARTITIONS}
    for i, left in enumerate(PARTITIONS):
        for right in PARTITIONS[i + 1 :]:
            if family_sets[left] & family_sets[right]:
                failures.append(f"{left}_{right}_FAMILY_ID_OVERLAP")

    core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "tokenizer_json_sha256": tokenizer["tokenizer_json_sha256"],
        "proxy_lexicon_sha256": canonical_sha(sorted(PROXY_LEXEMES)),
        "fixed_scaffold_sha256": canonical_sha(sorted(SCAFFOLD)),
        "partition_receipts": {
            p: {
                k: v
                for k, v in summaries[p].items()
                if k not in ("content_word_set", "content_token_id_set")
            }
            for p in PARTITIONS
        },
        "label_free": not any("SEMANTIC_LABEL" in x for x in failures),
        "compliance_proxy_free": not any("PROXY_LEAK" in x for x in failures),
        "within_family_lexical_counterbalance": not any("LEXICAL_MULTISET" in x for x in failures),
        "within_family_token_counterbalance": not any("MODEL_TOKEN_MULTISET" in x for x in failures),
        "cross_partition_lexically_disjoint": not any("CONTENT_LEXEME_OVERLAP" in x for x in failures),
        "cross_partition_model_token_disjoint": not any("MODEL_TOKEN_ID_OVERLAP" in x for x in failures),
        "evaluation_code_counterbalanced": not any("OUTPUT_CODE" in x for x in failures),
        "pass": not failures,
        "failures": sorted(set(failures)),
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS establishes a frozen label/proxy-free, within-family lexical+token counterbalanced, "
            "cross-partition lexically disjoint experiment design. It does not establish that the model "
            "actually represents the intended abstract state; that requires bound causal runtime evidence."
        ),
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def _failure(reason: str) -> dict[str, Any]:
    core = {
        "schema": RECEIPT_SCHEMA,
        "pass": False,
        "failures": [reason],
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "training_credit": False,
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = adjudicate(payload)
    except (OSError, json.JSONDecodeError) as exc:
        receipt = _failure(f"INPUT_FILE_INVALID:{type(exc).__name__}")
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
