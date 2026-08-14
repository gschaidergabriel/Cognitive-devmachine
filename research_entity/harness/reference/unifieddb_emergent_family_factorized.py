from __future__ import annotations

"""EAP-FAMILY-F1: explicit possibility-family factorization above current EAP.

This is a derived model-input selection layer, not a database and not truth/effect authority.
It preserves the current EAP traversal and incremental dependency-maintenance semantics, then
prevents multiple physical/state bindings of the same explicitly typed possibility family
from consuming the bounded ActiveAssembly budget.

Safety boundary:
- family identity is used ONLY when a selected row value explicitly carries
  `possibility_family_id` (configurable key);
- missing family metadata makes the row unique rather than heuristically merging it;
- free lexical-query EAP is left unchanged because enlarging max_items there would also alter
  lexical seed-cap semantics; the intended path is the fail-closed U12 resolved-seed cascade;
- StateLedger remains source truth; ClayGraph/EAP activation remains context only.
"""

from dataclasses import replace
from typing import Any

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec


IMPLEMENTATION_ID = "EAP_FAMILY_FACTORIZATION_F1"


class FamilyFactorizedEmergentAssemblyPreprocessor(
    IncrementalEmergentAssemblyPreprocessor
):
    def __init__(
        self,
        ledger,
        *,
        family_value_key: str = "possibility_family_id",
        max_per_family: int = 1,
        oversample_factor: int = 4,
    ):
        super().__init__(ledger)
        if not family_value_key.strip():
            raise ValueError("family_value_key required")
        if max_per_family <= 0 or max_per_family > 64:
            raise ValueError("max_per_family out of bounds")
        if oversample_factor <= 0 or oversample_factor > 64:
            raise ValueError("oversample_factor out of bounds")
        self.family_value_key = family_value_key
        self.max_per_family = int(max_per_family)
        self.oversample_factor = int(oversample_factor)

    def _family_id(self, item: dict[str, Any]) -> tuple[str, bool]:
        value = item.get("value")
        if isinstance(value, dict):
            raw = value.get(self.family_value_key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip(), True
        # Fail-conservative: absence of typed family identity never merges unrelated rows.
        return f"__UNIQUE__:{item['ref']}", False

    def compile_active_assembly(self, spec: PossibilitySpec) -> dict[str, Any]:
        if spec.query_text.strip():
            result = super().compile_active_assembly(spec)
            result.update(
                {
                    "family_factorization_implementation": IMPLEMENTATION_ID,
                    "family_factorization_applied": False,
                    "family_factorization_reason": "LEXICAL_QUERY_PATH_UNCHANGED",
                    "family_value_key": self.family_value_key,
                    "max_per_family": self.max_per_family,
                    "authority": "ASSEMBLY_CONTEXT_ONLY",
                }
            )
            return result

        pool_max_items = min(
            4096,
            max(spec.max_items, spec.max_items * self.oversample_factor),
        )
        base = super().compile_active_assembly(
            replace(spec, max_items=pool_max_items)
        )

        selected: list[dict[str, Any]] = []
        family_suppressed: list[dict[str, Any]] = []
        family_counts: dict[str, int] = {}
        explicit_families: set[str] = set()

        for item in base["selected"]:
            family_id, explicit = self._family_id(item)
            if explicit:
                explicit_families.add(family_id)
            count = family_counts.get(family_id, 0)
            if count >= self.max_per_family:
                family_suppressed.append(
                    {
                        "ref": item["ref"],
                        "possibility_family_id": family_id,
                        "activation_score": item["activation_score"],
                        "source_semantic_hash": item["source_semantic_hash"],
                        "reason": "DUPLICATE_POSSIBILITY_FAMILY",
                        "authority": "SUPPRESSED_CONTEXT_ONLY",
                    }
                )
                continue
            if len(selected) >= spec.max_items:
                break
            copy = dict(item)
            copy["possibility_family_id"] = family_id if explicit else None
            copy["possibility_family_explicit"] = explicit
            selected.append(copy)
            family_counts[family_id] = count + 1

        selection_hash = h(
            {
                "implementation": IMPLEMENTATION_ID,
                "base_selection_hash": base["selection_hash"],
                "requested_max_items": spec.max_items,
                "pool_max_items": pool_max_items,
                "family_value_key": self.family_value_key,
                "max_per_family": self.max_per_family,
                "selected": tuple(
                    (
                        item["ref"],
                        item["source_semantic_hash"],
                        item.get("possibility_family_id"),
                        item["activation_score"],
                    )
                    for item in selected
                ),
            }
        )

        result = dict(base)
        result.update(
            {
                "selected": selected,
                "selection_hash": selection_hash,
                "base_selection_hash": base["selection_hash"],
                "family_factorization_implementation": IMPLEMENTATION_ID,
                "family_factorization_applied": True,
                "family_factorization_reason": "EXPLICIT_FAMILY_IDS_ONLY",
                "family_value_key": self.family_value_key,
                "max_per_family": self.max_per_family,
                "requested_max_items": spec.max_items,
                "candidate_pool_items": len(base["selected"]),
                "explicit_family_count_in_pool": len(explicit_families),
                "family_suppressed": family_suppressed,
                "persistent_second_store": False,
                "authority": "ASSEMBLY_CONTEXT_ONLY",
            }
        )
        return result
