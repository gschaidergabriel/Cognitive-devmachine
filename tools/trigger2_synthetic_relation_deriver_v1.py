#!/usr/bin/env python3
"""Deterministic formal-world relation derivation for Trigger-2 Hyperposition.

Source-design primitive only. It converts typed synthetic task-world predictions plus
one observed measurement into branch-local SUPPORTS/COUNTERS/FALSIFIES/UNKNOWN
relations and a discriminator partition receipt.

It deliberately rejects caller-provided relation/effect/winner/target labels. It does
not mint canonical truth, real-effect authority, J-Space/HCU/runtime or training credit.
"""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_RELATION_DERIVER/v1"
WORLD_SCHEMA = "XENO_SYNTHETIC_RELATION_WORLD/v1"
OBS_SCHEMA = "XENO_SYNTHETIC_MEASUREMENT_OBSERVATION/v1"

FORBIDDEN_ASSERTED_LABEL_FIELDS = {
    "relation",
    "effect",
    "target_branch_ids",
    "winner_branch_id",
    "separates_live_branch_ids",
    "evidence_qualified",
    "decision_role",
}
ALLOWED_CONTEXT = {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}


class DerivationError(ValueError):
    pass


def _require_dict(x: Any, where: str) -> dict[str, Any]:
    if not isinstance(x, dict):
        raise DerivationError(f"{where}: object required")
    return x


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _digest(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_world(world: Any) -> dict[str, Any]:
    world = _require_dict(world, "world")
    if world.get("schema") != WORLD_SCHEMA:
        raise DerivationError("world: schema mismatch")
    if not _nonempty(world.get("world_id")):
        raise DerivationError("world: world_id required")
    measurements = world.get("measurements")
    if not isinstance(measurements, dict) or not measurements:
        raise DerivationError("world: nonempty measurements required")
    for mid, spec in measurements.items():
        if not _nonempty(mid):
            raise DerivationError("world: measurement id invalid")
        spec = _require_dict(spec, f"measurement:{mid}")
        if not isinstance(spec.get("admissible"), bool):
            raise DerivationError(f"measurement:{mid}: admissible bool required")
        if not isinstance(spec.get("decisive"), bool):
            raise DerivationError(f"measurement:{mid}: decisive bool required")
        domain = spec.get("outcome_domain")
        if not isinstance(domain, list) or len(domain) < 2:
            raise DerivationError(f"measurement:{mid}: outcome_domain >=2 required")
        if len(domain) != len({json.dumps(v, sort_keys=True, ensure_ascii=False) for v in domain}):
            raise DerivationError(f"measurement:{mid}: outcome_domain duplicates")
    return world


def _validate_branches(branches: Any, world: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("branches: at least two branches required")
    mids = set(world["measurements"])
    seen: set[str] = set()
    out = []
    for branch in branches:
        branch = _require_dict(branch, "branch")
        bid = branch.get("branch_id")
        if not _nonempty(bid):
            raise DerivationError("branch: branch_id required")
        if bid in seen:
            raise DerivationError("branch: duplicate branch_id")
        seen.add(bid)
        if branch.get("K") not in ALLOWED_CONTEXT:
            raise DerivationError(f"branch:{bid}: K invalid")
        predictions = branch.get("predictions")
        if not isinstance(predictions, dict):
            raise DerivationError(f"branch:{bid}: predictions object required")
        if not set(predictions).issubset(mids):
            raise DerivationError(f"branch:{bid}: prediction references unknown measurement")
        for mid, predicted in predictions.items():
            domain = world["measurements"][mid]["outcome_domain"]
            if predicted not in domain:
                raise DerivationError(f"branch:{bid}: predicted outcome outside domain")
        out.append(branch)
    return out


def _validate_observation(observation: Any, world: dict[str, Any]) -> dict[str, Any]:
    observation = _require_dict(observation, "observation")
    if observation.get("schema") != OBS_SCHEMA:
        raise DerivationError("observation: schema mismatch")
    forbidden = FORBIDDEN_ASSERTED_LABEL_FIELDS & set(observation)
    if forbidden:
        raise DerivationError(
            "observation: asserted label fields forbidden:" + ",".join(sorted(forbidden))
        )
    for key in (
        "evidence_event_id",
        "correlation_ancestry_id",
        "independence_group",
        "provenance",
        "measurement_id",
    ):
        if not _nonempty(observation.get(key)):
            raise DerivationError(f"observation: {key} required")
    mid = observation["measurement_id"]
    if mid not in world["measurements"]:
        raise DerivationError("observation: unknown measurement_id")
    if "observed_outcome" not in observation:
        raise DerivationError("observation: observed_outcome required")
    if observation["observed_outcome"] not in world["measurements"][mid]["outcome_domain"]:
        raise DerivationError("observation: observed_outcome outside domain")
    return observation


def _relation(branch: dict[str, Any], mid: str, observed: Any, decisive: bool) -> str:
    if branch["K"] == "DOES_NOT_APPLY":
        return "IRRELEVANT"
    if branch["K"] == "UNKNOWN":
        return "UNKNOWN_RELATION"
    predictions = branch["predictions"]
    if mid not in predictions:
        return "UNKNOWN_RELATION"
    if predictions[mid] == observed:
        return "SUPPORTS"
    return "FALSIFIES" if decisive else "COUNTERS"


def derive(world: Any, branches: Any, observation: Any) -> dict[str, Any]:
    """Derive branch relations and discriminator semantics from a formal synthetic world."""
    world = _validate_world(world)
    branches = _validate_branches(branches, world)
    observation = _validate_observation(observation, world)
    mid = observation["measurement_id"]
    spec = world["measurements"][mid]
    observed = observation["observed_outcome"]

    relation_rows = []
    predicted_outcomes: dict[str, Any] = {}
    for branch in branches:
        bid = branch["branch_id"]
        predicted = branch["predictions"].get(mid)
        if branch["K"] == "APPLIES" and mid in branch["predictions"]:
            predicted_outcomes[bid] = predicted
        relation_rows.append(
            {
                "branch_id": bid,
                "K": branch["K"],
                "predicted_outcome": predicted,
                "observed_outcome": observed,
                "relation": _relation(branch, mid, observed, bool(spec["decisive"])),
            }
        )

    # Stable receipts are branch-id sorted, independent of serialization order.
    relation_rows.sort(key=lambda x: x["branch_id"])
    target_branch_ids = sorted(
        x["branch_id"]
        for x in relation_rows
        if x["relation"] in {"SUPPORTS", "COUNTERS", "FALSIFIES"}
    )

    applicable_ids = sorted(predicted_outcomes)
    pairs = []
    for a, b in combinations(applicable_ids, 2):
        if predicted_outcomes[a] != predicted_outcomes[b]:
            pairs.append([a, b])

    groups: dict[str, list[str]] = {}
    for bid in applicable_ids:
        outcome_key = json.dumps(predicted_outcomes[bid], sort_keys=True, ensure_ascii=False)
        groups.setdefault(outcome_key, []).append(bid)
    partition = sorted((sorted(ids) for ids in groups.values()), key=lambda ids: tuple(ids))
    full_separation = bool(applicable_ids) and all(len(ids) == 1 for ids in partition)

    matching = sorted(
        bid for bid, predicted in predicted_outcomes.items() if predicted == observed
    )
    admissible = bool(spec["admissible"])
    decisive = bool(spec["decisive"])
    winner = matching[0] if admissible and decisive and full_separation and len(matching) == 1 else None

    # Adapter receipts for trigger2_hyperposition_reference_labelers_v2.u_state.
    # One receipt per affected branch avoids inventing one shared relation for branches
    # whose predictions differ.
    labeler_observations = []
    world_digest = _digest(world)
    observation_digest = _digest(observation)
    for row in relation_rows:
        if row["relation"] not in {"SUPPORTS", "COUNTERS", "FALSIFIES"}:
            continue
        labeler_observations.append(
            {
                "evidence_event_id": observation["evidence_event_id"],
                "correlation_ancestry_id": observation["correlation_ancestry_id"],
                "independence_group": observation["independence_group"],
                "provenance": observation["provenance"],
                "relation": row["relation"],
                "target_branch_ids": [row["branch_id"]],
                "independence_qualified": bool(observation.get("independence_qualified", False)),
                "derived_by": SCHEMA,
                "world_digest_sha256": world_digest,
                "observation_digest_sha256": observation_digest,
            }
        )

    discriminator = {
        "measurement_id": mid,
        "admissible": admissible,
        "decisive": decisive,
        "predicted_outcomes": {k: predicted_outcomes[k] for k in sorted(predicted_outcomes)},
        "separates_branch_pairs": pairs,
        "outcome_partition": partition,
        "full_pairwise_separation": full_separation,
        "matching_branch_ids": matching,
        "derived_winner_branch_id": winner,
    }

    return {
        "schema": SCHEMA,
        "world_id": world["world_id"],
        "world_digest_sha256": world_digest,
        "observation_digest_sha256": observation_digest,
        "branch_relations": relation_rows,
        "derived_target_branch_ids": target_branch_ids,
        "labeler_observations": labeler_observations,
        "discriminator": discriminator,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "jspace_causal_credit_minted": False,
        "runtime_credit_minted": False,
        "training_credit_minted": False,
    }
