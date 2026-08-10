#!/usr/bin/env python3
from __future__ import annotations

"""Small reproducible collision/coverage ablation for V13 semantic keys.

This is a hand-curated multilingual falsifier, not a representative language benchmark.
It exists to catch catastrophic key loss/collision in the hot exact-key plane before larger
real-corpus retrieval evaluation.
"""

from collections import defaultdict
import json
from pathlib import Path
import platform
import re
import sqlite3
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "research_entity" / "runtime"
sys.path.insert(0, str(RUNTIME))
from semantic_retrieval_runtime_v13 import NORMALIZER_VERSION, norm  # noqa: E402

OLD_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


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


def metrics(normalizer) -> dict:
    groups: dict[str, list[str]] = defaultdict(list)
    for term in TERMS:
        groups[normalizer(term)].append(term)
    false_collisions = {
        key: values
        for key, values in groups.items()
        if len({canonical_identity(value) for value in values}) > 1
    }
    empty_terms = [term for term in TERMS if not normalizer(term)]
    # If every normalized key maps to all records sharing that key and tie-breaking is fixed,
    # exactly one canonical target per collision group can be top-1 correct.
    top1_upper_bound = len(groups) / len(TERMS)
    return {
        "terms": len(TERMS),
        "unique_keys": len(groups),
        "nonempty_key_rate": (len(TERMS) - len(empty_terms)) / len(TERMS),
        "false_collision_group_count": len(false_collisions),
        "false_collision_term_count": sum(
            len({canonical_identity(value) for value in values})
            for values in false_collisions.values()
        ),
        "top1_upper_bound_under_exact_key_collision": top1_upper_bound,
        "empty_terms": empty_terms,
        "false_collisions": false_collisions,
    }


def main() -> int:
    old = metrics(old_ascii_norm)
    current = metrics(norm)
    result = {
        "schema_version": "clay.unifieddb.v13_unicode_ablation.v1",
        "benchmark_class": "HAND_CURATED_MULTILINGUAL_KEY_COLLISION_FALSIFIER",
        "normalizer_version": NORMALIZER_VERSION,
        "baseline": old,
        "candidate": current,
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
        },
        "acceptance": {
            "candidate_no_empty_keys": not current["empty_terms"],
            "candidate_no_false_collision_groups": current["false_collision_group_count"] == 0,
            "candidate_top1_upper_bound": current["top1_upper_bound_under_exact_key_collision"],
            "candidate_improves_over_ascii": (
                current["top1_upper_bound_under_exact_key_collision"]
                > old["top1_upper_bound_under_exact_key_collision"]
            ),
        },
        "limitations": [
            "Hand-curated terms are a falsifier, not a representative German or multilingual corpus.",
            "This measures normalization collision/coverage only, not semantic ranking, GraphRAG quality or downstream answer correctness.",
            "NFKC compatibility folding must remain versioned and separately evaluated where compatibility distinctions are semantically meaningful.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not all(result["acceptance"].values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
