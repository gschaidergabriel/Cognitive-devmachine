from __future__ import annotations

from collections import Counter
from typing import Any

from .method_memory import (
    CANDIDATE_KINDS,
    METHOD_SCHEMA_VERSION,
    MethodMemoryManager,
    MethodMemoryValidationError,
    signature_facets,
)


class MethodMemoryRetriever:
    """Deterministic Stage-B structural method retrieval.

    This layer may select reusable HOW records only. It never changes factual status,
    effect authority, durable memory contents or MicroClay's serving policy.
    """

    def __init__(self, db):
        self.db = db
        self.manager = MethodMemoryManager(db)

    @staticmethod
    def _score(query_facets: tuple[str, ...], method_facets: tuple[str, ...]) -> float:
        q = set(query_facets)
        m = set(method_facets)
        if not q or not m:
            return 0.0
        return len(q.intersection(m)) / len(q.union(m))

    def _row(self, memory_id: str):
        return self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
            (memory_id,),
        ).fetchone()

    def _lineage(self, promoted: dict[str, Any]) -> tuple[bool, str]:
        provenance = promoted["provenance"]
        source_id = provenance.get("promotion_source_memory_id")
        receipt_id = provenance.get("promotion_receipt_id")
        if (
            provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION
            or provenance.get("promotion_transaction_version") != 1
            or not isinstance(source_id, str)
            or not source_id
            or not isinstance(receipt_id, str)
            or not receipt_id
        ):
            return False, "missing_promotion_lineage"

        candidate_row = self._row(source_id)
        receipt_row = self._row(receipt_id)
        if candidate_row is None or receipt_row is None:
            return False, "missing_promotion_source_or_receipt"
        try:
            candidate = self.manager.decode_row(candidate_row)
            receipt = self.manager.decode_row(receipt_row)
        except MethodMemoryValidationError:
            return False, "invalid_promotion_source_or_receipt"

        expected_candidate_kind = (
            "framework_candidate" if promoted["kind"] == "framework" else "heuristic_candidate"
        )
        if candidate["kind"] != expected_candidate_kind or candidate["kind"] not in CANDIDATE_KINDS:
            return False, "promotion_source_kind_mismatch"
        if candidate["subject"] != promoted["subject"] or candidate["user_id"] != promoted["user_id"]:
            return False, "promotion_source_identity_mismatch"
        if receipt["kind"] != "method_receipt" or receipt["subject"] != source_id:
            return False, "promotion_receipt_identity_mismatch"
        receipt_value = receipt["value"]
        if receipt_value["action"] != "PROMOTE" or receipt_value["method_memory_id"] != source_id:
            return False, "promotion_receipt_action_mismatch"
        if (
            receipt["provenance"].get("promotion_source_memory_id") != source_id
            or receipt["provenance"].get("promotion_transaction_version") != 1
        ):
            return False, "promotion_receipt_provenance_mismatch"

        promoted_value = promoted["value"]
        candidate_value = candidate["value"]
        for field in (
            "problem_signature",
            "preconditions",
            "goal_shape",
            "method_steps",
            "invariants",
            "expected_observations",
            "falsifiers",
            "failure_modes",
            "scope_limits",
            "source_episode_ids",
            "supporting_memory_ids",
            "counterexample_memory_ids",
            "abstraction_version",
            "support_count",
            "success_count",
            "failure_count",
            "calibration",
        ):
            if promoted_value[field] != candidate_value[field]:
                return False, "promotion_payload_drift"
        if promoted_value["status"] != "PROMOTED":
            return False, "promotion_status_mismatch"
        if float(promoted_value["last_validated_at"]) != float(receipt_value["ts"]):
            return False, "promotion_validation_time_mismatch"
        if (
            receipt_value["source_episode_ids"] != promoted_value["source_episode_ids"]
            or receipt_value["supporting_memory_ids"] != promoted_value["supporting_memory_ids"]
            or receipt_value["counterexample_memory_ids"] != promoted_value["counterexample_memory_ids"]
        ):
            return False, "promotion_receipt_evidence_mismatch"

        source_episode_ids = list(promoted_value["source_episode_ids"])
        placeholders = ",".join("?" for _ in source_episode_ids)
        try:
            episodes = self.db.db.execute(
                f"SELECT episode_id FROM workspace_episodes WHERE episode_id IN ({placeholders})",
                tuple(source_episode_ids),
            ).fetchall()
        except Exception:
            return False, "workspace_episode_authority_unavailable"
        if {str(row["episode_id"]) for row in episodes} != set(source_episode_ids):
            return False, "promotion_episode_evidence_missing"

        evidence_ids = list(promoted_value["supporting_memory_ids"]) + list(
            promoted_value["counterexample_memory_ids"]
        )
        if evidence_ids:
            placeholders = ",".join("?" for _ in evidence_ids)
            memories = self.db.db.execute(
                f"SELECT memory_id FROM durable_memory WHERE memory_id IN ({placeholders})",
                tuple(evidence_ids),
            ).fetchall()
            if {str(row["memory_id"]) for row in memories} != set(evidence_ids):
                return False, "promotion_memory_evidence_missing"
        return True, "verified"

    def retrieve(
        self,
        *,
        problem_signature: dict[str, Any],
        user_id: str,
        limit: int = 5,
        min_score: float = 0.25,
    ) -> dict[str, Any]:
        if not isinstance(user_id, str) or not user_id.strip():
            raise MethodMemoryValidationError("method retrieval requires a non-empty user_id")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise MethodMemoryValidationError("method retrieval limit must be in [1,50]")
        if isinstance(min_score, bool) or not isinstance(min_score, (int, float)):
            raise MethodMemoryValidationError("method retrieval min_score must be numeric")
        threshold = float(min_score)
        if not 0.0 <= threshold <= 1.0:
            raise MethodMemoryValidationError("method retrieval min_score must be in [0,1]")

        query_facets = signature_facets({"problem_signature": problem_signature})
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            "WHERE kind IN ('framework','heuristic') AND (user_id IS NULL OR user_id=?) "
            "ORDER BY ts DESC",
            (user_id,),
        ).fetchall()

        valid: list[tuple[float, dict[str, Any]]] = []
        rejection_reasons: Counter[str] = Counter()
        for row in rows:
            try:
                decoded = self.manager.decode_row(row)
            except MethodMemoryValidationError:
                rejection_reasons["invalid_method_record"] += 1
                continue
            if decoded["value"]["status"] != "PROMOTED":
                rejection_reasons["not_promoted"] += 1
                continue
            lineage_ok, reason = self._lineage(decoded)
            if not lineage_ok:
                rejection_reasons[reason] += 1
                continue
            method_facets = signature_facets(decoded["value"])
            valid.append((self._score(query_facets, method_facets), decoded))

        valid.sort(
            key=lambda item: (
                item[0],
                float(item[1]["value"]["calibration"]),
                int(item[1]["value"]["support_count"]),
                float(item[1]["ts"]),
                item[1]["memory_id"],
            ),
            reverse=True,
        )
        selected = [item for item in valid if item[0] >= threshold][:limit]
        status = "PRESENT" if selected else ("UNDERCOVERED" if valid else "UNKNOWN")

        items = []
        for score, method in selected:
            value = method["value"]
            items.append(
                {
                    "memory_id": method["memory_id"],
                    "kind": method["kind"],
                    "subject": method["subject"],
                    "problem_signature": value["problem_signature"],
                    "preconditions": value["preconditions"],
                    "goal_shape": value["goal_shape"],
                    "method_steps": value["method_steps"],
                    "invariants": value["invariants"],
                    "expected_observations": value["expected_observations"],
                    "falsifiers": value["falsifiers"],
                    "failure_modes": value["failure_modes"],
                    "scope_limits": value["scope_limits"],
                    "source_episode_ids": value["source_episode_ids"],
                    "supporting_memory_ids": value["supporting_memory_ids"],
                    "counterexample_memory_ids": value["counterexample_memory_ids"],
                    "support_count": value["support_count"],
                    "success_count": value["success_count"],
                    "failure_count": value["failure_count"],
                    "calibration": value["calibration"],
                    "structural_score": score,
                    "promotion_source_memory_id": method["provenance"]["promotion_source_memory_id"],
                    "promotion_receipt_id": method["provenance"]["promotion_receipt_id"],
                }
            )

        return {
            "items": items,
            "receipt": {
                "status": status,
                "query_facets": list(query_facets),
                "promoted_candidate_count": len(rows),
                "validated_method_count": len(valid),
                "rejected_method_count": sum(rejection_reasons.values()),
                "rejection_reasons": dict(sorted(rejection_reasons.items())),
                "selected_count": len(items),
                "min_score": threshold,
                "truth_authority": False,
                "effect_authority": False,
                "fact_status": "UNCHANGED",
            },
        }
