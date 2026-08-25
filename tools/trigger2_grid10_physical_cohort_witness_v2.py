#!/usr/bin/env python3
"""Trigger-2 v2 source boundary for physical GRID cohort provenance.

This module is a successor adapter around the retained v1 FusedFabric.  It does not create
another state database, cohort identity, coordinator, or effect path.  Its sole purpose is
to separate two evidence classes that v1 currently represents with the same plain dict:

* PHYSICAL_OBSERVATION: proof data returned by the retained ``spawn_held_cohort`` path after
  the parent has performed the live-process/procfs/held-transaction/barrier observations.
* SYNTHETIC_SOURCE_FIXTURE: deterministic source-composition data used to exercise envelope,
  persistence, replay and fail-before-mutation behavior without claiming physical execution.

The physical commit API accepts only an instance-bound sealed ``PhysicalCohortWitness``
created inside ``ObservedPhysicalFusedFabric.spawn_observed_cohort``.  A caller-supplied raw
mapping is therefore structurally incapable of entering that v2 physical commit path.

This is a source-level provenance boundary, not a sandbox/security boundary against arbitrary
code execution inside the Python interpreter.  It mints zero physical GRID10, model, J-Space,
training, HCU, EntityOS, canonical-truth or effect-authority credit by source presence alone.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

try:
    from tools.trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import (
        FusedFabric,
        FabricError,
        dg,
        spawn_held_cohort,
    )
except ModuleNotFoundError:  # direct script/tool execution compatibility
    from trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import (
        FusedFabric,
        FabricError,
        dg,
        spawn_held_cohort,
    )

SCHEMA = "CLAY_TRIGGER2_GRID10_PHYSICAL_COHORT_WITNESS/v2"
PHYSICAL_KIND = "PHYSICAL_OBSERVATION"
SOURCE_FIXTURE_KIND = "SYNTHETIC_SOURCE_FIXTURE"


class WitnessError(FabricError):
    """Fail-closed v2 witness-boundary error."""


def _make_witness_factory():
    mint_capability = object()

    class PhysicalCohortWitness:
        """Opaque immutable-by-API proof object bound to one fabric instance."""

        __slots__ = ("__owner", "__proof", "__proof_digest", "__kind", "__mint_capability")

        def __init__(
            self,
            owner: object,
            proof: Mapping[str, Any],
            *,
            kind: str,
            _mint_capability: object | None = None,
        ) -> None:
            if _mint_capability is not mint_capability:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_CONSTRUCTOR_FORBIDDEN")
            if kind != PHYSICAL_KIND:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_KIND_INVALID")
            copied = deepcopy(dict(proof))
            self.__owner = owner
            self.__proof = copied
            self.__proof_digest = dg(copied)
            self.__kind = kind
            self.__mint_capability = _mint_capability

        @property
        def schema(self) -> str:
            return SCHEMA

        @property
        def kind(self) -> str:
            return self.__kind

        @property
        def proof_digest(self) -> str:
            return self.__proof_digest

        def _consume_for(self, owner: object) -> dict[str, Any]:
            if self.__mint_capability is not mint_capability:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_MINT_CAPABILITY_INVALID")
            if owner is not self.__owner:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_FABRIC_INSTANCE_MISMATCH")
            if self.__kind != PHYSICAL_KIND:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_KIND_INVALID")
            if dg(self.__proof) != self.__proof_digest:
                raise WitnessError("PHYSICAL_COHORT_WITNESS_MUTATED")
            return deepcopy(self.__proof)

    def mint(owner: object, proof: Mapping[str, Any]):
        return PhysicalCohortWitness(
            owner,
            proof,
            kind=PHYSICAL_KIND,
            _mint_capability=mint_capability,
        )

    return PhysicalCohortWitness, mint


PhysicalCohortWitness, _mint_physical_witness = _make_witness_factory()


class ObservedPhysicalFusedFabric(FusedFabric):
    """v2 physical-evidence facade over the sole retained FusedFabric authority."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.__physical_witness_owner = object()

    def spawn_observed_cohort(
        self,
        *,
        script: Path,
        db: Path,
        node_ids: list[str],
        root: Path,
    ) -> tuple[list[dict[str, Any]], PhysicalCohortWitness]:
        """Run the retained physical observation path and seal exactly its returned proof."""
        packets, proof = spawn_held_cohort(self, script, db, node_ids, root)
        if not isinstance(proof, Mapping):
            raise WitnessError("PHYSICAL_OBSERVER_PROOF_NOT_MAPPING")
        witness = _mint_physical_witness(self.__physical_witness_owner, proof)
        return packets, witness

    def atomic_fused_cohort_commit(
        self,
        *,
        proof: PhysicalCohortWitness,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Commit only proof sealed by this fabric instance's physical observer path."""
        if type(proof) is not PhysicalCohortWitness:
            raise WitnessError("PHYSICAL_COHORT_WITNESS_REQUIRED")
        raw_proof = proof._consume_for(self.__physical_witness_owner)
        receipt = super().atomic_fused_cohort_commit(proof=raw_proof, **kwargs)
        return {
            **receipt,
            "physical_witness_schema": SCHEMA,
            "physical_witness_kind": PHYSICAL_KIND,
            "physical_witness_digest": proof.proof_digest,
            "source_fixture_only": False,
            "credit_boundary": {
                "source_guard_is_physical_grid10_runtime_credit": False,
                "physical_grid10_runtime_credit_added": 0,
                "model_call_runtime_credit_added": 0,
                "jspace_model_credit_added": 0,
                "training_credit_added": 0,
                "whole_hcu_runtime_credit_added": 0,
                "whole_entityos_runtime_credit_added": 0,
            },
        }


class SourceFixtureFusedFabric(FusedFabric):
    """Explicit nonphysical compatibility facade for deterministic source composition."""

    def atomic_fused_cohort_commit(
        self,
        *,
        proof: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        if type(proof) is not dict:
            raise WitnessError("SOURCE_FIXTURE_PROOF_RAW_DICT_REQUIRED")
        if proof.get("synthetic_source_fixture_only") is not True:
            raise WitnessError("SOURCE_FIXTURE_PROOF_MARKER_REQUIRED")
        if proof.get("physical_observation") is True:
            raise WitnessError("SOURCE_FIXTURE_CANNOT_CLAIM_PHYSICAL_OBSERVATION")
        receipt = super().atomic_fused_cohort_commit(proof=dict(proof), **kwargs)
        return {
            **receipt,
            "physical_witness_schema": SCHEMA,
            "physical_witness_kind": SOURCE_FIXTURE_KIND,
            "source_fixture_only": True,
            "credit_boundary": {
                "source_fixture_is_physical_grid10_runtime_credit": False,
                "physical_grid10_runtime_credit_added": 0,
                "model_call_runtime_credit_added": 0,
                "jspace_model_credit_added": 0,
                "training_credit_added": 0,
                "whole_hcu_runtime_credit_added": 0,
                "whole_entityos_runtime_credit_added": 0,
            },
        }


def assert_witness_source_contract() -> dict[str, Any]:
    """Static contract declaration for receipts/review; performs no physical execution."""
    return {
        "schema": SCHEMA,
        "pass": True,
        "physical_commit_requires_exact_witness_type": True,
        "physical_witness_minted_only_after_retained_spawn_observation_call": True,
        "witness_bound_to_fabric_instance": True,
        "witness_payload_digest_bound": True,
        "source_fixture_path_explicitly_nonphysical": True,
        "second_cohort_authority_created": False,
        "second_state_or_effect_authority_created": False,
        "credit_boundary": {
            "physical_grid10_runtime_credit": 0,
            "model_call_runtime_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }
