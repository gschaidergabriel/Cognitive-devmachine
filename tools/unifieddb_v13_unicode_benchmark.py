#!/usr/bin/env python3
from __future__ import annotations

"""Reproducible collision/coverage ablation for V13 semantic keys.

The hand-curated fixture is a hard falsifier. A second pass scans versioned repository text
for non-ASCII tokens to measure actual Clay corpus exposure. Neither pass is a semantic
ranking benchmark or evidence of universal database superiority.
"""

from collections import defaultdict
import json
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "research_entity" / "runtime"
sys.path.insert(0, str(RUNTIME))
from semantic_retrieval_runtime_v13 import NORMALIZER_VERSION, norm  # noqa: E402

OLD_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
UNICODE_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
TEXT_SUFFIXES = {
    ".clay", ".json", ".jsonl", ".md", ".py", ".sql", ".txt", ".toml",
    ".yaml", ".yml",
}


def old_ascii_norm(value: object) -> str:
    return " ".join(match.group(0).lower() for match in OLD_TOKEN_RE.finditer(str(value)))


TERMS = (
    "Öl", "Él", "Ärger", "Arger", "Über", "Uber", "Größe", "Grosse", "Straße",
    "mañana", "manana", "São", "Sao", "Łódź", "Lodz", "北京", "東京", "Москва",
    "Moskva", "Český", "Cesky", "français", "francais", "naïve", "naive", "Résumé",
    "Resume", "İstanbul", "Istanbul", "Ångström", "Angstrom",
)


def canonical_identity(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def collision_metrics(terms: tuple[str, ...] | list[str], normalizer) -> dict:
    groups: dict[str, list[str]] = defaultdict(list)
    for term in terms:
        groups[normalizer(term)].append(term)
    false_collisions = {
        key: values
        for key, values in groups.items()
        if len({canonical_identity(value) for value in values}) > 1
    }
    empty_terms = [term for term in terms if not normalizer(term)]
    top1_upper_bound = len(groups) / len(terms) if terms else 1.0
    return {
        "terms": len(terms),
        "unique_keys": len(groups),
        "nonempty_key_rate": ((len(terms) - len(empty_terms)) / len(terms)) if terms else 1.0,
        "false_collision_group_count": len(false_collisions),
        "false_collision_term_count": sum(
            len({canonical_identity(value) for value in values})
            for values in false_collisions.values()
        ),
        "top1_upper_bound_under_exact_key_collision": top1_upper_bound,
        "empty_terms": empty_terms[:50],
        "false_collisions": dict(list(false_collisions.items())[:50]),
    }


def repo_unicode_risk_scan() -> dict:
    """Measure key-loss/collision exposure over tracked non-ASCII repository tokens."""
    try:
        tracked = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files"], text=True, timeout=10
        ).splitlines()
    except Exception as exc:
        return {"available": False, "reason": type(exc).__name__}

    canonical_to_examples: dict[str, set[str]] = defaultdict(set)
    scanned_files = 0
    skipped_large = 0
    for relative in tracked:
        path = ROOT / relative
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            if path.stat().st_size > 2_000_000:
                skipped_large += 1
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        scanned_files += 1
        for token in UNICODE_TOKEN_RE.findall(text):
            if token.isascii():
                continue
            canonical_to_examples[canonical_identity(token)].add(token)

    representatives = [sorted(values)[0] for _, values in sorted(canonical_to_examples.items())]
    baseline = collision_metrics(representatives, old_ascii_norm)
    candidate = collision_metrics(representatives, norm)

    destructive_examples = []
    for term in representatives:
        old_key = old_ascii_norm(term)
        new_key = norm(term)
        if old_key != new_key:
            destructive_examples.append({"term": term, "ascii_key": old_key, "unicode_key": new_key})
            if len(destructive_examples) >= 50:
                break

    return {
        "available": True,
        "scanned_text_files": scanned_files,
        "skipped_large_text_files": skipped_large,
        "unique_non_ascii_canonical_tokens": len(representatives),
        "baseline": baseline,
        "candidate": candidate,
        "ascii_vs_unicode_changed_key_example_count_capped": len(destructive_examples),
        "changed_key_examples": destructive_examples,
        "interpretation_boundary": (
            "Repository scan measures structural key-loss/collision exposure only. A changed key is not "
            "automatically a semantic error; held-out retrieval ground truth remains required."
        ),
    }


def main() -> int:
    old = collision_metrics(list(TERMS), old_ascii_norm)
    current = collision_metrics(list(TERMS), norm)
    repo_scan = repo_unicode_risk_scan()
    acceptance = {
        "candidate_no_empty_keys": not current["empty_terms"],
        "candidate_no_false_collision_groups": current["false_collision_group_count"] == 0,
        "candidate_top1_upper_bound_is_one": current["top1_upper_bound_under_exact_key_collision"] == 1.0,
        "candidate_improves_over_ascii": (
            current["top1_upper_bound_under_exact_key_collision"]
            > old["top1_upper_bound_under_exact_key_collision"]
        ),
    }
    if repo_scan.get("available"):
        acceptance["repo_candidate_no_empty_keys"] = not repo_scan["candidate"]["empty_terms"]
        acceptance["repo_candidate_no_false_collision_groups"] = (
            repo_scan["candidate"]["false_collision_group_count"] == 0
        )

    result = {
        "schema_version": "clay.unifieddb.v13_unicode_ablation.v2",
        "benchmark_class": "MULTILINGUAL_KEY_COLLISION_FALSIFIER_PLUS_REAL_REPO_RISK_SCAN",
        "normalizer_version": NORMALIZER_VERSION,
        "hand_curated": {"baseline": old, "candidate": current},
        "real_repo_unicode_risk_scan": repo_scan,
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
        },
        "acceptance": acceptance,
        "limitations": [
            "Hand-curated terms are a falsifier, not a representative German or multilingual corpus.",
            "Repository token scan has no relevance labels and therefore does not measure semantic ranking quality.",
            "This measures normalization collision/coverage only, not GraphRAG quality or downstream answer correctness.",
            "NFKC compatibility folding must remain versioned and separately evaluated where compatibility distinctions are semantically meaningful.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(acceptance.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
