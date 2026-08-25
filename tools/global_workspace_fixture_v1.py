#!/usr/bin/env python3
"""Deterministic model-free GLOBAL_WORKSPACE_PROTOCOL/v1 component fixture.

Scope:
- ZECP10 competition / selection / broadcast / re-entry mechanics only.
- S1 workspace state is in-memory and discardable.
- no canonical DB writer, EffectGate, provider, model, Claude Code, network, or tool I/O.
- broadcast delivery and observed downstream change never mint Global J-Space causal credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable


class GlobalWorkspaceError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _valid_process_id(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith("ZECP") or len(value) != 6:
        return False
    suffix = value[4:]
    return suffix.isdigit() and 1 <= int(suffix) <= 20


@dataclass(frozen=True)
class WorkspaceCandidate:
    causal_event_id: str
    admission_id: str
    generation: int
    work_id: str
    process_id: str
    result_id: str
    result_class: str
    result_digest: str
    salience_score: int
    uncertainty: str
    provenance_ref: str

    def validate(self) -> None:
        if not self.causal_event_id or not self.admission_id or not self.work_id or not self.result_id:
            raise GlobalWorkspaceError("CANDIDATE_IDENTITY_REQUIRED")
        if not _valid_process_id(self.process_id):
            raise GlobalWorkspaceError("PROCESS_ID_INVALID")
        if self.result_class not in {"CANDIDATE", "PROJECTION", "MEASUREMENT"}:
            raise GlobalWorkspaceError("RESULT_CLASS_AUTHORITY_ESCALATION")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise GlobalWorkspaceError("GENERATION_INVALID")
        if isinstance(self.salience_score, bool) or not isinstance(self.salience_score, int):
            raise GlobalWorkspaceError("SALIENCE_INTEGER_REQUIRED")
        if not self.result_digest:
            raise GlobalWorkspaceError("RESULT_DIGEST_REQUIRED")


class GlobalWorkspaceFixture:
    """Discardable S1 workspace for one admitted causal event/generation."""

    def __init__(self, *, causal_event_id: str, generation: int, requested_n: int):
        if not causal_event_id:
            raise GlobalWorkspaceError("CAUSAL_EVENT_ID_REQUIRED")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise GlobalWorkspaceError("GENERATION_INVALID")
        if isinstance(requested_n, bool) or not isinstance(requested_n, int) or requested_n < 1:
            raise GlobalWorkspaceError("GRID_N_MUST_BE_POSITIVE")
        self.causal_event_id = causal_event_id
        self.generation = generation
        self.requested_n = requested_n
        self._selections: dict[str, dict[str, Any]] = {}
        self._broadcasts: dict[str, dict[str, Any]] = {}
        self._reentries: list[dict[str, Any]] = []

    @staticmethod
    def semantic_fingerprint() -> str:
        """N-independent workspace semantics."""
        return digest(
            {
                "schema": "GLOBAL_WORKSPACE_PROTOCOL/v1",
                "process": "ZECP10",
                "state_class": "S1_NONCANONICAL_DISCARDABLE",
                "competition": ["salience_score_DESC", "result_digest_ASC", "result_id_ASC"],
                "truth_authority": "NONE",
                "effect_authority": "NONE",
                "reentry_causal_credit": "ZERO_WITHOUT_SEPARATE_MODEL_SPECIFIC_INTERVENTION",
            }
        )

    def compete(self, candidates: Iterable[WorkspaceCandidate], *, workspace_epoch: int) -> dict[str, Any]:
        if isinstance(workspace_epoch, bool) or not isinstance(workspace_epoch, int) or workspace_epoch < 0:
            raise GlobalWorkspaceError("WORKSPACE_EPOCH_INVALID")
        values = list(candidates)
        if not values:
            raise GlobalWorkspaceError("NO_WORKSPACE_CANDIDATES")

        for candidate in values:
            candidate.validate()
            if candidate.causal_event_id != self.causal_event_id:
                raise GlobalWorkspaceError("CROSS_CAUSAL_EVENT_COMPETITION_FORBIDDEN")
            if candidate.generation != self.generation:
                raise GlobalWorkspaceError("STALE_GENERATION_CANDIDATE")

        # Exact repeated result bytes cannot gain voting weight merely by recurrence.
        dedup: dict[str, WorkspaceCandidate] = {}
        for candidate in sorted(values, key=lambda x: (x.result_digest, x.result_id)):
            dedup.setdefault(candidate.result_digest, candidate)
        unique = list(dedup.values())
        unique.sort(key=lambda x: (-x.salience_score, x.result_digest, x.result_id))
        winner = unique[0]
        max_salience = winner.salience_score
        tied = sorted(x.result_id for x in unique if x.salience_score == max_salience)
        deferred = sorted(x.result_id for x in unique if x.result_id != winner.result_id)

        semantic = {
            "schema": "WORKSPACE_SELECTION/v1",
            "causal_event_id": self.causal_event_id,
            "generation": self.generation,
            "workspace_epoch": workspace_epoch,
            "selected_result_id": winner.result_id,
            "selected_result_digest": winner.result_digest,
            "selected_process_id": winner.process_id,
            "selected_result_class": winner.result_class,
            "tied_alternative_result_ids": tied,
            "deferred_result_ids": deferred,
            "deduplicated_recurrence_count": len(values) - len(unique),
            "authority": "ATTENTION_SELECTION_ONLY_NOT_CANONICAL_TRUTH",
        }
        selection_id = "sel-" + digest(semantic)[:24]
        selection = {**semantic, "selection_id": selection_id}
        self._selections[selection_id] = selection
        return dict(selection)

    def broadcast(self, selection: dict[str, Any], target_process_ids: Iterable[str]) -> dict[str, Any]:
        selection_id = selection.get("selection_id")
        if selection_id not in self._selections or self._selections[selection_id] != selection:
            raise GlobalWorkspaceError("SELECTION_NOT_OWNED_BY_WORKSPACE")
        targets = sorted(set(target_process_ids))
        if not targets:
            raise GlobalWorkspaceError("BROADCAST_TARGET_REQUIRED")
        if not all(_valid_process_id(x) for x in targets):
            raise GlobalWorkspaceError("BROADCAST_TARGET_MUST_BE_PROCESS_ID")
        payload = {
            "schema": "WORKSPACE_BROADCAST/v1",
            "causal_event_id": self.causal_event_id,
            "generation": self.generation,
            "workspace_epoch": selection["workspace_epoch"],
            "selection_id": selection_id,
            "selected_result_id": selection["selected_result_id"],
            "selected_result_digest": selection["selected_result_digest"],
            "target_process_ids": targets,
            "authority": "NONCANONICAL_S1_DELIVERY_ONLY",
        }
        broadcast_id = "bcast-" + digest(payload)[:24]
        packet = {**payload, "broadcast_id": broadcast_id, "broadcast_digest": digest(payload)}
        self._broadcasts[broadcast_id] = packet
        return dict(packet)

    def reenter(
        self,
        broadcast: dict[str, Any],
        *,
        target_process_id: str,
        observed_downstream_change: str = "UNKNOWN",
    ) -> dict[str, Any]:
        broadcast_id = broadcast.get("broadcast_id")
        if broadcast_id not in self._broadcasts or self._broadcasts[broadcast_id] != broadcast:
            raise GlobalWorkspaceError("BROADCAST_NOT_OWNED_BY_WORKSPACE")
        if target_process_id not in broadcast["target_process_ids"]:
            raise GlobalWorkspaceError("REENTRY_TARGET_NOT_BROADCAST")
        if observed_downstream_change not in {"TRUE", "FALSE", "UNKNOWN"}:
            raise GlobalWorkspaceError("REENTRY_DOWNSTREAM_CHANGE_TRI_STATE_REQUIRED")
        from_epoch = int(broadcast["workspace_epoch"])
        payload_ref = f"workspace://{broadcast_id}/{target_process_id}"
        semantic = {
            "schema": "WORKSPACE_REENTRY/v1",
            "source_result_id": broadcast["selected_result_id"],
            "source_process_id": "ZECP10",
            "target_process_id": target_process_id,
            "causal_event_id": self.causal_event_id,
            "generation": self.generation,
            "from_workspace_epoch": from_epoch,
            "to_workspace_epoch": from_epoch + 1,
            "reentry_payload_ref": payload_ref,
            "observed_downstream_change": observed_downstream_change,
            "delivery_observed": True,
            "causal_use_proven": False,
            "global_jspace_causal_credit": 0,
            "authority": "NONCANONICAL_REENTRY_MEASUREMENT_ONLY",
        }
        reentry = {**semantic, "reentry_digest": digest(semantic)}
        self._reentries.append(reentry)
        return dict(reentry)

    def discard_s1(self) -> None:
        self._selections.clear()
        self._broadcasts.clear()
        self._reentries.clear()

    def s1_counts(self) -> dict[str, int]:
        return {
            "selections": len(self._selections),
            "broadcasts": len(self._broadcasts),
            "reentries": len(self._reentries),
        }

    @staticmethod
    def direct_s0_commit_allowed() -> bool:
        return False

    @staticmethod
    def direct_real_effect_allowed() -> bool:
        return False

    @staticmethod
    def capability_broadening_allowed() -> bool:
        return False
