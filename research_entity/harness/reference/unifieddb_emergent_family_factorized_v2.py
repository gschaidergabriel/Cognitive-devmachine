from __future__ import annotations

"""EAP-FAMILY-F2: one-pass pre-truncation possibility-family factorization experiment.

F2 intentionally remains a derived wrapper around the current incremental EAP. It asks the
existing preprocessor for a bounded larger visited-candidate pool once, then spends the final
ActiveAssembly budget on distinct explicitly typed possibility families. This is a research
step toward native factorization before EAP truncation; it does not create a persistent store,
truth, or effect authority.
"""

from dataclasses import replace
from typing import Any

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec


IMPLEMENTATION_ID = "EAP_FAMILY_FACTORIZATION_F2_ONE_PASS_POOL"


class OnePassFamilyFactorizedEmergentAssemblyPreprocessor(
    IncrementalEmergentAssemblyPreprocessor
):
    def __init__(
        self,
        ledger,
        *,
        family_value_key: str = "possibility_family_id",
        max_per_family: int = 1,
        pool_cap: int = 4096,
    ):
        super().__init__(ledger)
        if not family_value_key.strip():
            raise ValueError("family_value_key required")
        if max_per_family <= 0 or max_per_family > 64:
            raise ValueError("max_per_family out of bounds")
        if pool_cap <= 0 or pool_cap > 4096:
            raise ValueError("pool_cap out of bounds")
        self.family_value_key = family_value_key
        self.max_per_family = int(max_per_family)
        self.pool_cap = int(pool_cap)

    def _family_id(self, item: dict[str, Any]) -> tuple[str, bool]:
        value = item.get("value")
        if isinstance(value, dict):
            raw = value.get(self.family_value_key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip(), True
        return f"__UNIQUE__:{item['ref']}", False

    def compile_active_assembly(self, spec: PossibilitySpec) -> dict[str, Any]:
        # Keep free lexical query semantics byte-selection-compatible. In that path max_items
        # also controls lexical seed fan-in, so silently enlarging it would alter the query.
        if spec.query_text.strip():
            result = super().compile_active_assembly(spec)
            result.update(
                {
                    "family_factorization_implementation": IMPLEMENTATION_ID,
                    "family_factorization_applied": False,
                    "family_factorization_reason": "LEXICAL_QUERY_PATH_UNCHANGED",
                    "authority": "ASSEMBLY_CONTEXT_ONLY",
                }
            )
            return result

        pool_items = min(4096, max(spec.max_items, self.pool_cap))
        base = super().compile_active_assembly(replace(spec, max_items=pool_items))

        selected: list[dict[str, Any]] = []
        duplicate_family_suppressed: list[dict[str, Any]] = []
        family_counts: dict[str, int] = {}
        explicit_families: set[str] = set()

        for item in base["selected"]:
            family_id, explicit = self._family_id(item)
            if explicit:
                explicit_families.add(family_id)
            count = family_counts.get(family_id, 0)
            if count >= self.max_per_family:
                duplicate_family_suppressed.append(
                    {
                        "ref": item["ref"],
                        "possibility_family_id": family_id,
                        "source_semantic_hash": item["source_semantic_hash"],
                        "activation_score": item["activation_score"],
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
                "pool_items_requested": pool_items,
                "pool_items_materialized": len(base["selected"]),
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
                "family_factorization_reason": "EXPLICIT_FAMILY_IDS_ONE_PASS_POOL",
                "family_value_key": self.family_value_key,
                "max_per_family": self.max_per_family,
                "requested_max_items": spec.max_items,
                "candidate_pool_items": len(base["selected"]),
                "candidate_pool_cap": self.pool_cap,
                "explicit_family_count_in_pool": len(explicit_families),
                "family_suppressed": duplicate_family_suppressed,
                "pool_exhausted_before_requested_family_budget": (
                    len(selected) < spec.max_items
                    and len(base["selected"]) >= pool_items
                ),
                "persistent_second_store": False,
                "authority": "ASSEMBLY_CONTEXT_ONLY",
            }
        )
        return result
