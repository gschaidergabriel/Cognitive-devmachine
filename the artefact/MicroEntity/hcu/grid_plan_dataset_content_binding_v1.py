from __future__ import annotations

from typing import Any, Mapping

try:
    from .grid10_scheduler_v1 import (
        GridPlan,
        GridScheduleError,
        PLAN_SCHEMA,
        validate_grid_plan_identity,
    )
except ImportError:
    from grid10_scheduler_v1 import (
        GridPlan,
        GridScheduleError,
        PLAN_SCHEMA,
        validate_grid_plan_identity,
    )


class GridPlanDatasetBindingError(ValueError):
    """Fail-closed GRID plan ancestry rejection at dataset admission boundaries."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GridPlanDatasetBindingError(f"{field}:MAPPING_REQUIRED")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise GridPlanDatasetBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if (
        len(value) != 64
        or value.lower() != value
        or any(ch not in "0123456789abcdef" for ch in value)
        or value in {"0" * 64, "f" * 64}
    ):
        raise GridPlanDatasetBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GridPlanDatasetBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise GridPlanDatasetBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def verify_admitted_grid_plan_binding(
    admitted_grid_plans: Any,
    *,
    grid_plan_sha256: str,
    generation: int,
    causal: Mapping[str, str],
) -> GridPlan:
    """Resolve GRID plan ancestry through the scheduler's sole content-hash authority.

    A registry key plus a repeated ``plan_sha256`` field is not cryptographic ancestry.
    ``grid10_scheduler_v1.validate_grid_plan_identity`` owns the canonical PLAN_SCHEMA hash
    material, so this adapter deliberately calls that producer validator instead of
    reconstructing a second serializer in the dataset layer.

    The registry must therefore contain the exact ``GridPlan`` preimage, not a reduced
    receipt that merely repeats the digest. This helper does not mint state, scheduling
    authority, execution credit, or dataset truth; it only fail-closes content-false GRID
    ancestry before downstream training admission.
    """
    registry = _mapping(admitted_grid_plans, "admitted_grid_plans")
    claimed = _sha256(grid_plan_sha256, "grid_plan_sha256")
    expected_generation = _generation(generation, "generation")
    causal = _mapping(causal, "causal")

    plan = registry.get(claimed)
    if plan is None:
        raise GridPlanDatasetBindingError("GRID_PLAN_NOT_ADMITTED")
    if not isinstance(plan, GridPlan):
        raise GridPlanDatasetBindingError("GRID_PLAN_PREIMAGE_TYPE_INVALID")

    try:
        observed = validate_grid_plan_identity(plan)
    except GridScheduleError as exc:
        raise GridPlanDatasetBindingError(f"GRID_PLAN_PREIMAGE_REJECTED:{exc}") from exc

    if plan.schema != PLAN_SCHEMA:
        raise GridPlanDatasetBindingError("GRID_PLAN_SCHEMA_UNSUPPORTED")
    if observed != claimed or plan.plan_sha256 != claimed:
        raise GridPlanDatasetBindingError("GRID_PLAN_REGISTRY_KEY_CONTENT_MISMATCH")
    if _generation(plan.entity_generation, "admitted_grid_plan.entity_generation") != expected_generation:
        raise GridPlanDatasetBindingError("GRID_PLAN_GENERATION_MISMATCH")

    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
    ):
        expected = _sha256(causal.get(field), f"causal.{field}")
        observed_field = _sha256(getattr(plan, field), f"admitted_grid_plan.{field}")
        if observed_field != expected:
            raise GridPlanDatasetBindingError(f"GRID_PLAN_CAUSAL_BINDING_MISMATCH:{field}")

    return plan
