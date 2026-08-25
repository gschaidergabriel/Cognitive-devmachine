from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tools.trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import FabricError


_SOURCE_TEST = Path(__file__).with_name(
    "test_trigger2_fused_membership_two_phase_real_fabric_source_v1.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "trigger2_real_fusedfabric_source_fixture",
    _SOURCE_TEST,
)
assert _SPEC is not None and _SPEC.loader is not None
_FIXTURE_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FIXTURE_MODULE)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V66 source gap: physical admission still accepts caller-forgeable synthetic proof "
        "dictionaries instead of a source-enforced physical witness provenance boundary"
    ),
)
def test_all_true_synthetic_proof_cannot_mutate_physical_cohort_state(tmp_path):
    """Fail-closed target: raw synthetic proof must never satisfy physical admission.

    The imported fixture deliberately creates deterministic fake producer PIDs and an
    all-true proof dictionary.  At V66 that dictionary can traverse the retained adapter
    into FusedFabric and mutate cohort state.  This test stays strict-xfail until the
    physical path requires an observed/minted witness and rejects the raw fixture proof
    before mutation.
    """

    fx = _FIXTURE_MODULE._fixture(tmp_path, "caller-forgeable-physical-proof")
    fabric = fx["fabric"]
    try:
        before_epoch = fabric.snapshot().epoch
        before_cohorts = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM fused_cohort_admissions"
        ).fetchone()["n"]
        before_results = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM admitted_results"
        ).fetchone()["n"]

        with pytest.raises(
            FabricError,
            match="^(PHYSICAL_COHORT_WITNESS_REQUIRED|PHYSICAL_COHORT_PROVENANCE_INVALID)$",
        ):
            _FIXTURE_MODULE._commit(fx, fx["extended_envelopes"])

        assert fabric.snapshot().epoch == before_epoch
        assert (
            fabric.con.execute(
                "SELECT COUNT(*) AS n FROM fused_cohort_admissions"
            ).fetchone()["n"]
            == before_cohorts
        )
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM admitted_results").fetchone()["n"]
            == before_results
        )
    finally:
        fabric.close()
